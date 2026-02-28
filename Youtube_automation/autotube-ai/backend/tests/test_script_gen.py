"""Tests for the Script Generator service."""

import re
from unittest.mock import MagicMock, patch

import pytest

# Test the utility methods that don't require API calls


class TestScriptGeneratorUtils:
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_script = """
**HOOK**
Did you know that 90% of AI startups fail within the first year?

[B-ROLL: futuristic city with AI robots]
[MUSIC: tension building]

**INTRO**
Today we're exploring the shocking truth about artificial intelligence.

[EMPHASIS]
This will change how you think about technology forever.

[B-ROLL: scientist working in lab]

**BODY - Point 1**
The first thing you need to understand is that AI is not what movies show you.

[B-ROLL: movie clips of robots]
[MUSIC: uplifting discovery]

**CTA**
If you found this valuable, smash that subscribe button!

**OUTRO**
Next week, we're diving into something even more mind-blowing.
"""

    def test_clean_script_for_tts(self):
        """Test that script markers are properly removed for TTS."""
        from app.services.script_generator import ScriptGenerator

        with patch("app.services.script_generator.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch("anthropic.Anthropic"):
                gen = ScriptGenerator()

        cleaned = gen.clean_script_for_tts(self.sample_script)

        # Should not contain markers
        assert "[B-ROLL:" not in cleaned
        assert "[MUSIC:" not in cleaned
        assert "[EMPHASIS]" not in cleaned
        assert "**" not in cleaned

        # Should still contain spoken text
        assert "90% of AI startups" in cleaned
        assert "subscribe button" in cleaned

    def test_extract_broll_markers(self):
        """Test B-ROLL marker extraction."""
        from app.services.script_generator import ScriptGenerator

        with patch("app.services.script_generator.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch("anthropic.Anthropic"):
                gen = ScriptGenerator()

        markers = gen._extract_broll_markers(self.sample_script)

        assert len(markers) >= 3
        assert markers[0]["description"] == "futuristic city with AI robots"
        assert markers[1]["description"] == "scientist working in lab"

        # Each marker should have a time position
        for marker in markers:
            assert "approximate_time" in marker
            assert isinstance(marker["approximate_time"], float)

    def test_extract_music_markers(self):
        """Test music marker extraction."""
        from app.services.script_generator import ScriptGenerator

        with patch("app.services.script_generator.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch("anthropic.Anthropic"):
                gen = ScriptGenerator()

        markers = gen._extract_music_markers(self.sample_script)

        assert len(markers) >= 2
        assert markers[0]["mood"] == "tension building"
        assert markers[1]["mood"] == "uplifting discovery"

    def test_estimate_duration(self):
        """Test duration estimation from word count."""
        from app.services.script_generator import ScriptGenerator

        with patch("app.services.script_generator.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch("anthropic.Anthropic"):
                gen = ScriptGenerator()

        # 150 words should be ~60 seconds
        text = " ".join(["word"] * 150)
        duration = gen.estimate_duration(text)
        assert abs(duration - 60.0) < 1.0

        # 1500 words should be ~600 seconds (10 min)
        text = " ".join(["word"] * 1500)
        duration = gen.estimate_duration(text)
        assert abs(duration - 600.0) < 1.0
