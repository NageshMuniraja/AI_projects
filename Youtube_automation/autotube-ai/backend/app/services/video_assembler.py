"""Video Assembler Service — cinematic video assembly using MoviePy 2.x and FFmpeg.

Features:
- Crossfade transitions between clips (0.4s)
- Animated captions with scale pop-in, word highlighting, background pill
- Enhanced Ken Burns with easing curves and random pan directions
- Animated intro (fade+zoom) and outro (pulse subscribe CTA)
- Background music with voice-activity audio ducking
- Transition sound effects
"""

import random
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
    AudioClip,
)
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pydub import AudioSegment

from app.config import settings
from app.services.caption_generator import SubtitleEntry
from app.utils.file_manager import get_unique_path

# --- Constants ---
CROSSFADE_DURATION = 0.4
CAPTION_FADE_IN = 0.12
CAPTION_FADE_OUT = 0.10
CAPTION_SCALE_START = 0.85
INTRO_DURATION = 3.0
OUTRO_DURATION = 5.0
MUSIC_DUCK_DB = -18  # dB reduction during speech
MUSIC_BED_DB = -8    # dB during silence


@dataclass
class VideoComponents:
    voiceover_path: str
    asset_paths: list[str]
    asset_types: list[str]
    subtitle_entries: list[SubtitleEntry] = field(default_factory=list)
    channel_name: str = "AutoTube AI"
    caption_style: str = "hormozi"
    music_path: str | None = None
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30


@dataclass
class AssembledVideo:
    video_path: str
    duration_seconds: float
    resolution: tuple[int, int]


def _ease_out_cubic(t: float) -> float:
    """Cubic ease-out: fast start, slow end."""
    return 1.0 - (1.0 - t) ** 3


def _ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out: smooth acceleration and deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


def _is_emphasis_word(word: str) -> bool:
    """Detect words that should be highlighted in captions."""
    clean = word.strip(".,!?;:'\"()-")
    if clean.isupper() and len(clean) > 1:
        return True
    if re.match(r"^\$?\d[\d,.%]+[KMBkmbx]*$", clean):
        return True
    emphasis_words = {
        "never", "always", "insane", "shocking", "secret", "crazy", "incredible",
        "unbelievable", "massive", "huge", "tiny", "impossible", "dangerous",
        "powerful", "deadly", "genius", "worst", "best", "first", "last",
        "only", "every", "million", "billion", "trillion", "free", "instantly",
    }
    return clean.lower() in emphasis_words


class VideoAssembler:
    def __init__(self):
        self.default_resolution = (1920, 1080)
        self.fps = settings.DEFAULT_FPS
        self._font_path = self._find_font()

    # =========================================================================
    # MAIN ASSEMBLY
    # =========================================================================

    def assemble_video(self, components: VideoComponents) -> AssembledVideo:
        """Assemble a cinematic video from all components."""
        resolution = components.resolution
        logger.info(f"Assembling video: {len(components.asset_paths)} assets, "
                     f"{resolution[0]}x{resolution[1]}")

        # 1. Load voiceover — determines total duration
        voiceover = AudioFileClip(components.voiceover_path)
        total_duration = voiceover.duration
        logger.info(f"Voiceover duration: {total_duration:.1f}s")

        # 2. Build visual track with crossfade transitions
        visual_clip = self._build_visual_track_with_transitions(
            components.asset_paths,
            components.asset_types,
            total_duration,
            resolution,
        )

        # 3. Create animated captions overlay
        caption_clip = None
        if components.subtitle_entries:
            caption_clip = self._create_animated_caption_overlay(
                components.subtitle_entries,
                total_duration,
                resolution,
                style=components.caption_style,
            )

        # 4. Create animated intro
        intro_clip = self._create_animated_intro(components.channel_name, resolution)

        # 5. Create animated outro
        outro_clip = self._create_animated_outro(components.channel_name, resolution)

        # 6. Composite visual + captions
        layers = [visual_clip]
        if caption_clip:
            layers.append(caption_clip)

        main_video = CompositeVideoClip(layers, size=resolution)
        main_video = main_video.with_duration(total_duration)

        # 7. Combine intro + main + outro
        final_video = concatenate_videoclips(
            [intro_clip, main_video, outro_clip],
            method="compose",
        )

        # 8. Build audio mix (voiceover + music with ducking)
        final_audio = self._build_audio_mix(
            voiceover,
            components.music_path,
            intro_clip.duration,
            outro_clip.duration,
            total_duration,
        )
        final_video = final_video.with_audio(final_audio)

        # 9. Export
        output_path = get_unique_path(settings.final_videos_dir, "video", ".mp4")

        logger.info(f"Exporting video to {output_path}...")
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            bitrate=settings.DEFAULT_VIDEO_BITRATE,
            preset="medium",
            threads=4,
            logger=None,
        )

        duration = final_video.duration

        # Cleanup
        voiceover.close()
        final_video.close()

        logger.info(f"Video assembled: {output_path} ({duration:.1f}s)")

        return AssembledVideo(
            video_path=str(output_path),
            duration_seconds=duration,
            resolution=resolution,
        )

    # =========================================================================
    # VISUAL TRACK WITH CROSSFADE TRANSITIONS
    # =========================================================================

    def _build_visual_track_with_transitions(
        self,
        asset_paths: list[str],
        asset_types: list[str],
        total_duration: float,
        resolution: tuple[int, int],
    ) -> CompositeVideoClip:
        """Build visual track with crossfade transitions between clips."""
        if not asset_paths:
            return ColorClip(size=resolution, color=(15, 15, 25)).with_duration(total_duration)

        # Prepare individual clips
        raw_clips = []
        n = len(asset_paths)
        # Each segment is slightly longer to account for crossfade overlap
        overlap_total = CROSSFADE_DURATION * max(0, n - 1)
        segment_duration = (total_duration + overlap_total) / n

        for path, atype in zip(asset_paths, asset_types):
            path = Path(path)
            if not path.exists():
                logger.warning(f"Asset not found: {path}, using dark frame")
                raw_clips.append(
                    ColorClip(size=resolution, color=(15, 15, 25))
                    .with_duration(segment_duration)
                )
                continue

            try:
                if atype == "stock_video":
                    clip = self._prepare_video_clip(str(path), segment_duration, resolution)
                else:
                    clip = self._prepare_image_clip_enhanced(str(path), segment_duration, resolution)
                raw_clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to process asset {path}: {e}")
                raw_clips.append(
                    ColorClip(size=resolution, color=(15, 15, 25))
                    .with_duration(segment_duration)
                )

        if len(raw_clips) == 1:
            clip = raw_clips[0]
            if clip.duration > total_duration:
                clip = clip.subclipped(0, total_duration)
            elif clip.duration < total_duration:
                clip = clip.with_duration(total_duration)
            return clip

        # Apply crossfade: stagger clips with overlap, apply fade in/out
        composed_clips = []
        current_time = 0.0

        for i, clip in enumerate(raw_clips):
            # Fade in (except first clip)
            if i > 0:
                clip = clip.with_effects([
                    lambda c, dur=CROSSFADE_DURATION: c.crossfadein(dur)
                ]) if hasattr(clip, 'crossfadein') else clip

            # Fade out (except last clip)
            if i < len(raw_clips) - 1:
                clip = clip.with_effects([
                    lambda c, dur=CROSSFADE_DURATION: c.crossfadeout(dur)
                ]) if hasattr(clip, 'crossfadeout') else clip

            clip = clip.with_start(current_time)
            composed_clips.append(clip)

            # Next clip starts CROSSFADE_DURATION before this one ends
            if i < len(raw_clips) - 1:
                current_time += clip.duration - CROSSFADE_DURATION
            else:
                current_time += clip.duration

        result = CompositeVideoClip(composed_clips, size=resolution)
        # Trim to exact duration needed
        if result.duration > total_duration:
            result = result.subclipped(0, total_duration)
        return result.with_duration(total_duration)

    def _prepare_video_clip(
        self, path: str, target_duration: float, resolution: tuple[int, int]
    ) -> VideoFileClip:
        """Load, resize, and trim/loop a video clip."""
        clip = VideoFileClip(path)
        clip = self._resize_and_crop(clip, resolution)

        if clip.duration >= target_duration:
            clip = clip.subclipped(0, target_duration)
        else:
            loops = int(target_duration / clip.duration) + 1
            clip = concatenate_videoclips([clip] * loops).subclipped(0, target_duration)

        return clip.without_audio()

    # =========================================================================
    # ENHANCED KEN BURNS (easing + random direction)
    # =========================================================================

    def _prepare_image_clip_enhanced(
        self, path: str, duration: float, resolution: tuple[int, int]
    ) -> ImageClip:
        """Ken Burns with easing curves and randomized pan direction."""
        img = Image.open(path).convert("RGB")

        # 20% larger for zoom/pan room
        margin = 1.20
        zoom_w = int(resolution[0] * margin)
        zoom_h = int(resolution[1] * margin)
        img = img.resize((zoom_w, zoom_h), Image.LANCZOS)

        img_array = np.array(img)
        clip = ImageClip(img_array).with_duration(duration)

        # Random direction: zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down
        direction = random.choice([
            "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down",
        ])
        res_w, res_h = resolution

        def ken_burns_enhanced(get_frame, t):
            progress = _ease_in_out_cubic(t / duration)
            frame = get_frame(t)
            fh, fw = frame.shape[:2]

            if direction == "zoom_in":
                scale = 1.0 + (margin - 1.0) * progress
            elif direction == "zoom_out":
                scale = margin - (margin - 1.0) * progress
            elif direction == "pan_left":
                scale = 1.0
                offset_x = int((fw - res_w) * (1.0 - progress))
                offset_y = (fh - res_h) // 2
                cropped = frame[offset_y:offset_y + res_h, offset_x:offset_x + res_w]
                return np.array(Image.fromarray(cropped).resize(resolution, Image.LANCZOS))
            elif direction == "pan_right":
                scale = 1.0
                offset_x = int((fw - res_w) * progress)
                offset_y = (fh - res_h) // 2
                cropped = frame[offset_y:offset_y + res_h, offset_x:offset_x + res_w]
                return np.array(Image.fromarray(cropped).resize(resolution, Image.LANCZOS))
            elif direction == "pan_up":
                scale = 1.0
                offset_x = (fw - res_w) // 2
                offset_y = int((fh - res_h) * (1.0 - progress))
                cropped = frame[offset_y:offset_y + res_h, offset_x:offset_x + res_w]
                return np.array(Image.fromarray(cropped).resize(resolution, Image.LANCZOS))
            else:  # pan_down
                scale = 1.0
                offset_x = (fw - res_w) // 2
                offset_y = int((fh - res_h) * progress)
                cropped = frame[offset_y:offset_y + res_h, offset_x:offset_x + res_w]
                return np.array(Image.fromarray(cropped).resize(resolution, Image.LANCZOS))

            new_w = int(res_w / scale * (fw / res_w))
            new_h = int(res_h / scale * (fh / res_h))
            x = (fw - new_w) // 2
            y = (fh - new_h) // 2
            cropped = frame[max(0, y):y + new_h, max(0, x):x + new_w]
            pil_img = Image.fromarray(cropped).resize(resolution, Image.LANCZOS)
            return np.array(pil_img)

        clip = clip.transform(ken_burns_enhanced)
        return clip

    def _resize_and_crop(self, clip, resolution: tuple[int, int]):
        """Resize video clip to resolution with center crop."""
        target_w, target_h = resolution
        target_ratio = target_w / target_h
        clip_ratio = clip.w / clip.h

        if clip_ratio > target_ratio:
            new_h = target_h
            new_w = int(clip.w * (target_h / clip.h))
        else:
            new_w = target_w
            new_h = int(clip.h * (target_w / clip.w))

        clip = clip.resized((new_w, new_h))
        x = (new_w - target_w) // 2
        y = (new_h - target_h) // 2
        clip = clip.cropped(x1=x, y1=y, x2=x + target_w, y2=y + target_h)
        return clip

    # =========================================================================
    # ANIMATED CAPTIONS (MrBeast/Hormozi style)
    # =========================================================================

    def _create_animated_caption_overlay(
        self,
        entries: list[SubtitleEntry],
        total_duration: float,
        resolution: tuple[int, int],
        style: str = "hormozi",
    ) -> CompositeVideoClip:
        """Create animated caption overlay with pop-in, highlighting, and fade-out."""
        clips = []
        w, h = resolution

        for i, entry in enumerate(entries):
            if not entry.text or entry.text == "...":
                continue

            duration = entry.end_time - entry.start_time
            if duration <= 0.05:
                continue

            # Render caption frame with word highlighting and background pill
            caption_img = self._render_caption_frame_enhanced(
                entry.text, w, style=style
            )
            caption_array = np.array(caption_img)
            cap_h, cap_w = caption_array.shape[:2]

            # Position: alternate between center-bottom and slightly higher
            y_pos = h - 220 if i % 2 == 0 else h - 260

            # Create the clip with scale pop-in animation
            def make_frame_animated(get_frame, t, dur=duration, arr=caption_array,
                                     cw=cap_w, ch=cap_h, target_w=w):
                # Scale pop-in: 0.85 → 1.0 over first 0.15s
                if t < CAPTION_FADE_IN and dur > CAPTION_FADE_IN:
                    progress = _ease_out_cubic(t / CAPTION_FADE_IN)
                    scale = CAPTION_SCALE_START + (1.0 - CAPTION_SCALE_START) * progress
                    alpha_mult = progress
                elif t > dur - CAPTION_FADE_OUT and dur > CAPTION_FADE_OUT:
                    # Fade out
                    progress = (dur - t) / CAPTION_FADE_OUT
                    scale = 1.0
                    alpha_mult = max(0, progress)
                else:
                    scale = 1.0
                    alpha_mult = 1.0

                frame = get_frame(t)

                if abs(scale - 1.0) > 0.01:
                    new_w = max(1, int(cw * scale))
                    new_h = max(1, int(ch * scale))
                    pil = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
                    # Center on original size canvas
                    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                    paste_x = (cw - new_w) // 2
                    paste_y = (ch - new_h) // 2
                    canvas.paste(pil, (paste_x, paste_y))
                    frame = np.array(canvas)

                if alpha_mult < 1.0:
                    frame = frame.copy()
                    if frame.shape[2] == 4:
                        frame[:, :, 3] = (frame[:, :, 3] * alpha_mult).astype(np.uint8)

                return frame

            img_clip = ImageClip(caption_array).with_duration(duration)
            img_clip = img_clip.transform(make_frame_animated)
            img_clip = img_clip.with_start(entry.start_time)
            img_clip = img_clip.with_position(("center", y_pos))

            clips.append(img_clip)

        if not clips:
            base = ColorClip(size=resolution, color=(0, 0, 0)).with_duration(total_duration)
            return base.with_opacity(0)

        base = ColorClip(size=resolution, color=(0, 0, 0)).with_duration(total_duration)
        base = base.with_opacity(0)

        return CompositeVideoClip([base] + clips, size=resolution)

    def _render_caption_frame_enhanced(
        self, text: str, video_width: int, style: str = "hormozi"
    ) -> Image.Image:
        """Render caption with background pill and word-level highlighting."""
        max_width = int(video_width * 0.75)
        font_size = 72 if style == "hormozi" else 52
        font = self._get_font(font_size)

        # Word wrap
        words = text.split()
        lines = []
        current_line_words = []
        img_tmp = Image.new("RGBA", (max_width + 100, 500), (0, 0, 0, 0))
        draw_tmp = ImageDraw.Draw(img_tmp)

        for word in words:
            test_words = current_line_words + [word]
            test_str = " ".join(test_words)
            bbox = draw_tmp.textbbox((0, 0), test_str, font=font)
            if bbox[2] > max_width and current_line_words:
                lines.append(current_line_words[:])
                current_line_words = [word]
            else:
                current_line_words.append(word)
        if current_line_words:
            lines.append(current_line_words)

        # Calculate dimensions
        line_height = draw_tmp.textbbox((0, 0), "Ay", font=font)[3] + 14
        padding_x, padding_y = 30, 20
        total_text_height = line_height * len(lines)
        img_height = total_text_height + padding_y * 2
        img_width = max_width + padding_x * 2

        # Create image with transparent background
        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw background pill (rounded rectangle)
        pill_margin = 8
        draw.rounded_rectangle(
            [pill_margin, pill_margin, img_width - pill_margin, img_height - pill_margin],
            radius=20,
            fill=(0, 0, 0, 153),  # 60% opacity black
        )

        # Draw each line with word-level highlighting
        y = padding_y
        for line_words in lines:
            # Calculate line width for centering
            line_str = " ".join(line_words)
            line_bbox = draw.textbbox((0, 0), line_str, font=font)
            line_width = line_bbox[2] - line_bbox[0]
            x_start = (img_width - line_width) // 2

            x = x_start
            for word in line_words:
                is_emphasis = _is_emphasis_word(word)
                word_display = word + " "
                word_bbox = draw.textbbox((0, 0), word_display, font=font)
                word_w = word_bbox[2] - word_bbox[0]

                # Stroke/outline
                stroke_width = 3
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx * dx + dy * dy <= stroke_width * stroke_width:
                            draw.text((x + dx, y + dy), word_display, font=font,
                                      fill=(0, 0, 0, 255))

                # Main text color
                if is_emphasis:
                    color = (255, 215, 0, 255)  # Gold for emphasis
                elif style == "hormozi":
                    color = (255, 255, 255, 255)
                else:
                    color = (255, 255, 255, 230)

                draw.text((x, y), word_display, font=font, fill=color)
                x += word_w

            y += line_height

        return img

    # =========================================================================
    # ANIMATED INTRO (fade + zoom)
    # =========================================================================

    def _create_animated_intro(
        self, channel_name: str, resolution: tuple[int, int], duration: float = INTRO_DURATION
    ) -> CompositeVideoClip:
        """Create intro with gradient background and text fade+zoom animation."""
        w, h = resolution

        # Gradient background (#0a0a1a → #1a1a3e)
        bg_img = self._create_gradient((10, 10, 26), (26, 26, 62), w, h)
        bg_clip = ImageClip(np.array(bg_img)).with_duration(duration)

        # Render channel name text
        font = self._get_font(96)
        text_img = Image.new("RGBA", resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        bbox = draw.textbbox((0, 0), channel_name, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (w - text_w) // 2
        y = (h - text_h) // 2

        # Stroke
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    draw.text((x + dx, y + dy), channel_name, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), channel_name, font=font, fill=(255, 215, 0, 255))

        text_array = np.array(text_img)
        text_clip = ImageClip(text_array).with_duration(duration)

        # Animate: fade in (0→1) + zoom (0.7→1.0) over 1.5s with ease-out
        def intro_animation(get_frame, t, dur=duration):
            anim_dur = min(1.5, dur * 0.8)
            if t < anim_dur:
                progress = _ease_out_cubic(t / anim_dur)
            else:
                progress = 1.0

            frame = get_frame(t)
            alpha_mult = progress
            scale = 0.7 + 0.3 * progress

            fh, fw = frame.shape[:2]
            if abs(scale - 1.0) > 0.01:
                new_w = max(1, int(fw * scale))
                new_h = max(1, int(fh * scale))
                pil = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
                canvas = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                canvas.paste(pil, ((fw - new_w) // 2, (fh - new_h) // 2))
                frame = np.array(canvas)

            if alpha_mult < 1.0:
                frame = frame.copy()
                if frame.shape[2] == 4:
                    frame[:, :, 3] = (frame[:, :, 3] * alpha_mult).astype(np.uint8)

            return frame

        text_clip = text_clip.transform(intro_animation)

        return CompositeVideoClip([bg_clip, text_clip], size=resolution)

    # =========================================================================
    # ANIMATED OUTRO (pulsing subscribe CTA)
    # =========================================================================

    def _create_animated_outro(
        self, channel_name: str, resolution: tuple[int, int], duration: float = OUTRO_DURATION
    ) -> CompositeVideoClip:
        """Create outro with pulsing SUBSCRIBE and animated channel name."""
        w, h = resolution
        import math

        # Gradient background
        bg_img = self._create_gradient((10, 10, 26), (26, 26, 62), w, h)
        bg_clip = ImageClip(np.array(bg_img)).with_duration(duration)

        # Render subscribe button
        sub_img = Image.new("RGBA", resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(sub_img)

        # Red subscribe button
        btn_w, btn_h = 450, 80
        btn_x = (w - btn_w) // 2
        btn_y = h // 2 - 60
        draw.rounded_rectangle(
            [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
            radius=12,
            fill=(255, 0, 0, 255),
        )

        font_sub = self._get_font(44)
        sub_text = "SUBSCRIBE"
        text_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
        tx = btn_x + (btn_w - (text_bbox[2] - text_bbox[0])) // 2
        ty = btn_y + (btn_h - (text_bbox[3] - text_bbox[1])) // 2
        draw.text((tx, ty), sub_text, font=font_sub, fill=(255, 255, 255, 255))

        # Channel name below
        font_name = self._get_font(40)
        name_bbox = draw.textbbox((0, 0), channel_name, font=font_name)
        nx = (w - (name_bbox[2] - name_bbox[0])) // 2
        draw.text((nx, btn_y + btn_h + 30), channel_name, font=font_name,
                  fill=(255, 255, 255, 200))

        sub_array = np.array(sub_img)
        sub_clip = ImageClip(sub_array).with_duration(duration)

        # Animate: subtle pulse (1.0→1.04→1.0 over 1s cycle) + fade in
        def outro_animation(get_frame, t, dur=duration):
            # Fade in during first 1s
            fade_progress = min(1.0, t / 1.0)
            alpha = _ease_out_cubic(fade_progress)

            # Pulse effect
            pulse = 1.0 + 0.04 * math.sin(t * math.pi * 2)

            frame = get_frame(t)
            fh, fw = frame.shape[:2]

            if abs(pulse - 1.0) > 0.005:
                new_w = max(1, int(fw * pulse))
                new_h = max(1, int(fh * pulse))
                pil = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
                canvas = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                canvas.paste(pil, ((fw - new_w) // 2, (fh - new_h) // 2))
                frame = np.array(canvas)

            if alpha < 1.0:
                frame = frame.copy()
                if frame.shape[2] == 4:
                    frame[:, :, 3] = (frame[:, :, 3] * alpha).astype(np.uint8)

            return frame

        sub_clip = sub_clip.transform(outro_animation)

        return CompositeVideoClip([bg_clip, sub_clip], size=resolution)

    # =========================================================================
    # AUDIO MIXING WITH DUCKING
    # =========================================================================

    def _build_audio_mix(
        self,
        voiceover: AudioFileClip,
        music_path: str | None,
        intro_duration: float,
        outro_duration: float,
        main_duration: float,
    ) -> AudioClip:
        """Build final audio: silence for intro + voiceover + music with ducking."""
        total = intro_duration + main_duration + outro_duration

        # Intro silence
        silence_intro = AudioClip(lambda t: [0, 0], duration=intro_duration, fps=44100)
        # Outro silence
        silence_outro = AudioClip(lambda t: [0, 0], duration=outro_duration, fps=44100)

        # Base voiceover with padding
        full_vo = concatenate_audioclips([silence_intro, voiceover, silence_outro])

        if not music_path or not Path(music_path).exists():
            return full_vo

        # Mix with background music using pydub for proper ducking
        try:
            return self._mix_with_ducking(full_vo, music_path, total)
        except Exception as e:
            logger.warning(f"Music mixing failed, using voiceover only: {e}")
            return full_vo

    def _mix_with_ducking(
        self, voiceover_clip: AudioClip, music_path: str, total_duration: float
    ) -> AudioClip:
        """Mix voiceover with background music, ducking music during speech."""
        # Export voiceover to temp file for pydub processing
        temp_vo = settings.temp_dir / "temp_vo_mix.wav"
        voiceover_clip.write_audiofile(str(temp_vo), fps=44100, logger=None)

        vo_audio = AudioSegment.from_file(str(temp_vo))
        music = AudioSegment.from_file(music_path)

        # Loop music to match duration
        target_ms = int(total_duration * 1000)
        if len(music) < target_ms:
            loops = (target_ms // len(music)) + 1
            music = music * loops
        music = music[:target_ms]

        # Fade in/out on music
        music = music.fade_in(2000).fade_out(3000)

        # Voice activity detection via RMS energy
        chunk_ms = 100  # 100ms chunks
        ducked_music = AudioSegment.empty()
        rms_threshold = vo_audio.rms * 0.3  # 30% of voice RMS = silence threshold

        for i in range(0, len(music), chunk_ms):
            music_chunk = music[i:i + chunk_ms]
            vo_chunk = vo_audio[i:i + chunk_ms] if i < len(vo_audio) else AudioSegment.silent(chunk_ms)

            if vo_chunk.rms > rms_threshold:
                # Voice present → duck music heavily
                ducked_music += music_chunk + MUSIC_DUCK_DB
            else:
                # Silence → music at bed level
                ducked_music += music_chunk + MUSIC_BED_DB

        # Mix
        mixed = vo_audio.overlay(ducked_music)

        # Export mixed audio
        temp_mixed = settings.temp_dir / "temp_mixed.wav"
        mixed.export(str(temp_mixed), format="wav")

        # Load back as MoviePy AudioClip
        result = AudioFileClip(str(temp_mixed))

        # Cleanup temp files
        temp_vo.unlink(missing_ok=True)
        temp_mixed.unlink(missing_ok=True)

        return result

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _create_gradient(
        self, color1: tuple, color2: tuple, w: int, h: int
    ) -> Image.Image:
        """Create a vertical gradient background."""
        img = Image.new("RGB", (w, h))
        pixels = img.load()
        for y in range(h):
            ratio = y / h
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            for x in range(w):
                pixels[x, y] = (r, g, b)
        return img

    def _find_font(self) -> str | None:
        """Find a bold font on the system."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSMono.ttf",
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
