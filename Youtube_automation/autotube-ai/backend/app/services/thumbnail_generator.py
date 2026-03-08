"""Thumbnail Generator Service — creates click-worthy thumbnails with AI backgrounds and CTR optimization.

Features:
- DALL-E 3 AI-generated cinematic background images (no more plain gradients)
- Niche-specific color schemes (color psychology for CTR)
- Dynamic text sizing with glow effects and gradient fills
- Number circles for listicle thumbnails
- Vignette, saturation boost, bottom darkening for text contrast
- Multiple A/B variants per thumbnail
"""

import base64
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from app.config import settings
from app.utils.file_manager import get_unique_path


# Niche-specific accent colors (color psychology for CTR)
NICHE_COLORS = {
    "tech": {"accent": "#00D4FF", "bg": ["#0a0a2e", "#001a3a"], "glow": "#00A8FF"},
    "ai": {"accent": "#00D4FF", "bg": ["#0a0a2e", "#001a3a"], "glow": "#00A8FF"},
    "finance": {"accent": "#00FF88", "bg": ["#0a1a0a", "#002a10"], "glow": "#00CC66"},
    "motivation": {"accent": "#FFD700", "bg": ["#1a1000", "#2a1a00"], "glow": "#FFAA00"},
    "history": {"accent": "#D4A574", "bg": ["#1a1008", "#2a1a10"], "glow": "#C48850"},
    "health": {"accent": "#4ADE80", "bg": ["#0a1a10", "#002818"], "glow": "#30B060"},
    "science": {"accent": "#A855F7", "bg": ["#1a0a2e", "#0a0020"], "glow": "#8030D0"},
    "gaming": {"accent": "#FF4444", "bg": ["#1a0000", "#2a0a0a"], "glow": "#FF2020"},
    "psychology": {"accent": "#818CF8", "bg": ["#0a0a20", "#10102a"], "glow": "#6060E0"},
    "luxury": {"accent": "#FFD700", "bg": ["#0a0a0a", "#1a1a1a"], "glow": "#FFAA00"},
    "scary": {"accent": "#FF1744", "bg": ["#0a0000", "#1a0000"], "glow": "#CC0030"},
    "horror": {"accent": "#FF1744", "bg": ["#0a0000", "#1a0000"], "glow": "#CC0030"},
    "space": {"accent": "#60A5FA", "bg": ["#000010", "#000830"], "glow": "#4080E0"},
    "kids": {"accent": "#FFD700", "bg": ["#1a0050", "#000080"], "glow": "#FF8800"},
}

# DALL-E 3 background prompts per niche
THUMBNAIL_BG_PROMPTS = {
    "tech": "futuristic technology background, glowing circuits, neon blue lights, dark dramatic atmosphere, abstract digital landscape, 8K",
    "ai": "artificial intelligence neural network visualization, glowing nodes and connections, deep blue and cyan, futuristic, 8K",
    "finance": "dramatic stock market visualization, golden coins, upward charts, dark green atmosphere with golden highlights, 8K",
    "motivation": "dramatic sunset over mountain peak, golden light rays, epic landscape, inspiring atmosphere, 8K",
    "history": "ancient dramatic scene, aged textures, warm bronze tones, cinematic historical atmosphere, 8K",
    "health": "vibrant natural wellness scene, fresh greens, clean bright atmosphere, energetic, 8K",
    "science": "dramatic scientific visualization, molecular structures, glowing purple and blue, laboratory atmosphere, 8K",
    "gaming": "epic gaming scene, dramatic red and dark lighting, action-packed atmosphere, cinematic, 8K",
    "psychology": "abstract mind visualization, deep indigo and purple, neural pathways, mysterious atmosphere, 8K",
    "luxury": "opulent dark scene, gold accents on black, dramatic lighting, premium feel, 8K",
    "scary": "eerie dark atmospheric scene, deep shadows, subtle red accents, horror movie aesthetic, 8K",
    "horror": "terrifying dark scene, blood red accents on black, fog and shadows, cinematic horror, 8K",
    "space": "deep space nebula, stars, cosmic blue and purple, dramatic galaxy view, 8K",
    "kids": "bright colorful magical world, sparkles and rainbows, cartoon-style landscape, cheerful and fun, 8K",
}


@dataclass
class ThumbnailResult:
    paths: list[str]  # Multiple A/B variants
    primary_path: str
    style: str
    cost_usd: float = 0.0


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
        """Generate thumbnail variants with AI backgrounds and CTR-optimized design."""
        output_dir = settings.thumbnails_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        niche_config = self._get_niche_colors(niche)
        short_title = self._shorten_title(title)
        total_cost = 0.0

        # Generate AI background if no image provided
        ai_bg_path = background_image_path
        if not ai_bg_path:
            ai_bg_path, bg_cost = self._generate_ai_background(title, niche)
            total_cost += bg_cost

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
                ai_bg_path,
                niche_config,
                variant_style,
            )
            img.save(str(output_path), "JPEG", quality=95)
            paths.append(str(output_path))
            logger.debug(f"Thumbnail variant {i + 1}: {output_path}")

        primary = paths[0] if paths else ""
        logger.info(f"Generated {len(paths)} thumbnail variants ({niche}), cost=${total_cost:.4f}")

        return ThumbnailResult(
            paths=paths, primary_path=primary, style=style, cost_usd=total_cost
        )

    # =========================================================================
    # AI BACKGROUND GENERATION
    # =========================================================================

    def _generate_ai_background(
        self, title: str, niche: str
    ) -> tuple[str | None, float]:
        """Generate a DALL-E 3 cinematic background for the thumbnail."""
        try:
            import openai

            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            niche_lower = niche.lower()
            base_prompt = THUMBNAIL_BG_PROMPTS.get(niche_lower, "")
            if not base_prompt:
                for key, prompt in THUMBNAIL_BG_PROMPTS.items():
                    if key in niche_lower:
                        base_prompt = prompt
                        break

            if not base_prompt:
                base_prompt = "dramatic cinematic background, dark atmospheric, professional, 8K"

            prompt = (
                f"{base_prompt}. "
                f"Context: YouTube thumbnail background for '{title}'. "
                "Wide shot composition, blurred background suitable for text overlay, "
                "dramatic lighting, high contrast, no text, no watermarks, no logos, "
                "no people faces, leave center-right area clear for text"
            )

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="hd",
                n=1,
                response_format="b64_json",
            )

            image_data = base64.b64decode(response.data[0].b64_json)
            output_dir = settings.thumbnails_dir / "backgrounds"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = get_unique_path(output_dir, "ai_bg", ".png")
            output_path.write_bytes(image_data)

            logger.info(f"AI thumbnail background: {output_path}")
            return str(output_path), 0.080

        except Exception as e:
            logger.warning(f"AI background generation failed: {e}")
            return None, 0.0

    # =========================================================================
    # THUMBNAIL RENDERING
    # =========================================================================

    def _render_thumbnail(
        self,
        title: str,
        config: dict,
        background_image_path: str | None,
        niche_config: dict,
        variant_style: str = "bold",
    ) -> Image.Image:
        """Render a single thumbnail image with AI background and CTR-optimized design."""
        w, h = self.CANVAS_SIZE

        # Create background
        if background_image_path and Path(background_image_path).exists():
            img = Image.open(background_image_path).convert("RGB")
            img = self._crop_to_aspect(img, w, h)
            img = img.resize((w, h), Image.LANCZOS)
            img = self._boost_saturation(img, 1.25)
            img = self._boost_contrast(img, 1.15)
        else:
            bg_colors = niche_config.get("bg", ["#1a1a2e", "#16213e"])
            img = self._create_gradient_background_colors(bg_colors, w, h)

        draw = ImageDraw.Draw(img)

        # Apply bottom darkening gradient for text contrast
        img = self._apply_bottom_gradient(img, intensity=0.6)

        # Apply vignette
        img = self._apply_vignette(img)
        draw = ImageDraw.Draw(img)

        # Check if title has a number for listicle treatment
        number = self._extract_leading_number(title)

        if number:
            img = self._draw_number_circle(img, number, niche_config)
            draw = ImageDraw.Draw(img)
            title = self._remove_leading_number(title)

        # Render text with glow and dynamic sizing
        accent_color = niche_config.get("accent", "#FFD700")
        glow_color = niche_config.get("glow", accent_color)
        text_cfg = config.get("text", {})
        self._draw_text_with_glow(
            img, draw, title, text_cfg, w, h, accent_color, glow_color, variant_style
        )

        return img

    def _draw_text_with_glow(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        text: str,
        config: dict,
        w: int,
        h: int,
        accent_color: str,
        glow_color: str,
        variant_style: str,
    ) -> None:
        """Draw text with outer glow effect and dynamic sizing."""
        words = text.upper().split()
        word_count = len(words)

        # Dynamic font sizing
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

        line_height = draw.textbbox((0, 0), "Ay", font=font)[3] + 15
        total_height = line_height * len(lines)

        # Position text in lower third for thumbnail best practices
        if variant_style == "minimal":
            start_y = (h - total_height) // 2
        else:
            start_y = h - total_height - int(h * 0.12)

        # Create glow layer
        glow_rgb = self._hex_to_rgb(glow_color)
        glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (w - text_w) // 2
            y = start_y + i * line_height

            # Draw glow text (will be blurred)
            glow_draw.text(
                (x, y), line, font=font,
                fill=(*glow_rgb, 180),
            )

        # Blur the glow layer
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=12))

        # Composite glow onto main image
        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, glow_layer)
        img.paste(img_rgba.convert("RGB"))
        draw = ImageDraw.Draw(img)

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
            x = (w - text_w) // 2
            y = start_y + i * line_height

            # Shadow
            draw.text((x + sx, y + sy), line, font=font, fill=shadow_color)

            # Main text with stroke — accent color for first line
            line_color = self._hex_to_rgb(accent_color) if i == 0 else color
            draw.text(
                (x, y), line, font=font, fill=line_color,
                stroke_width=stroke_width, stroke_fill=stroke_color,
            )

    def _apply_bottom_gradient(
        self, img: Image.Image, intensity: float = 0.5
    ) -> Image.Image:
        """Apply bottom-to-top darkening gradient for text contrast."""
        w, h = img.size
        gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # Dark gradient from bottom 40% of image
        gradient_start = int(h * 0.6)
        for y in range(gradient_start, h):
            progress = (y - gradient_start) / (h - gradient_start)
            alpha = int(255 * progress * intensity)
            draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

        img_rgba = img.convert("RGBA")
        composited = Image.alpha_composite(img_rgba, gradient)
        return composited.convert("RGB")

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
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)

    @staticmethod
    def _boost_contrast(img: Image.Image, factor: float) -> Image.Image:
        enhancer = ImageEnhance.Contrast(img)
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
        bg_cfg = config.get("background", {})
        colors = bg_cfg.get("colors", ["#1a1a2e", "#16213e"])
        return self._create_gradient_background_colors(colors, w, h)

    def _apply_overlay(self, img: Image.Image, config: dict) -> Image.Image:
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
        words = title.split()
        if len(words) <= max_words:
            return title
        return " ".join(words[:max_words])

    def _crop_to_aspect(
        self, img: Image.Image, target_w: int, target_h: int
    ) -> Image.Image:
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
        niche_lower = niche.lower()
        for key, config in NICHE_COLORS.items():
            if key in niche_lower:
                return config
        return {"accent": "#FFD700", "bg": ["#1a1a2e", "#16213e"], "glow": "#FFAA00"}

    @staticmethod
    def _extract_leading_number(title: str) -> str | None:
        match = re.match(r"^(\d+)\s", title)
        return match.group(1) if match else None

    @staticmethod
    def _remove_leading_number(title: str) -> str:
        return re.sub(r"^\d+\s+", "", title)

    def _find_font(self) -> str | None:
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
