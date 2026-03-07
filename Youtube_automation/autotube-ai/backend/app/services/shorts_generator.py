"""YouTube Shorts Generator — renders native 9:16 vertical Shorts from scratch.

Features:
- Native 1080x1920 vertical rendering (not cropped horizontal)
- AI-selected viral segments from main video script
- Portrait DALL-E 3 images (1024x1792) with cinematic or kids style
- Ken Burns animation with easing curves
- Animated captions (large, bold, mobile-optimized)
- Crossfade transitions between images (0.5s)
- Background music generation and mixing
- Kids content mode (bright colorful AI visuals, fun narration, cheerful music)
"""

import base64
import json
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import anthropic
import numpy as np
from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
)
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.services.asset_collector import AssetCollector
from app.services.caption_generator import SubtitleEntry
from app.utils.file_manager import get_unique_path


@dataclass
class ShortsResult:
    video_path: str
    duration_seconds: float
    hook_text: str
    cost_usd: float = 0.0


# --- Crossfade duration between image clips ---
CROSSFADE_SEC = 0.5

# --- Segment selection prompt (for extracting from main video) ---
SHORTS_EXTRACT_PROMPT = """Analyze this YouTube script and identify the SINGLE BEST 45-55 second segment for a YouTube Short.

Script:
{script}

Requirements for the perfect Short:
- Must be self-contained (viewer needs no context to understand)
- Must start with a hook that makes someone stop scrolling in <2 seconds
- Must deliver a complete "aha moment" or surprising revelation
- Must NOT require knowledge from earlier in the video
- Prefer segments with: shocking facts, surprising statistics, emotional stories, or controversial takes
- The segment should feel complete — not cut off mid-thought

Also extract 3-4 visual descriptions for AI image generation that match the segment content.

Return ONLY this JSON (no other text):
{{
  "start_sentence": "[exact first sentence of the segment]",
  "end_sentence": "[exact last sentence of the segment]",
  "hook_text": "[2-3 word hook to overlay at start, e.g. 'This is INSANE' or 'Nobody knows this']",
  "why": "[1 sentence why this segment will go viral as a Short]",
  "visuals": ["description 1 for AI image", "description 2", "description 3"]
}}"""

# --- Kids content prompts ---
KIDS_SCRIPT_PROMPT = """Write a fun, exciting 35-45 second narration for kids (ages 4-10) about: {topic}

Rules:
- Use simple words a 5-year-old can understand
- Start with something attention-grabbing: "Did you know...", "Guess what!", "Whoa! Check this out!"
- Build wonder and excitement throughout
- Include 2-3 amazing facts that will blow kids' minds
- End with something exciting: "How COOL is that?!", "Can you believe it?!", "Mind BLOWN!"
- Keep it between 70-100 words
- Sound super enthusiastic, like a fun teacher
- NO scary content, NO violence, NO complex words
- Use fun sound words: "WHOOSH!", "BOOM!", "WOW!", "SPLAT!"

Include exactly 4 [B-ROLL: description] markers for AI image generation.
Make B-ROLL descriptions vivid, colorful, fun, and kid-friendly.
Example: [B-ROLL: a cute cartoon T-Rex with big eyes smiling in a colorful jungle with butterflies]

Return ONLY the narration script with B-ROLL markers inline."""

KIDS_DALLE_PROMPT = (
    "A vibrant, colorful illustration for children: {description}. "
    "Bright cheerful saturated colors, cute cartoon-inspired style, "
    "friendly adorable characters with big expressive eyes, "
    "whimsical magical scene with sparkles and stars, "
    "soft rounded shapes, warm lighting, "
    "Pixar and Disney inspired quality, child-safe, "
    "professional children's book illustration, "
    "no text, no watermarks, no logos, no scary elements"
)


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


class ShortsGenerator:
    """Generate YouTube Shorts as native 9:16 vertical video from scratch."""

    SHORTS_MAX_DURATION = 58
    SHORTS_MIN_DURATION = 30
    SHORTS_RESOLUTION = (1080, 1920)  # 9:16 vertical
    FPS = 30

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.asset_collector = AssetCollector()
        self._font_path = self._find_font()

    # =========================================================================
    # MAIN ENTRY: GENERATE SHORT FROM MAIN VIDEO
    # =========================================================================

    def generate_short(
        self,
        video_path: str,
        script_text: str,
        voiceover_path: str,
        video_duration: float,
        caption_entries: list[SubtitleEntry] | None = None,
    ) -> ShortsResult | None:
        """Create a native 9:16 vertical Short from the main video's best segment."""
        try:
            # 1. AI selects best segment
            segment = self._find_best_segment(script_text)
            if not segment:
                logger.warning("Could not identify a good Short segment")
                return None

            total_cost = segment.get("cost", 0.0)

            # 2. Find timestamp range
            start_time, end_time = self._find_segment_timestamps(
                script_text, segment["start_sentence"], segment["end_sentence"],
                video_duration,
            )

            duration = end_time - start_time
            if duration > self.SHORTS_MAX_DURATION:
                end_time = start_time + self.SHORTS_MAX_DURATION
            elif duration < self.SHORTS_MIN_DURATION:
                end_time = min(start_time + self.SHORTS_MIN_DURATION, video_duration)

            duration = end_time - start_time

            # 3. Extract voiceover audio for this segment
            audio_segment_path = self._extract_audio_segment(
                voiceover_path, start_time, end_time
            )

            # 4. Generate portrait AI images for the Short
            visuals = segment.get("visuals", [])
            if not visuals:
                visuals = [segment.get("hook_text", "dramatic cinematic scene")]

            portrait_assets = self._generate_portrait_assets(visuals)
            total_cost += sum(a.get("cost", 0) for a in portrait_assets)

            # 5. Filter caption entries for this time range
            segment_captions = []
            if caption_entries:
                for entry in caption_entries:
                    if entry.start_time >= start_time and entry.end_time <= end_time + 1.0:
                        segment_captions.append(SubtitleEntry(
                            index=entry.index,
                            start_time=entry.start_time - start_time,
                            end_time=entry.end_time - start_time,
                            text=entry.text,
                        ))

            # 6. Generate background music
            music_path = self._generate_ambient_music(duration, style="cinematic")

            # 7. Render native 9:16 vertical video
            output_path = get_unique_path(settings.final_videos_dir, "short", ".mp4")
            self._render_vertical_short(
                audio_path=audio_segment_path,
                asset_paths=[a["path"] for a in portrait_assets],
                caption_entries=segment_captions,
                hook_text=segment.get("hook_text", "Watch This"),
                output_path=str(output_path),
                duration=duration,
                music_path=music_path,
            )

            logger.info(f"Native 9:16 Short rendered: {output_path} ({duration:.1f}s)")

            return ShortsResult(
                video_path=str(output_path),
                duration_seconds=duration,
                hook_text=segment.get("hook_text", ""),
                cost_usd=total_cost,
            )

        except Exception as e:
            logger.error(f"Shorts generation failed: {e}")
            return None

    # =========================================================================
    # KIDS SHORT: STANDALONE PIPELINE
    # =========================================================================

    def generate_kids_short(
        self,
        topic: str,
        voice_id: str = "nova",
    ) -> ShortsResult | None:
        """Generate a standalone kids-focused YouTube Short from scratch.

        Complete pipeline: script -> voiceover -> AI images -> music -> render.
        """
        try:
            total_cost = 0.0

            # 1. Generate kids script
            logger.info(f"Kids Short: Generating script for '{topic}'")
            script_text, script_cost = self._generate_kids_script(topic)
            total_cost += script_cost

            # 2. Clean script for TTS
            clean_script = re.sub(r"\[B-ROLL:.*?\]", "", script_text)
            clean_script = re.sub(r"\[.*?\]", "", clean_script)
            clean_script = re.sub(r"\*\*.*?\*\*", "", clean_script)
            clean_script = re.sub(r"\n{2,}", "\n", clean_script).strip()

            # 3. Generate voiceover with fun friendly voice
            logger.info("Kids Short: Generating voiceover")
            audio_path, vo_cost, vo_duration = self._generate_kids_voiceover(
                clean_script, voice_id
            )
            total_cost += vo_cost

            # 4. Extract B-ROLL markers and generate kids AI images
            markers = re.findall(r"\[B-ROLL:\s*(.+?)\]", script_text)
            if not markers:
                markers = [f"colorful fun illustration about {topic}"] * 3

            logger.info(f"Kids Short: Generating {len(markers)} AI images")
            portrait_assets = self._generate_kids_assets(markers[:4])
            total_cost += sum(a.get("cost", 0) for a in portrait_assets)

            # 5. Generate cheerful kids background music
            music_path = self._generate_ambient_music(vo_duration, style="kids")

            # 6. Render the Short
            output_path = get_unique_path(settings.final_videos_dir, "kids_short", ".mp4")
            hook_text = "SO COOL!"

            self._render_vertical_short(
                audio_path=audio_path,
                asset_paths=[a["path"] for a in portrait_assets],
                caption_entries=[],
                hook_text=hook_text,
                output_path=str(output_path),
                duration=vo_duration,
                music_path=music_path,
                is_kids=True,
            )

            logger.info(
                f"Kids Short rendered: {output_path} ({vo_duration:.1f}s), "
                f"cost=${total_cost:.4f}"
            )

            return ShortsResult(
                video_path=str(output_path),
                duration_seconds=vo_duration,
                hook_text=hook_text,
                cost_usd=total_cost,
            )

        except Exception as e:
            logger.error(f"Kids Short generation failed: {e}")
            return None

    def _generate_kids_script(self, topic: str) -> tuple[str, float]:
        """Generate a fun kids narration script using Claude."""
        prompt = KIDS_SCRIPT_PROMPT.format(topic=topic)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        cost = (
            (response.usage.input_tokens / 1_000_000) * 3.0
            + (response.usage.output_tokens / 1_000_000) * 15.0
        )
        return text, cost

    def _generate_kids_voiceover(
        self, script: str, voice_id: str = "nova"
    ) -> tuple[str, float, float]:
        """Generate kids voiceover using OpenAI TTS with a fun friendly voice."""
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        output_path = get_unique_path(settings.voiceovers_dir, "kids_vo", ".mp3")
        settings.voiceovers_dir.mkdir(parents=True, exist_ok=True)

        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice_id,
            input=script[:4000],
            speed=1.05,
        )

        with open(str(output_path), "wb") as f:
            f.write(response.content)

        audio = AudioFileClip(str(output_path))
        duration = audio.duration
        audio.close()

        cost = len(script) / 1000 * 0.030
        return str(output_path), cost, duration

    def _generate_kids_assets(self, descriptions: list[str]) -> list[dict]:
        """Generate bright colorful portrait AI images for kids Short."""
        assets = []
        output_dir = settings.footage_dir / "kids_shorts"
        output_dir.mkdir(parents=True, exist_ok=True)

        for desc in descriptions[:4]:
            asset = self._generate_kids_dalle_image(desc, output_dir)
            if asset:
                assets.append(asset)
            else:
                fallback = self.asset_collector._collect_single_asset(
                    desc, output_dir, orientation="portrait"
                )
                if fallback:
                    assets.append({
                        "path": fallback.local_path,
                        "cost": fallback.cost_usd,
                    })

        return assets

    def _generate_kids_dalle_image(self, description: str, output_dir: Path) -> dict | None:
        """Generate a kids-style portrait image using DALL-E 3."""
        try:
            import openai

            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = KIDS_DALLE_PROMPT.format(description=description)

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",
                quality="standard",
                n=1,
                response_format="b64_json",
            )

            image_data = base64.b64decode(response.data[0].b64_json)
            output_path = get_unique_path(output_dir, "kids_dalle", ".png")
            output_path.write_bytes(image_data)

            logger.info(f"Kids DALL-E image: {output_path}")
            return {"path": str(output_path), "cost": 0.040}

        except Exception as e:
            logger.warning(f"Kids DALL-E generation failed: {e}")
            return None

    # =========================================================================
    # AI SEGMENT SELECTION (for main video shorts)
    # =========================================================================

    def _find_best_segment(self, script_text: str) -> dict | None:
        """Use AI to find the most viral segment for a Short."""
        prompt = SHORTS_EXTRACT_PROMPT.format(script=script_text[:3000])

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        cost = (
            (response.usage.input_tokens / 1_000_000) * 3.0
            + (response.usage.output_tokens / 1_000_000) * 15.0
        )

        try:
            if "```" in text:
                text = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL).group(1)
            result = json.loads(text)
            result["cost"] = cost
            return result
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse segment selection: {e}")
            return None

    def _find_segment_timestamps(
        self,
        full_script: str,
        start_sentence: str,
        end_sentence: str,
        total_duration: float,
    ) -> tuple[float, float]:
        """Estimate timestamps for the selected segment based on word position."""
        words_per_second = 2.5

        clean_script = re.sub(r"\[.*?\]", "", full_script)
        clean_script = re.sub(r"\*\*.*?\*\*", "", clean_script)
        script_words = clean_script.split()
        total_words = len(script_words)

        start_words = start_sentence.split()[:6]
        start_search = " ".join(start_words).lower()
        start_pos = 0

        for i in range(len(script_words) - len(start_words)):
            window = " ".join(script_words[i:i + len(start_words)]).lower()
            if start_search in window or window in start_search:
                start_pos = i
                break

        end_words = end_sentence.split()[-6:]
        end_search = " ".join(end_words).lower()
        end_pos = min(start_pos + int(self.SHORTS_MAX_DURATION * words_per_second), total_words)

        for i in range(start_pos, min(start_pos + 200, len(script_words))):
            window = " ".join(script_words[i:i + len(end_words)]).lower()
            if end_search in window or window in end_search:
                end_pos = i + len(end_words)
                break

        intro_offset = 3.0
        start_time = intro_offset + (start_pos / total_words) * (total_duration - intro_offset)
        end_time = intro_offset + (end_pos / total_words) * (total_duration - intro_offset)

        return max(0, start_time), min(end_time, total_duration)

    # =========================================================================
    # AUDIO & ASSET PREPARATION
    # =========================================================================

    def _extract_audio_segment(
        self, voiceover_path: str, start: float, end: float
    ) -> str:
        """Extract audio segment using FFmpeg."""
        output_path = get_unique_path(settings.temp_dir, "short_audio", ".wav")
        settings.temp_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", voiceover_path,
            "-ss", f"{start:.2f}",
            "-to", f"{end:.2f}",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr[-300:]}")

        return str(output_path)

    def _generate_portrait_assets(self, visual_descriptions: list[str]) -> list[dict]:
        """Generate portrait-oriented AI images for the Short."""
        assets = []
        output_dir = settings.footage_dir / "shorts"
        output_dir.mkdir(parents=True, exist_ok=True)

        for desc in visual_descriptions[:4]:
            asset = self.asset_collector._collect_single_asset(
                desc, output_dir, orientation="portrait"
            )
            if asset:
                assets.append({
                    "path": asset.local_path,
                    "cost": asset.cost_usd,
                })
            else:
                logger.warning(f"Short asset failed for: '{desc}'")

        return assets

    # =========================================================================
    # BACKGROUND MUSIC GENERATION
    # =========================================================================

    def _generate_ambient_music(self, duration: float, style: str = "cinematic") -> str | None:
        """Generate ambient background music using FFmpeg audio synthesis."""
        settings.temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = get_unique_path(settings.temp_dir, f"music_{style}", ".wav")
        dur = int(duration) + 2
        fade_out_start = max(0, dur - 3)

        if style == "kids":
            # Cheerful major chord: C4 + E4 + G4 + C5
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"sine=frequency=261.63:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=329.63:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=392.00:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=523.25:duration={dur}",
                "-filter_complex",
                f"[0:a][1:a][2:a][3:a]amerge=inputs=4,"
                f"aformat=channel_layouts=stereo,"
                f"lowpass=f=2500,"
                f"tremolo=f=3:d=0.4,"
                f"volume=0.05,"
                f"afade=t=in:d=1,"
                f"afade=t=out:st={fade_out_start}:d=3",
                "-ar", "44100",
                str(output_path),
            ]
        else:
            # Cinematic ambient pad: C3 + Eb3 + G3 (minor chord)
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"sine=frequency=130.81:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=155.56:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=196.00:duration={dur}",
                "-filter_complex",
                f"[0:a][1:a][2:a]amerge=inputs=3,"
                f"aformat=channel_layouts=stereo,"
                f"lowpass=f=800,"
                f"tremolo=f=0.5:d=0.3,"
                f"volume=0.04,"
                f"afade=t=in:d=2,"
                f"afade=t=out:st={fade_out_start}:d=3",
                "-ar", "44100",
                str(output_path),
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning(f"Music generation failed: {result.stderr[-200:]}")
                return None
            logger.info(f"Background music generated: {output_path} ({style})")
            return str(output_path)
        except Exception as e:
            logger.warning(f"Music generation error: {e}")
            return None

    def _mix_audio_with_music(
        self, voiceover_path: str, music_path: str, duration: float
    ) -> str:
        """Mix voiceover with background music using FFmpeg (voice dominant)."""
        output_path = get_unique_path(settings.temp_dir, "mixed_audio", ".wav")

        cmd = [
            "ffmpeg", "-y",
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]atrim=0:{duration:.2f},asetpts=PTS-STARTPTS[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2",
            "-ar", "44100",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"Audio mixing failed: {result.stderr[-200:]}")
                return voiceover_path
            return str(output_path)
        except Exception:
            return voiceover_path

    # =========================================================================
    # NATIVE 9:16 VERTICAL RENDERING
    # =========================================================================

    def _render_vertical_short(
        self,
        audio_path: str,
        asset_paths: list[str],
        caption_entries: list[SubtitleEntry],
        hook_text: str,
        output_path: str,
        duration: float,
        music_path: str | None = None,
        is_kids: bool = False,
    ) -> None:
        """Render a native 1080x1920 vertical Short using MoviePy."""
        w, h = self.SHORTS_RESOLUTION

        # Mix voiceover with background music if available
        if music_path and Path(music_path).exists():
            final_audio_path = self._mix_audio_with_music(audio_path, music_path, duration)
        else:
            final_audio_path = audio_path

        # Load audio
        audio = AudioFileClip(final_audio_path)
        actual_duration = audio.duration

        # Build visual track from portrait images with Ken Burns + crossfade
        visual_clip = self._build_vertical_visuals(asset_paths, actual_duration)

        # Create caption overlay
        caption_clip = None
        if caption_entries:
            caption_clip = self._create_vertical_captions(
                caption_entries, actual_duration
            )

        # Create hook text overlay (first 3 seconds)
        hook_clip = self._create_hook_overlay(
            hook_text, min(3.0, actual_duration), is_kids=is_kids
        )

        # Create CTA overlay (last 4 seconds)
        cta_clip = self._create_cta_overlay(actual_duration, is_kids=is_kids)

        # Composite all layers
        layers = [visual_clip]
        if caption_clip:
            layers.append(caption_clip)
        layers.append(hook_clip)
        layers.append(cta_clip)

        final = CompositeVideoClip(layers, size=(w, h))
        final = final.with_duration(actual_duration)
        final = final.with_audio(audio)

        # Export — high quality encoding (CRF 18, no conflicting bitrate)
        settings.final_videos_dir.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            output_path,
            fps=self.FPS,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None,
            ffmpeg_params=[
                "-movflags", "+faststart",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-profile:v", "high",
                "-level", "4.0",
            ],
        )

        final.close()
        audio.close()

    def _build_vertical_visuals(
        self, asset_paths: list[str], duration: float
    ) -> CompositeVideoClip:
        """Build vertical visual track with crossfade transitions between images."""
        w, h = self.SHORTS_RESOLUTION

        if not asset_paths:
            return ColorClip(size=(w, h), color=(15, 15, 25)).with_duration(duration)

        valid_paths = [p for p in asset_paths if Path(p).exists()]
        if not valid_paths:
            return ColorClip(size=(w, h), color=(15, 15, 25)).with_duration(duration)

        n = len(valid_paths)
        # Account for crossfade overlap in segment duration
        overlap_total = CROSSFADE_SEC * max(0, n - 1)
        segment_dur = (duration + overlap_total) / n

        clips = []
        for path in valid_paths:
            try:
                clip = self._prepare_portrait_image(path, segment_dur)
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Failed to load Short asset {path}: {e}")
                clips.append(
                    ColorClip(size=(w, h), color=(15, 15, 25))
                    .with_duration(segment_dur)
                )

        if len(clips) == 1:
            return clips[0].with_duration(duration)

        # Composite with crossfade transitions (opacity-based blending)
        composed = []
        current_time = 0.0

        for i, clip in enumerate(clips):
            fade_in = i > 0
            fade_out = i < len(clips) - 1
            clip_dur = clip.duration

            if fade_in or fade_out:
                def make_fade(get_frame, t, d=clip_dur, fi=fade_in, fo=fade_out):
                    frame = get_frame(t)
                    alpha = 1.0
                    if fi and t < CROSSFADE_SEC:
                        alpha = t / CROSSFADE_SEC
                    if fo and t > d - CROSSFADE_SEC:
                        alpha = min(alpha, (d - t) / CROSSFADE_SEC)
                    if alpha < 1.0:
                        frame = (frame * alpha).astype(np.uint8)
                    return frame
                clip = clip.transform(make_fade)

            clip = clip.with_start(current_time)
            composed.append(clip)

            if i < len(clips) - 1:
                current_time += clip_dur - CROSSFADE_SEC
            else:
                current_time += clip_dur

        result = CompositeVideoClip(composed, size=(w, h))
        return result.with_duration(duration)

    def _prepare_portrait_image(
        self, path: str, duration: float
    ) -> ImageClip:
        """Load portrait image with Ken Burns animation for 9:16."""
        w, h = self.SHORTS_RESOLUTION
        img = Image.open(path).convert("RGB")

        # Scale to fill with 20% extra for Ken Burns room
        margin = 1.20
        target_w = int(w * margin)
        target_h = int(h * margin)

        # Resize maintaining aspect ratio, then crop to fill
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            new_h = target_h
            new_w = int(img.width * (target_h / img.height))
        else:
            new_w = target_w
            new_h = int(img.height * (target_w / img.width))

        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop to target
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        img_array = np.array(img)
        clip = ImageClip(img_array).with_duration(duration)

        direction = random.choice(["zoom_in", "zoom_out", "pan_up", "pan_down"])

        def ken_burns_vertical(get_frame, t, dur=duration, d=direction):
            progress = _ease_in_out_cubic(t / dur)
            frame = get_frame(t)
            fh, fw = frame.shape[:2]

            if d == "zoom_in":
                scale = 1.0 + (margin - 1.0) * progress
            elif d == "zoom_out":
                scale = margin - (margin - 1.0) * progress
            elif d == "pan_up":
                offset_x = (fw - w) // 2
                offset_y = int((fh - h) * (1.0 - progress))
                cropped = frame[offset_y:offset_y + h, offset_x:offset_x + w]
                return np.array(Image.fromarray(cropped).resize((w, h), Image.LANCZOS))
            else:  # pan_down
                offset_x = (fw - w) // 2
                offset_y = int((fh - h) * progress)
                cropped = frame[offset_y:offset_y + h, offset_x:offset_x + w]
                return np.array(Image.fromarray(cropped).resize((w, h), Image.LANCZOS))

            new_w = int(w / scale * (fw / w))
            new_h = int(h / scale * (fh / h))
            x = (fw - new_w) // 2
            y = (fh - new_h) // 2
            cropped = frame[max(0, y):y + new_h, max(0, x):x + new_w]
            return np.array(Image.fromarray(cropped).resize((w, h), Image.LANCZOS))

        clip = clip.transform(ken_burns_vertical)
        return clip

    # =========================================================================
    # VERTICAL CAPTIONS (mobile-optimized, large bold text)
    # =========================================================================

    def _create_vertical_captions(
        self,
        entries: list[SubtitleEntry],
        duration: float,
    ) -> CompositeVideoClip:
        """Create animated caption overlay for vertical Short."""
        w, h = self.SHORTS_RESOLUTION
        clips = []

        for entry in entries:
            if not entry.text or entry.text == "...":
                continue

            dur = entry.end_time - entry.start_time
            if dur <= 0.05:
                continue

            caption_img = self._render_vertical_caption(entry.text)
            caption_array = np.array(caption_img)

            y_pos = int(h * 0.65)

            def make_animated(get_frame, t, d=dur, arr=caption_array):
                frame = get_frame(t)
                if t < 0.12 and d > 0.15:
                    progress = _ease_out_cubic(t / 0.12)
                    scale = 0.85 + 0.15 * progress
                    alpha = progress
                elif t > d - 0.1 and d > 0.15:
                    alpha = max(0, (d - t) / 0.1)
                    scale = 1.0
                else:
                    scale = 1.0
                    alpha = 1.0

                fh, fw = frame.shape[:2]
                if abs(scale - 1.0) > 0.01:
                    nw = max(1, int(fw * scale))
                    nh = max(1, int(fh * scale))
                    pil = Image.fromarray(frame).resize((nw, nh), Image.LANCZOS)
                    canvas = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                    canvas.paste(pil, ((fw - nw) // 2, (fh - nh) // 2))
                    frame = np.array(canvas)

                if alpha < 1.0:
                    frame = frame.copy()
                    if frame.shape[2] == 4:
                        frame[:, :, 3] = (frame[:, :, 3] * alpha).astype(np.uint8)

                return frame

            img_clip = ImageClip(caption_array).with_duration(dur)
            img_clip = img_clip.transform(make_animated)
            img_clip = img_clip.with_start(entry.start_time)
            img_clip = img_clip.with_position(("center", y_pos))
            clips.append(img_clip)

        if not clips:
            base = ColorClip(size=(w, h), color=(0, 0, 0)).with_duration(duration)
            return base.with_opacity(0)

        base = ColorClip(size=(w, h), color=(0, 0, 0)).with_duration(duration)
        base = base.with_opacity(0)
        return CompositeVideoClip([base] + clips, size=(w, h))

    def _render_vertical_caption(self, text: str) -> Image.Image:
        """Render a single caption frame — large bold text for mobile viewing."""
        w = self.SHORTS_RESOLUTION[0]
        max_text_width = int(w * 0.88)
        font_size = 80
        stroke_width = 4
        font = self._get_font(font_size)

        # Word wrap
        words = text.split()
        lines = []
        current = []
        tmp_img = Image.new("RGBA", (max_text_width + 100, 500), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp_img)

        for word in words:
            test = current + [word]
            bbox = tmp_draw.textbbox((0, 0), " ".join(test), font=font)
            if bbox[2] > max_text_width and current:
                lines.append(current[:])
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(current)

        # Calculate dimensions
        line_height = tmp_draw.textbbox((0, 0), "Ay", font=font)[3] + 16
        padding_x, padding_y = 32, 20
        total_height = line_height * len(lines) + padding_y * 2
        img_width = max_text_width + padding_x * 2

        img = Image.new("RGBA", (img_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background pill — high opacity for mobile contrast
        draw.rounded_rectangle(
            [6, 6, img_width - 6, total_height - 6],
            radius=20,
            fill=(0, 0, 0, 200),
        )

        # Draw text with emphasis highlighting
        y = padding_y
        emphasis_words = {
            "never", "always", "insane", "shocking", "secret", "crazy", "incredible",
            "massive", "huge", "impossible", "dangerous", "powerful", "deadly",
            "worst", "best", "only", "every", "million", "billion", "free",
        }

        for line_words in lines:
            line_str = " ".join(line_words)
            line_bbox = draw.textbbox((0, 0), line_str, font=font)
            line_w = line_bbox[2] - line_bbox[0]
            x = (img_width - line_w) // 2

            for word in line_words:
                word_display = word + " "
                word_bbox = draw.textbbox((0, 0), word_display, font=font)
                word_w = word_bbox[2] - word_bbox[0]

                # Thick black stroke for mobile visibility
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx * dx + dy * dy <= stroke_width * stroke_width:
                            draw.text((x + dx, y + dy), word_display, font=font,
                                      fill=(0, 0, 0, 255))

                # Highlight emphasis words in gold
                clean = word.strip(".,!?;:'\"()-")
                is_emphasis = (
                    (clean.isupper() and len(clean) > 1)
                    or clean.lower() in emphasis_words
                    or re.match(r"^\$?\d[\d,.%]+", clean)
                )
                color = (255, 215, 0, 255) if is_emphasis else (255, 255, 255, 255)
                draw.text((x, y), word_display, font=font, fill=color)
                x += word_w

            y += line_height

        return img

    # =========================================================================
    # OVERLAYS
    # =========================================================================

    def _create_hook_overlay(
        self, hook_text: str, duration: float, is_kids: bool = False
    ) -> ImageClip:
        """Create hook text overlay for first 3 seconds."""
        w, h = self.SHORTS_RESOLUTION
        font = self._get_font(80)

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), hook_text.upper(), font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (w - text_w) // 2
        y = int(h * 0.12)

        pill_pad = 24
        if is_kids:
            pill_color = (255, 200, 0, 220)
            text_color = (50, 50, 50, 255)
        else:
            pill_color = (255, 0, 0, 200)
            text_color = (255, 255, 255, 255)

        draw.rounded_rectangle(
            [x - pill_pad, y - pill_pad, x + text_w + pill_pad, y + text_h + pill_pad],
            radius=16,
            fill=pill_color,
        )

        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    draw.text((x + dx, y + dy), hook_text.upper(), font=font,
                              fill=(0, 0, 0, 255))
        draw.text((x, y), hook_text.upper(), font=font, fill=text_color)

        hook_array = np.array(img)
        clip = ImageClip(hook_array).with_duration(duration)
        clip = clip.with_start(0)
        return clip

    def _create_cta_overlay(
        self, total_duration: float, is_kids: bool = False
    ) -> ImageClip:
        """Create CTA overlay for last 4 seconds."""
        w, h = self.SHORTS_RESOLUTION
        cta_duration = min(4.0, total_duration * 0.3)
        font = self._get_font(44)

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cta_text = "Like & Subscribe!" if is_kids else "Full video on channel"
        bbox = draw.textbbox((0, 0), cta_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (w - text_w) // 2
        y = int(h * 0.90)

        pill_pad = 16
        pill_color = (0, 180, 0, 200) if is_kids else (0, 0, 0, 150)

        draw.rounded_rectangle(
            [x - pill_pad, y - pill_pad, x + text_w + pill_pad, y + text_h + pill_pad],
            radius=12,
            fill=pill_color,
        )

        draw.text((x, y), cta_text, font=font, fill=(255, 255, 255, 240))

        cta_array = np.array(img)
        clip = ImageClip(cta_array).with_duration(cta_duration)
        clip = clip.with_start(total_duration - cta_duration)
        return clip

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _find_font(self) -> str | None:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for fp in font_paths:
            if Path(fp).exists():
                return fp
        return None

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if self._font_path:
            try:
                return ImageFont.truetype(self._font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()
