"""Video Assembler Service — assembles final videos using MoviePy 2.x and FFmpeg."""

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
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.services.caption_generator import SubtitleEntry
from app.utils.file_manager import get_unique_path


@dataclass
class VideoComponents:
    voiceover_path: str
    asset_paths: list[str]
    asset_types: list[str]  # "stock_video" or "stock_image" or "ai_image"
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


class VideoAssembler:
    def __init__(self):
        self.default_resolution = (1920, 1080)
        self.fps = settings.DEFAULT_FPS
        self._font_path = self._find_font()

    def assemble_video(self, components: VideoComponents) -> AssembledVideo:
        """Assemble a full video from all components."""
        resolution = components.resolution
        logger.info(f"Assembling video: {len(components.asset_paths)} assets, "
                     f"{resolution[0]}x{resolution[1]}")

        # 1. Load voiceover — determines total duration
        voiceover = AudioFileClip(components.voiceover_path)
        total_duration = voiceover.duration
        logger.info(f"Voiceover duration: {total_duration:.1f}s")

        # 2. Build visual track from assets
        visual_clip = self._build_visual_track(
            components.asset_paths,
            components.asset_types,
            total_duration,
            resolution,
        )

        # 3. Create animated captions overlay
        caption_clip = None
        if components.subtitle_entries:
            caption_clip = self._create_caption_overlay(
                components.subtitle_entries,
                total_duration,
                resolution,
                style=components.caption_style,
            )

        # 4. Create intro (3s)
        intro_clip = self._create_intro(components.channel_name, resolution)

        # 5. Create outro (5s)
        outro_clip = self._create_outro(components.channel_name, resolution)

        # 6. Composite everything
        layers = [visual_clip]
        if caption_clip:
            layers.append(caption_clip)

        main_video = CompositeVideoClip(layers, size=resolution)
        main_video = main_video.with_duration(total_duration)

        # Add intro and outro
        final_video = concatenate_videoclips(
            [intro_clip, main_video, outro_clip],
            method="compose",
        )

        # 7. Set audio
        final_video = final_video.with_audio(voiceover)

        # If intro/outro added time, we need to offset audio
        intro_dur = intro_clip.duration
        if intro_dur > 0:
            # Pad audio start with silence for intro
            from moviepy import AudioClip
            silence = AudioClip(lambda t: [0, 0], duration=intro_dur, fps=44100)
            outro_silence = AudioClip(lambda t: [0, 0], duration=outro_clip.duration, fps=44100)
            from moviepy import concatenate_audioclips
            full_audio = concatenate_audioclips([silence, voiceover, outro_silence])
            final_video = final_video.with_audio(full_audio)

        # 8. Export
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

        # Cleanup
        voiceover.close()
        final_video.close()

        duration = final_video.duration
        logger.info(f"Video assembled: {output_path} ({duration:.1f}s)")

        return AssembledVideo(
            video_path=str(output_path),
            duration_seconds=duration,
            resolution=resolution,
        )

    def _build_visual_track(
        self,
        asset_paths: list[str],
        asset_types: list[str],
        total_duration: float,
        resolution: tuple[int, int],
    ) -> VideoFileClip | CompositeVideoClip:
        """Build the visual track from stock videos and images."""
        if not asset_paths:
            # Solid color background as fallback
            return ColorClip(size=resolution, color=(15, 15, 25)).with_duration(total_duration)

        clips = []
        segment_duration = total_duration / len(asset_paths)

        for path, atype in zip(asset_paths, asset_types):
            path = Path(path)
            if not path.exists():
                logger.warning(f"Asset not found: {path}, using black frame")
                clips.append(
                    ColorClip(size=resolution, color=(15, 15, 25))
                    .with_duration(segment_duration)
                )
                continue

            try:
                if atype == "stock_video":
                    clip = self._prepare_video_clip(str(path), segment_duration, resolution)
                else:  # stock_image or ai_image
                    clip = self._prepare_image_clip(str(path), segment_duration, resolution)
                clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to process asset {path}: {e}")
                clips.append(
                    ColorClip(size=resolution, color=(15, 15, 25))
                    .with_duration(segment_duration)
                )

        return concatenate_videoclips(clips, method="compose")

    def _prepare_video_clip(
        self, path: str, target_duration: float, resolution: tuple[int, int]
    ) -> VideoFileClip:
        """Load, resize, and trim/loop a video clip to target duration."""
        clip = VideoFileClip(path)

        # Resize to target resolution (center crop to maintain aspect ratio)
        clip = self._resize_and_crop(clip, resolution)

        # Trim or loop to match target duration
        if clip.duration >= target_duration:
            clip = clip.subclipped(0, target_duration)
        else:
            # Loop the clip
            loops = int(target_duration / clip.duration) + 1
            clips = [clip] * loops
            clip = concatenate_videoclips(clips).subclipped(0, target_duration)

        return clip.without_audio()

    def _prepare_image_clip(
        self, path: str, duration: float, resolution: tuple[int, int]
    ) -> ImageClip:
        """Create an ImageClip with Ken Burns effect (slow zoom)."""
        # Load and resize image to be slightly larger for zoom effect
        img = Image.open(path).convert("RGB")
        # Make image 15% larger than target for zoom room
        zoom_w = int(resolution[0] * 1.15)
        zoom_h = int(resolution[1] * 1.15)
        img = img.resize((zoom_w, zoom_h), Image.LANCZOS)

        img_array = np.array(img)
        clip = ImageClip(img_array).with_duration(duration)

        # Ken Burns: zoom from 115% to 100% (slow zoom in effect)
        def ken_burns(get_frame, t):
            progress = t / duration
            # Zoom from 1.0 (showing 115% image = zoomed out) to 1.15 (cropped to 100%)
            scale = 1.0 + (0.15 * progress)
            frame = get_frame(t)

            h, w = frame.shape[:2]
            new_w = int(resolution[0] / scale * (w / resolution[0]))
            new_h = int(resolution[1] / scale * (h / resolution[1]))
            x = (w - new_w) // 2
            y = (h - new_h) // 2

            cropped = frame[y:y + new_h, x:x + new_w]

            # Resize to target resolution
            from PIL import Image as PILImg
            pil_img = PILImg.fromarray(cropped)
            pil_img = pil_img.resize(resolution, PILImg.LANCZOS)
            return np.array(pil_img)

        clip = clip.transform(ken_burns)
        return clip

    def _resize_and_crop(self, clip, resolution: tuple[int, int]):
        """Resize video clip to resolution with center crop."""
        target_w, target_h = resolution
        target_ratio = target_w / target_h
        clip_ratio = clip.w / clip.h

        if clip_ratio > target_ratio:
            # Clip is wider — resize by height, crop width
            new_h = target_h
            new_w = int(clip.w * (target_h / clip.h))
        else:
            # Clip is taller — resize by width, crop height
            new_w = target_w
            new_h = int(clip.h * (target_w / clip.w))

        clip = clip.resized((new_w, new_h))

        # Center crop
        x = (new_w - target_w) // 2
        y = (new_h - target_h) // 2
        clip = clip.cropped(x1=x, y1=y, x2=x + target_w, y2=y + target_h)

        return clip

    def _create_caption_overlay(
        self,
        entries: list[SubtitleEntry],
        total_duration: float,
        resolution: tuple[int, int],
        style: str = "hormozi",
    ) -> CompositeVideoClip:
        """Create animated caption overlay from subtitle entries."""
        clips = []
        w, h = resolution

        for entry in entries:
            if not entry.text or entry.text == "...":
                continue

            duration = entry.end_time - entry.start_time
            if duration <= 0:
                continue

            # Create caption image with Pillow
            caption_img = self._render_caption_frame(
                entry.text, w, style=style
            )

            img_clip = (
                ImageClip(np.array(caption_img))
                .with_duration(duration)
                .with_start(entry.start_time)
                .with_position(("center", h - 200))
            )
            clips.append(img_clip)

        if not clips:
            return CompositeVideoClip(
                [ColorClip(size=resolution, color=(0, 0, 0, 0)).with_duration(total_duration)],
                size=resolution,
            )

        # Create a transparent base
        base = ColorClip(size=resolution, color=(0, 0, 0)).with_duration(total_duration)
        base = base.with_opacity(0)

        return CompositeVideoClip([base] + clips, size=resolution)

    def _render_caption_frame(
        self, text: str, video_width: int, style: str = "hormozi"
    ) -> Image.Image:
        """Render a single caption frame using Pillow."""
        max_width = int(video_width * 0.8)
        font_size = 72 if style == "hormozi" else 48
        font = self._get_font(font_size)

        # Word wrap
        words = text.split()
        lines = []
        current_line = ""
        img_tmp = Image.new("RGBA", (max_width, 500), (0, 0, 0, 0))
        draw_tmp = ImageDraw.Draw(img_tmp)

        for word in words:
            test = f"{current_line} {word}".strip()
            bbox = draw_tmp.textbbox((0, 0), test, font=font)
            if bbox[2] > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        # Calculate image height
        line_height = draw_tmp.textbbox((0, 0), "Ay", font=font)[3] + 10
        img_height = line_height * len(lines) + 40

        # Create caption image
        img = Image.new("RGBA", (max_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        y = 20
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (max_width - bbox[2]) // 2

            # Draw text stroke/outline
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))

            # Draw main text
            if style == "hormozi":
                draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            else:
                draw.text((x, y), line, font=font, fill=(255, 255, 255, 230))

            y += line_height

        return img

    def _create_intro(
        self, channel_name: str, resolution: tuple[int, int], duration: float = 3.0
    ) -> CompositeVideoClip:
        """Create a simple intro clip."""
        w, h = resolution
        bg = ColorClip(size=resolution, color=(15, 15, 30)).with_duration(duration)

        # Render channel name with Pillow
        font = self._get_font(96)
        img = Image.new("RGBA", resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), channel_name, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (w - text_w) // 2
        y = (h - text_h) // 2

        # Stroke
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                draw.text((x + dx, y + dy), channel_name, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), channel_name, font=font, fill=(255, 215, 0, 255))

        text_clip = ImageClip(np.array(img)).with_duration(duration)

        return CompositeVideoClip([bg, text_clip], size=resolution)

    def _create_outro(
        self, channel_name: str, resolution: tuple[int, int], duration: float = 5.0
    ) -> CompositeVideoClip:
        """Create a simple outro clip with subscribe CTA."""
        w, h = resolution
        bg = ColorClip(size=resolution, color=(15, 15, 30)).with_duration(duration)

        img = Image.new("RGBA", resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # "Subscribe" text
        font_large = self._get_font(80)
        font_small = self._get_font(48)

        sub_text = "SUBSCRIBE"
        bbox = draw.textbbox((0, 0), sub_text, font=font_large)
        x = (w - (bbox[2] - bbox[0])) // 2
        y = h // 2 - 80
        draw.text((x, y), sub_text, font=font_large, fill=(255, 0, 0, 255))

        # Channel name
        bbox2 = draw.textbbox((0, 0), channel_name, font=font_small)
        x2 = (w - (bbox2[2] - bbox2[0])) // 2
        draw.text((x2, y + 100), channel_name, font=font_small, fill=(255, 255, 255, 200))

        text_clip = ImageClip(np.array(img)).with_duration(duration)

        return CompositeVideoClip([bg, text_clip], size=resolution)

    def _find_font(self) -> str | None:
        """Find a suitable font file on the system."""
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
        """Get a font at the specified size."""
        if self._font_path:
            try:
                return ImageFont.truetype(self._font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()
