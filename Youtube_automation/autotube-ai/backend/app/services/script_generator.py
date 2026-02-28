"""Script Generator Service — generates viral YouTube scripts using Claude API."""

import re
from dataclasses import dataclass, field

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.prompts import SCRIPT_GENERATION_PROMPT, SCRIPT_SYSTEM_PROMPT


@dataclass
class Script:
    topic: str
    niche: str
    text: str
    word_count: int
    estimated_duration_seconds: int
    sections: list[dict] = field(default_factory=list)
    broll_markers: list[dict] = field(default_factory=list)
    music_markers: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class ScriptGenerator:
    WORDS_PER_MINUTE = 150
    # Claude Sonnet pricing per 1M tokens (approx)
    INPUT_COST_PER_M = 3.0
    OUTPUT_COST_PER_M = 15.0

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for script generation")
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
    def generate_script(
        self,
        topic: str,
        niche: str,
        tone: str = "engaging and conversational",
        duration_minutes: int = 10,
    ) -> Script:
        """Generate a full YouTube script for the given topic."""
        target_word_count = duration_minutes * self.WORDS_PER_MINUTE

        prompt = SCRIPT_GENERATION_PROMPT.format(
            topic=topic,
            niche=niche,
            duration_minutes=duration_minutes,
            word_count=target_word_count,
            tone=tone,
        )

        logger.info(f"Generating script for '{topic}' ({niche}, ~{duration_minutes}min)")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SCRIPT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        script_text = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        cost = (
            (input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

        word_count = len(script_text.split())
        duration_seconds = int((word_count / self.WORDS_PER_MINUTE) * 60)

        broll_markers = self._extract_broll_markers(script_text)
        music_markers = self._extract_music_markers(script_text)

        logger.info(
            f"Script generated: {word_count} words, ~{duration_seconds}s, "
            f"${cost:.4f} (in={input_tokens}, out={output_tokens})"
        )

        return Script(
            topic=topic,
            niche=niche,
            text=script_text,
            word_count=word_count,
            estimated_duration_seconds=duration_seconds,
            broll_markers=broll_markers,
            music_markers=music_markers,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
    def refine_script(self, script: Script, feedback: str) -> Script:
        """Refine an existing script based on feedback."""
        prompt = (
            f"Here is a YouTube script to refine:\n\n{script.text}\n\n"
            f"Feedback to incorporate:\n{feedback}\n\n"
            "Rewrite the script incorporating this feedback while keeping "
            "the same structure and markers ([B-ROLL], [MUSIC], [EMPHASIS])."
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SCRIPT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        refined_text = response.content[0].text
        word_count = len(refined_text.split())
        duration_seconds = int((word_count / self.WORDS_PER_MINUTE) * 60)

        cost = (
            (response.usage.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (response.usage.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

        return Script(
            topic=script.topic,
            niche=script.niche,
            text=refined_text,
            word_count=word_count,
            estimated_duration_seconds=duration_seconds,
            broll_markers=self._extract_broll_markers(refined_text),
            music_markers=self._extract_music_markers(refined_text),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=script.cost_usd + cost,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
    def generate_hooks(self, topic: str, count: int = 5) -> list[str]:
        """Generate multiple hook options for a video opening."""
        prompt = (
            f"Generate {count} different hook options (first 15-30 seconds) for a YouTube "
            f"video about: {topic}\n\n"
            "Each hook should be a different style:\n"
            "1. Shocking statistic\n"
            "2. Bold question\n"
            "3. Controversial statement\n"
            "4. Personal story intro\n"
            "5. Fear-based urgency\n\n"
            "Return ONLY the hooks, numbered 1-5, one per line."
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        hooks = [
            line.strip().lstrip("0123456789.)")
            for line in text.strip().split("\n")
            if line.strip()
        ]
        return hooks[:count]

    def estimate_duration(self, script_text: str) -> float:
        """Estimate video duration in seconds based on word count."""
        word_count = len(script_text.split())
        return (word_count / self.WORDS_PER_MINUTE) * 60

    def clean_script_for_tts(self, script_text: str) -> str:
        """Remove markers and formatting from script, leaving only speakable text."""
        cleaned = script_text
        # Remove B-ROLL markers
        cleaned = re.sub(r"\[B-ROLL:.*?\]", "", cleaned)
        # Remove MUSIC markers
        cleaned = re.sub(r"\[MUSIC:.*?\]", "", cleaned)
        # Remove EMPHASIS markers
        cleaned = re.sub(r"\[EMPHASIS\]", "", cleaned)
        # Remove section headers (bold markdown)
        cleaned = re.sub(r"\*\*.*?\*\*", "", cleaned)
        # Remove extra whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"  +", " ", cleaned)
        return cleaned.strip()

    def _extract_broll_markers(self, text: str) -> list[dict]:
        """Extract [B-ROLL: description] markers with approximate positions."""
        markers = []
        lines = text.split("\n")
        word_position = 0

        for line in lines:
            match = re.search(r"\[B-ROLL:\s*(.+?)\]", line)
            if match:
                time_seconds = (word_position / self.WORDS_PER_MINUTE) * 60
                markers.append({
                    "description": match.group(1).strip(),
                    "approximate_time": round(time_seconds, 1),
                    "word_position": word_position,
                })
            word_position += len(line.split())

        return markers

    def _extract_music_markers(self, text: str) -> list[dict]:
        """Extract [MUSIC: mood] markers."""
        markers = []
        lines = text.split("\n")
        word_position = 0

        for line in lines:
            match = re.search(r"\[MUSIC:\s*(.+?)\]", line)
            if match:
                time_seconds = (word_position / self.WORDS_PER_MINUTE) * 60
                markers.append({
                    "mood": match.group(1).strip(),
                    "approximate_time": round(time_seconds, 1),
                })
            word_position += len(line.split())

        return markers
