"""Voiceover Generator Service — TTS using ElevenLabs (primary) and Edge-TTS (fallback)."""

import asyncio
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.file_manager import get_unique_path


@dataclass
class VoiceoverResult:
    audio_path: str
    duration_seconds: float
    provider: str
    cost_usd: float = 0.0


class VoiceoverGenerator:
    MAX_CHUNK_CHARS = 4500  # ElevenLabs limit per request
    # ElevenLabs pricing: ~$0.30 per 1000 chars
    ELEVENLABS_COST_PER_CHAR = 0.0003

    def __init__(self):
        self.elevenlabs_key = settings.ELEVENLABS_API_KEY
        self._elevenlabs_client = None

    @property
    def elevenlabs_client(self):
        if self._elevenlabs_client is None and self.elevenlabs_key:
            from elevenlabs import ElevenLabs
            self._elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_key)
        return self._elevenlabs_client

    def generate_voiceover(
        self,
        script: str,
        voice_id: str | None = None,
        provider: str = "elevenlabs",
        speed: float = 1.0,
        output_dir: Path | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover from script text. Falls back to edge-tts if elevenlabs fails."""
        if output_dir is None:
            output_dir = settings.voiceovers_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = get_unique_path(output_dir, "voiceover", ".mp3")

        if provider == "elevenlabs" and self.elevenlabs_key:
            try:
                return self._generate_elevenlabs(script, voice_id, output_path, speed)
            except Exception as e:
                logger.warning(f"ElevenLabs failed, falling back to Edge-TTS: {e}")

        return self._generate_edge_tts(script, output_path, speed)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_elevenlabs(
        self,
        script: str,
        voice_id: str | None,
        output_path: Path,
        speed: float,
    ) -> VoiceoverResult:
        """Generate voiceover using ElevenLabs API."""
        client = self.elevenlabs_client
        if not client:
            raise RuntimeError("ElevenLabs client not initialized")

        voice_id = voice_id or "EXAVITQu4vr4xnSDxMaL"  # Default: Sarah
        chunks = self._split_into_chunks(script)
        audio_segments = []

        logger.info(f"Generating ElevenLabs voiceover: {len(chunks)} chunk(s), "
                     f"{len(script)} chars, voice={voice_id}")

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)")

            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=chunk,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            # Collect all audio bytes from generator
            audio_bytes = b"".join(audio_generator)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segment = AudioSegment.from_mp3(tmp_path)
            audio_segments.append(segment)
            Path(tmp_path).unlink(missing_ok=True)

        # Merge all segments
        combined = audio_segments[0]
        for seg in audio_segments[1:]:
            combined += seg

        # Adjust speed if needed
        if speed != 1.0:
            combined = self._adjust_speed_pydub(combined, speed)

        combined.export(str(output_path), format="mp3", bitrate="192k")
        duration = len(combined) / 1000.0
        cost = len(script) * self.ELEVENLABS_COST_PER_CHAR

        logger.info(f"ElevenLabs voiceover: {duration:.1f}s, ${cost:.4f}")

        return VoiceoverResult(
            audio_path=str(output_path),
            duration_seconds=duration,
            provider="elevenlabs",
            cost_usd=cost,
        )

    def _generate_edge_tts(
        self,
        script: str,
        output_path: Path,
        speed: float,
    ) -> VoiceoverResult:
        """Generate voiceover using Edge-TTS (free, no API key)."""
        logger.info(f"Generating Edge-TTS voiceover: {len(script)} chars")

        # Calculate rate adjustment string
        rate_str = f"+{int((speed - 1) * 100)}%" if speed >= 1 else f"{int((speed - 1) * 100)}%"

        # Run edge-tts as subprocess (it's async internally but we run sync)
        cmd = [
            "edge-tts",
            "--voice", "en-US-GuyNeural",
            "--rate", rate_str,
            "--text", script,
            "--write-media", str(output_path),
            "--write-subtitles", str(output_path.with_suffix(".vtt")),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Edge-TTS failed: {result.stderr}")

        # Get duration
        audio = AudioSegment.from_mp3(str(output_path))
        duration = len(audio) / 1000.0

        logger.info(f"Edge-TTS voiceover: {duration:.1f}s (free)")

        return VoiceoverResult(
            audio_path=str(output_path),
            duration_seconds=duration,
            provider="edge-tts",
            cost_usd=0.0,
        )

    def normalize_audio(self, audio_path: str, target_lufs: float = -14.0) -> str:
        """Normalize audio to target LUFS using FFmpeg loudnorm filter."""
        output_path = Path(audio_path).with_suffix(".normalized.mp3")

        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-ar", "44100",
            "-ab", "192k",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"Audio normalization failed: {result.stderr[:200]}")
            return audio_path

        # Replace original with normalized
        Path(audio_path).unlink(missing_ok=True)
        output_path.rename(audio_path)
        logger.info(f"Audio normalized to {target_lufs} LUFS")
        return audio_path

    def mix_background_music(
        self,
        voiceover_path: str,
        music_path: str,
        output_path: str | None = None,
        music_volume_db: float = -20.0,
        duck_volume_db: float = -30.0,
    ) -> str:
        """Mix background music with voiceover, ducking music during speech."""
        vo = AudioSegment.from_file(voiceover_path)
        music = AudioSegment.from_file(music_path)

        # Adjust music volume
        music = music + music_volume_db

        # Loop music to match voiceover length
        if len(music) < len(vo):
            loops_needed = (len(vo) // len(music)) + 1
            music = music * loops_needed
        music = music[:len(vo)]

        # Simple mix (ducking would require voice activity detection — simplified here)
        mixed = vo.overlay(music)

        if output_path is None:
            output_path = Path(voiceover_path).with_suffix(".mixed.mp3")

        mixed.export(str(output_path), format="mp3", bitrate="192k")
        logger.info(f"Mixed voiceover + music: {len(mixed) / 1000:.1f}s")
        return str(output_path)

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries, respecting API limits."""
        if len(text) <= self.MAX_CHUNK_CHARS:
            return [text]

        chunks = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.MAX_CHUNK_CHARS:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _adjust_speed_pydub(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Adjust audio playback speed using pydub frame rate manipulation."""
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": int(audio.frame_rate * speed)},
        )
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
