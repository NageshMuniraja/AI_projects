"""Caption Generator Service — generates SRT subtitles from audio using Whisper or Edge-TTS VTT."""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class SubtitleEntry:
    index: int
    start_time: float  # seconds
    end_time: float  # seconds
    text: str


@dataclass
class CaptionResult:
    srt_path: str
    entries: list[SubtitleEntry] = field(default_factory=list)
    provider: str = "whisper"


class CaptionGenerator:
    def generate_captions(
        self,
        audio_path: str,
        output_dir: Path | None = None,
        method: str = "whisper",
    ) -> CaptionResult:
        """Generate SRT captions from audio file."""
        audio_path = Path(audio_path)
        if output_dir is None:
            output_dir = audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        srt_path = output_dir / f"{audio_path.stem}.srt"

        # Check if edge-tts already generated a VTT file
        vtt_path = audio_path.with_suffix(".vtt")
        if vtt_path.exists():
            logger.info("Using existing Edge-TTS VTT file for captions")
            entries = self._parse_vtt(vtt_path)
            self._write_srt(entries, srt_path)
            return CaptionResult(srt_path=str(srt_path), entries=entries, provider="edge-tts")

        if method == "whisper":
            try:
                return self._generate_whisper(str(audio_path), srt_path)
            except Exception as e:
                logger.warning(f"Whisper failed, falling back to simple caption: {e}")

        # Fallback: generate simple timed captions from text
        return self._generate_simple_captions(str(audio_path), srt_path)

    def _generate_whisper(self, audio_path: str, srt_path: Path) -> CaptionResult:
        """Generate captions using faster-whisper."""
        logger.info("Generating captions with faster-whisper...")

        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, word_timestamps=True)

        entries = []
        idx = 1
        current_words = []
        current_start = 0.0

        for segment in segments:
            if segment.words:
                for word in segment.words:
                    current_words.append(word.word)
                    if len(current_words) == 1:
                        current_start = word.start

                    # Group 4-6 words per subtitle entry
                    if len(current_words) >= 5 or word.word.rstrip().endswith((".", "!", "?")):
                        entries.append(SubtitleEntry(
                            index=idx,
                            start_time=current_start,
                            end_time=word.end,
                            text=" ".join(current_words).strip(),
                        ))
                        idx += 1
                        current_words = []
            else:
                # No word timestamps, use segment level
                entries.append(SubtitleEntry(
                    index=idx,
                    start_time=segment.start,
                    end_time=segment.end,
                    text=segment.text.strip(),
                ))
                idx += 1

        # Flush remaining words
        if current_words:
            entries.append(SubtitleEntry(
                index=idx,
                start_time=current_start,
                end_time=entries[-1].end_time + 2.0 if entries else current_start + 3.0,
                text=" ".join(current_words).strip(),
            ))

        self._write_srt(entries, srt_path)
        logger.info(f"Generated {len(entries)} caption entries with Whisper")

        return CaptionResult(srt_path=str(srt_path), entries=entries, provider="whisper")

    def _generate_simple_captions(
        self, audio_path: str, srt_path: Path
    ) -> CaptionResult:
        """Fallback: generate evenly-spaced captions (no word-level timing)."""
        logger.info("Generating simple timed captions (fallback)")

        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000.0

        # Create entries every 3 seconds as placeholder
        entries = []
        interval = 3.0
        idx = 1
        t = 0.0
        while t < duration:
            end = min(t + interval, duration)
            entries.append(SubtitleEntry(
                index=idx,
                start_time=t,
                end_time=end,
                text="...",  # Placeholder — will be overwritten by script text
            ))
            idx += 1
            t += interval

        self._write_srt(entries, srt_path)
        return CaptionResult(srt_path=str(srt_path), entries=entries, provider="simple")

    def _parse_vtt(self, vtt_path: Path) -> list[SubtitleEntry]:
        """Parse a WebVTT file into SubtitleEntry list."""
        content = vtt_path.read_text()
        entries = []
        idx = 1

        # Match VTT cue blocks: timestamp --> timestamp\ntext
        pattern = r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)

        for start_str, end_str, text in matches:
            entries.append(SubtitleEntry(
                index=idx,
                start_time=self._vtt_time_to_seconds(start_str),
                end_time=self._vtt_time_to_seconds(end_str),
                text=text.strip(),
            ))
            idx += 1

        return entries

    def _write_srt(self, entries: list[SubtitleEntry], path: Path) -> None:
        """Write SubtitleEntry list to SRT file."""
        lines = []
        for entry in entries:
            start = self._seconds_to_srt_time(entry.start_time)
            end = self._seconds_to_srt_time(entry.end_time)
            lines.append(f"{entry.index}\n{start} --> {end}\n{entry.text}\n")

        path.write_text("\n".join(lines))

    @staticmethod
    def _vtt_time_to_seconds(time_str: str) -> float:
        """Convert HH:MM:SS.mmm to seconds."""
        parts = time_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
