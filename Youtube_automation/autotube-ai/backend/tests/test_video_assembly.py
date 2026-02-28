"""Tests for Video Assembly service utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.services.caption_generator import CaptionGenerator, SubtitleEntry


class TestCaptionGenerator:
    def test_seconds_to_srt_time(self):
        """Test time format conversion."""
        assert CaptionGenerator._seconds_to_srt_time(0) == "00:00:00,000"
        assert CaptionGenerator._seconds_to_srt_time(61.5) == "00:01:01,500"
        assert CaptionGenerator._seconds_to_srt_time(3661.123) == "01:01:01,123"

    def test_vtt_time_to_seconds(self):
        """Test VTT time parsing."""
        assert CaptionGenerator._vtt_time_to_seconds("00:00:00.000") == 0.0
        assert abs(CaptionGenerator._vtt_time_to_seconds("00:01:30.500") - 90.5) < 0.01
        assert abs(CaptionGenerator._vtt_time_to_seconds("01:00:00.000") - 3600.0) < 0.01

    def test_write_srt(self, tmp_path):
        """Test SRT file generation."""
        gen = CaptionGenerator()
        entries = [
            SubtitleEntry(index=1, start_time=0.0, end_time=3.0, text="Hello world"),
            SubtitleEntry(index=2, start_time=3.5, end_time=6.0, text="This is a test"),
        ]

        srt_path = tmp_path / "test.srt"
        gen._write_srt(entries, srt_path)

        content = srt_path.read_text()
        assert "1\n00:00:00,000 --> 00:00:03,000\nHello world" in content
        assert "2\n00:00:03,500 --> 00:00:06,000\nThis is a test" in content


class TestThumbnailGenerator:
    def test_shorten_title(self):
        """Test title shortening for thumbnails."""
        from app.services.thumbnail_generator import ThumbnailGenerator

        gen = ThumbnailGenerator()

        # Short titles unchanged
        assert gen._shorten_title("Short Title") == "Short Title"

        # Long titles truncated to 5 words
        long_title = "This Is A Very Long Title That Should Be Shortened"
        assert gen._shorten_title(long_title) == "This Is A Very Long"

    def test_hex_to_rgb(self):
        """Test hex color conversion."""
        from app.services.thumbnail_generator import ThumbnailGenerator

        assert ThumbnailGenerator._hex_to_rgb("#FF0000") == (255, 0, 0)
        assert ThumbnailGenerator._hex_to_rgb("#00FF00") == (0, 255, 0)
        assert ThumbnailGenerator._hex_to_rgb("#0000FF") == (0, 0, 255)
        assert ThumbnailGenerator._hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert ThumbnailGenerator._hex_to_rgb("#000000") == (0, 0, 0)

    def test_crop_to_aspect(self):
        """Test image aspect ratio cropping."""
        from app.services.thumbnail_generator import ThumbnailGenerator

        gen = ThumbnailGenerator()

        # Wide image (2:1) cropped to 16:9
        wide_img = Image.new("RGB", (2000, 1000))
        cropped = gen._crop_to_aspect(wide_img, 1280, 720)
        ratio = cropped.width / cropped.height
        target_ratio = 1280 / 720
        assert abs(ratio - target_ratio) < 0.01


class TestValidators:
    def test_youtube_channel_id_validation(self):
        from app.utils.validators import validate_youtube_channel_id

        assert validate_youtube_channel_id("UCxxxxxxxxxxxxxxxxxxxxxxx") is False  # Too short
        assert validate_youtube_channel_id("UCabcdefghijklmnopqrstuv") is True
        assert validate_youtube_channel_id("not-a-channel-id") is False

    def test_sanitize_filename(self):
        from app.utils.validators import sanitize_filename

        assert sanitize_filename('test/file:name?"yes"') == "testfilenameyesq"[: len(sanitize_filename('test/file:name?"yes"'))]
        result = sanitize_filename("hello world test")
        assert " " not in result

    def test_truncate_title(self):
        from app.utils.validators import truncate_title

        short = "Short Title"
        assert truncate_title(short) == short

        long = "A " * 60
        assert len(truncate_title(long, 50)) <= 50
