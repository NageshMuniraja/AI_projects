"""Thumbnail Generator Service — creates click-worthy thumbnails with CTR optimization."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from app.config import settings
from app.utils.file_manager import get_unique_path


# Niche-specific accent colors (color psychology for CTR)
NICHE_COLORS = {
    "tech": {"accent": "#00D4FF", "bg": ["#0a0a2e", "#001a3a"]},       # electric blue
    "ai": {"accent": "#00D4FF", "bg": ["#0a0a2e", "#001a3a"]},
    "finance": {"accent": "#00FF88", "bg": ["#0a1a0a", "#002a10"]},     # money green
    "motivation": {"accent": "#FFD700", "bg": ["#1a1000", "#2a1a00"]},  # gold
    "history": {"accent": "#D4A574", "bg": ["#1a1008", "#2a1a10"]},     # aged bronze
    "health": {"accent": "#4ADE80", "bg": ["#0a1a10", "#002818"]},      # vital green
    "science": {"accent": "#A855F7", "bg": ["#1a0a2e", "#0a0020"]},     # purple
    "gaming": {"accent": "#FF4444", "bg": ["#1a0000", "#2a0a0a"]},      # red
    "psychology": {"accent": "#818CF8", "bg": ["#0a0a20", "#10102a"]},   # indigo
    "luxury": {"accent": "#FFD700", "bg": ["#0a0a0a", "#1a1a1a"]},      # gold on black
    "scary": {"accent": "#FF1744", "bg": ["#0a0000", "#1a0000"]},       # blood red
    "horror": {"accent": "#FF1744", "bg": ["#0a0000", "#1a0000"]},
    "space": {"accent": "#60A5FA", "bg": ["#000010", "#000830"]},       # cosmic blue
}


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
        niche: str = "general",
        variants: int = 3,
    ) -> ThumbnailResult:
        """Generate thumbnail variants with CTR-optimized design."""
        output_dir = settings.thumbnails_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get niche-specific colors
        niche_config = self._get_niche_colors(niche)

        # Shorten title for thumbnail
        short_title = self._shorten_title(title)

        paths = []
        styles = ["bold", "minimal", "shocking"]

        for i in range(min(variants, len(styles))):
            variant_style = styles[i]
            variant_config = self._load_template(variant_style)
            variant_config["niche"] = niche_config
            output_path = get_unique_path(output_dir, f"thumb_{variant_style}", ".jpg")

            img = self._render_thumbnail(
                short_title,
                variant_config,
                background_image_path,
                niche_config,
            )
            img.save(str(output_path), "JPEG", quality=95)
            paths.append(str(output_path))
            logger.debug(f"Thumbnail variant {i + 1}: {output_path}")

        primary = paths[0] if paths else ""
        logger.info(f"Generated {len(paths)} thumbnail variants ({niche})")

        return ThumbnailResult(paths=paths, primary_path=primary, style=style)

    def _render_thumbnail(
        self,
        title: str,
        config: dict,
        background_image_path: str | None,
        niche_config: dict,
    ) -> Image.Image:
        """Render a single thumbnail image with CTR-optimized design."""
        w, h = self.CANVAS_SIZE

        # Create background
        if background_image_path and Path(background_image_path).exists():
            img = Image.open(background_image_path).convert("RGB")
            img = self._crop_to_aspect(img, w, h)
            img = img.resize((w, h), Image.LANCZOS)
            # Boost saturation by 20% for more vivid thumbnails
            img = self._boost_saturation(img, 1.20)
        else:
            bg_colors = niche_config.get("bg", ["#1a1a2e", "#16213e"])
            img = self._create_gradient_background_colors(bg_colors, w, h)

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

        # Check if title has a number for listicle treatment
        number = self._extract_leading_number(title)

        if number:
            img = self._draw_number_circle(img, number, niche_config)
            draw = ImageDraw.Draw(img)
            title = self._remove_leading_number(title)

        # Render text with dynamic sizing
        text_cfg = config.get("text", {})
        accent_color = niche_config.get("accent", "#FFD700")
        self._draw_text_dynamic(draw, title, text_cfg, w, h, accent_color)

        return img

    def _draw_text_dynamic(
        self, draw: ImageDraw.ImageDraw, text: str, config: dict,
        w: int, h: int, accent_color: str,
    ) -> None:
        """Draw text with dynamic sizing based on word count."""
        words = text.upper().split()
        word_count = len(words)

        # Dynamic font sizing — fewer words = bigger text
        if word_count <= 2:
            font_size = 140
        elif word_count <= 4:
            font_size = 110
        else:
            font_size = 90

        color = self._hex_to_rgb(config.get("color", "#FFFFFF"))
        stroke_color = self._hex_to_rgb(config.get("stroke_color", "#000000"))
        stroke_width = config.get("stroke_width", 5)

        font = self._get_font(font_size)

        # Word wrap
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
        start_y = (h - total_height) // 2

        # Shadow settings
        shadow_cfg = config.get("shadow", {})
        sx, sy = 4, 4
        shadow_color = (0, 0, 0)
        if shadow_cfg:
            sx, sy = shadow_cfg.get("offset", [4, 4])
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
            draw.text((x + sx, y + sy), line, font=font, fill=shadow_color)

            # Main text with stroke — use accent color for first line
            line_color = self._hex_to_rgb(accent_color) if i == 0 else color
            draw.text(
                (x, y), line, font=font, fill=line_color,
                stroke_width=stroke_width, stroke_fill=stroke_color,
            )

    def _draw_number_circle(
        self, img: Image.Image, number: str, niche_config: dict
    ) -> Image.Image:
        """Draw a large number in a colored circle (listicle thumbnail style)."""
        circle_size = 180
        margin = 40

        circle = Image.new("RGBA", (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle)

        accent = self._hex_to_rgb(niche_config.get("accent", "#FF0000"))
        circle_draw.ellipse(
            [0, 0, circle_size - 1, circle_size - 1],
            fill=(*accent, 230),
            outline=(255, 255, 255, 255),
            width=4,
        )

        num_font = self._get_font(100)
        bbox = circle_draw.textbbox((0, 0), number, font=num_font)
        num_w = bbox[2] - bbox[0]
        num_h = bbox[3] - bbox[1]
        num_x = (circle_size - num_w) // 2
        num_y = (circle_size - num_h) // 2 - 10

        circle_draw.text(
            (num_x, num_y), number, font=num_font,
            fill=(255, 255, 255, 255),
            stroke_width=3, stroke_fill=(0, 0, 0, 255),
        )

        img_rgba = img.convert("RGBA")
        img_rgba.paste(circle, (margin, margin), circle)
        return img_rgba.convert("RGB")

    @staticmethod
    def _boost_saturation(img: Image.Image, factor: float) -> Image.Image:
        """Boost image saturation for more vivid thumbnails."""
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)

    def _create_gradient_background_colors(
        self, colors: list[str], w: int, h: int
    ) -> Image.Image:
        """Create a gradient background from color list."""
        color1 = self._hex_to_rgb(colors[0])
        color2 = self._hex_to_rgb(colors[1]) if len(colors) > 1 else color1

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

    def _create_gradient_background(
        self, config: dict, w: int, h: int
    ) -> Image.Image:
        """Create a gradient background from config."""
        bg_cfg = config.get("background", {})
        colors = bg_cfg.get("colors", ["#1a1a2e", "#16213e"])
        return self._create_gradient_background_colors(colors, w, h)

    def _apply_overlay(self, img: Image.Image, config: dict) -> Image.Image:
        """Apply a colored overlay to the image."""
        color = self._hex_to_rgb(config.get("color", "#000000"))
        opacity = int(config.get("opacity", 0.3) * 255)
        overlay_type = config.get("type", "full")

        overlay = Image.new("RGBA", img.size, (*color, opacity))

        if overlay_type == "strip":
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

        for i in range(50):
            ratio = i / 50
            brightness = int(255 * ratio)
            margin_x = int(w * (1 - ratio) / 2)
            margin_y = int(h * (1 - ratio) / 2)
            draw.ellipse(
                [margin_x, margin_y, w - margin_x, h - margin_y],
                fill=brightness,
            )

        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=50))

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

        return {
            "background": {"colors": ["#1a1a2e", "#16213e"]},
            "text": {
                "font_size": 100,
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 5,
                "position": "center",
                "shadow": {"offset": [4, 4], "color": "#000000"},
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

    def _get_niche_colors(self, niche: str) -> dict:
        """Get niche-specific color configuration."""
        niche_lower = niche.lower()
        for key, config in NICHE_COLORS.items():
            if key in niche_lower:
                return config
        return {"accent": "#FFD700", "bg": ["#1a1a2e", "#16213e"]}

    @staticmethod
    def _extract_leading_number(title: str) -> str | None:
        """Extract a leading number from title (e.g., '7 Reasons...' -> '7')."""
        match = re.match(r"^(\d+)\s", title)
        return match.group(1) if match else None

    @staticmethod
    def _remove_leading_number(title: str) -> str:
        """Remove leading number from title."""
        return re.sub(r"^\d+\s+", "", title)

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
