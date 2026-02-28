"""Thumbnail Generator Service — creates click-worthy thumbnails using Pillow."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.config import settings
from app.utils.file_manager import get_unique_path


@dataclass
class ThumbnailResult:
    paths: list[str]  # Multiple A/B variants
    primary_path: str
    style: str


class ThumbnailGenerator:
    CANVAS_SIZE = (1280, 720)
    TEMPLATES_DIR = Path("/app/templates/thumbnails")

    def __init__(self):
        self._font_path = self._find_font()

    def generate_thumbnail(
        self,
        title: str,
        style: str = "bold",
        background_image_path: str | None = None,
        variants: int = 3,
    ) -> ThumbnailResult:
        """Generate thumbnail variants for a video."""
        output_dir = settings.thumbnails_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load template config
        config = self._load_template(style)

        # Shorten title for thumbnail (max 5-6 words)
        short_title = self._shorten_title(title)

        paths = []
        styles = ["bold", "minimal", "shocking"]

        for i in range(min(variants, len(styles))):
            variant_style = styles[i]
            variant_config = self._load_template(variant_style)
            output_path = get_unique_path(output_dir, f"thumb_{variant_style}", ".jpg")

            img = self._render_thumbnail(
                short_title,
                variant_config,
                background_image_path,
            )
            img.save(str(output_path), "JPEG", quality=95)
            paths.append(str(output_path))
            logger.debug(f"Thumbnail variant {i + 1}: {output_path}")

        primary = paths[0] if paths else ""
        logger.info(f"Generated {len(paths)} thumbnail variants")

        return ThumbnailResult(paths=paths, primary_path=primary, style=style)

    def _render_thumbnail(
        self,
        title: str,
        config: dict,
        background_image_path: str | None,
    ) -> Image.Image:
        """Render a single thumbnail image."""
        w, h = self.CANVAS_SIZE

        # Create background
        if background_image_path and Path(background_image_path).exists():
            img = Image.open(background_image_path).convert("RGB")
            img = self._crop_to_aspect(img, w, h)
            img = img.resize((w, h), Image.LANCZOS)
        else:
            img = self._create_gradient_background(config, w, h)

        draw = ImageDraw.Draw(img)

        # Apply overlay
        overlay_cfg = config.get("overlay", {})
        if overlay_cfg.get("enabled"):
            img = self._apply_overlay(img, overlay_cfg)
            draw = ImageDraw.Draw(img)

        # Apply vignette
        if config.get("effects", {}).get("vignette"):
            img = self._apply_vignette(img)
            draw = ImageDraw.Draw(img)

        # Render text
        text_cfg = config.get("text", {})
        self._draw_text(draw, title, text_cfg, w, h)

        return img

    def _create_gradient_background(
        self, config: dict, w: int, h: int
    ) -> Image.Image:
        """Create a gradient background."""
        bg_cfg = config.get("background", {})
        colors = bg_cfg.get("colors", ["#1a1a2e", "#16213e"])

        color1 = self._hex_to_rgb(colors[0])
        color2 = self._hex_to_rgb(colors[1])

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

    def _draw_text(
        self, draw: ImageDraw.ImageDraw, text: str, config: dict, w: int, h: int
    ) -> None:
        """Draw text with stroke and shadow on the thumbnail."""
        font_size = config.get("font_size", 100)
        color = self._hex_to_rgb(config.get("color", "#FFFFFF"))
        stroke_color = self._hex_to_rgb(config.get("stroke_color", "#000000"))
        stroke_width = config.get("stroke_width", 4)

        font = self._get_font(font_size)

        # Word wrap
        words = text.upper().split()
        lines = []
        current = ""
        max_w = int(w * 0.85)

        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] > max_w and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        # Calculate total text height
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3] + 15
        total_height = line_height * len(lines)

        # Position
        position = config.get("position", "center")
        if position == "center":
            start_y = (h - total_height) // 2
        elif position == "center-left":
            start_y = (h - total_height) // 2
        else:
            start_y = (h - total_height) // 2

        # Draw shadow
        shadow_cfg = config.get("shadow", {})
        if shadow_cfg:
            sx, sy = shadow_cfg.get("offset", [3, 3])
            shadow_color = self._hex_to_rgb(shadow_cfg.get("color", "#000000"))

        # Draw each line
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]

            if position == "center-left":
                x = int(w * 0.08)
            else:
                x = (w - text_w) // 2

            y = start_y + i * line_height

            # Shadow
            if shadow_cfg:
                draw.text((x + sx, y + sy), line, font=font, fill=shadow_color)

            # Stroke
            draw.text(
                (x, y), line, font=font, fill=color,
                stroke_width=stroke_width, stroke_fill=stroke_color,
            )

    def _apply_overlay(self, img: Image.Image, config: dict) -> Image.Image:
        """Apply a colored overlay to the image."""
        color = self._hex_to_rgb(config.get("color", "#000000"))
        opacity = int(config.get("opacity", 0.3) * 255)
        overlay_type = config.get("type", "full")

        overlay = Image.new("RGBA", img.size, (*color, opacity))

        if overlay_type == "strip":
            # Only bottom 30%
            strip = Image.new("RGBA", img.size, (0, 0, 0, 0))
            strip_overlay = Image.new(
                "RGBA", (img.width, int(img.height * 0.3)), (*color, opacity)
            )
            strip.paste(strip_overlay, (0, int(img.height * 0.7)))
            overlay = strip

        img_rgba = img.convert("RGBA")
        composited = Image.alpha_composite(img_rgba, overlay)
        return composited.convert("RGB")

    def _apply_vignette(self, img: Image.Image) -> Image.Image:
        """Apply a vignette effect (darken edges)."""
        w, h = img.size
        vignette = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(vignette)

        # Draw concentric ellipses getting lighter toward center
        for i in range(50):
            ratio = i / 50
            brightness = int(255 * ratio)
            margin_x = int(w * (1 - ratio) / 2)
            margin_y = int(h * (1 - ratio) / 2)
            draw.ellipse(
                [margin_x, margin_y, w - margin_x, h - margin_y],
                fill=brightness,
            )

        # Blur for smoothness
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=50))

        # Apply to image
        img_array = np.array(img, dtype=np.float32)
        vignette_array = np.array(vignette, dtype=np.float32) / 255.0
        vignette_array = np.expand_dims(vignette_array, axis=2)

        result = (img_array * vignette_array).astype(np.uint8)
        return Image.fromarray(result)

    def _load_template(self, style: str) -> dict:
        """Load a thumbnail template configuration."""
        template_path = self.TEMPLATES_DIR / f"style_{style}.json"
        if template_path.exists():
            with open(template_path) as f:
                return json.load(f)

        # Fallback defaults
        return {
            "background": {"colors": ["#1a1a2e", "#16213e"]},
            "text": {
                "font_size": 100,
                "color": "#FFD700",
                "stroke_color": "#000000",
                "stroke_width": 4,
                "position": "center",
                "shadow": {"offset": [3, 3], "color": "#000000"},
            },
            "overlay": {"enabled": False},
            "effects": {"vignette": True},
        }

    def _shorten_title(self, title: str, max_words: int = 5) -> str:
        """Shorten title for thumbnail (max 5-6 words)."""
        words = title.split()
        if len(words) <= max_words:
            return title
        return " ".join(words[:max_words])

    def _crop_to_aspect(
        self, img: Image.Image, target_w: int, target_h: int
    ) -> Image.Image:
        """Center-crop image to target aspect ratio."""
        target_ratio = target_w / target_h
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            offset = (img.width - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            offset = (img.height - new_h) // 2
            img = img.crop((0, offset, img.width, offset + new_h))

        return img

    def _find_font(self) -> str | None:
        """Find a bold font on the system."""
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for p in paths:
            if Path(p).exists():
                return p
        return None

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if self._font_path:
            try:
                return ImageFont.truetype(self._font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
