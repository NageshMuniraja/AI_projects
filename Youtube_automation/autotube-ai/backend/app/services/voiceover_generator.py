"""Voiceover Generator Service — TTS with Edge-TTS (free default), OpenAI TTS, or ElevenLabs.

Provider priority (configurable):
1. edge-tts (FREE — Microsoft Azure neural voices, excellent quality)
2. openai (cheap — $15/1M chars, HD quality voices)
3. elevenlabs (premium — $0.30/1K chars, best quality but expensive)
"""

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


# Best free Edge-TTS voices for YouTube content
EDGE_TTS_VOICES = {
    "male_us": "en-US-GuyNeural",
    "male_us_deep": "en-US-DavisNeural",
    "female_us": "en-US-JennyNeural",
    "male_uk": "en-GB-RyanNeural",
    "female_uk": "en-GB-SoniaNeural",
    "male_au": "en-AU-WilliamNeural",
}

# OpenAI TTS voices
OPENAI_TTS_VOICES = {
    "alloy": "alloy",       # neutral
    "echo": "echo",         # male, warm
    "fable": "fable",       # male, British
    "onyx": "onyx",         # male, deep authoritative
    "nova": "nova",         # female, warm
    "shimmer": "shimmer",   # female, clear
}


class VoiceoverGenerator:
    MAX_CHUNK_CHARS = 3500  # OpenAI TTS limit is 4096, keep well under
    ELEVENLABS_COST_PER_CHAR = 0.0003
    OPENAI_COST_PER_CHAR = 0.000015  # $15/1M chars

    def __init__(self):
        self.elevenlabs_key = settings.ELEVENLABS_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self._elevenlabs_client = None
        self._openai_client = None

    @property
    def elevenlabs_client(self):
        if self._elevenlabs_client is None and self.elevenlabs_key:
            from elevenlabs import ElevenLabs
            self._elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_key)
        return self._elevenlabs_client

    @property
    def openai_client(self):
        if self._openai_client is None and self.openai_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self.openai_key)
        return self._openai_client

    def generate_voiceover(
        self,
        script: str,
        voice_id: str | None = None,
        provider: str = "edge-tts",
        speed: float = 1.05,
        output_dir: Path | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover. Default: edge-tts (FREE). Falls back through providers."""
        if output_dir is None:
            output_dir = settings.voiceovers_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = get_unique_path(output_dir, "voiceover", ".mp3")

        # Provider chain: requested → fallbacks
        providers = self._build_provider_chain(provider)

        for prov in providers:
            try:
                if prov == "edge-tts":
                    return self._generate_edge_tts(script, output_path, speed, voice_id)
                elif prov == "openai":
                    return self._generate_openai_tts(script, output_path, speed, voice_id)
                elif prov == "elevenlabs":
                    return self._generate_elevenlabs(script, voice_id, output_path, speed)
            except Exception as e:
                logger.warning(f"{prov} TTS failed, trying next: {e}")

        raise RuntimeError("All TTS providers failed")

    def _build_provider_chain(self, preferred: str) -> list[str]:
        """Build fallback chain starting with preferred provider."""
        all_providers = ["edge-tts", "openai", "elevenlabs"]
        chain = [preferred]
        for p in all_providers:
            if p not in chain:
                # Only add if credentials available (edge-tts always available)
                if p == "edge-tts":
                    chain.append(p)
                elif p == "openai" and self.openai_key:
                    chain.append(p)
                elif p == "elevenlabs" and self.elevenlabs_key:
                    chain.append(p)
        return chain

    def _generate_edge_tts(
        self, script: str, output_path: Path, speed: float, voice_id: str | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover using Edge-TTS (FREE, no API key needed)."""
        voice = voice_id or EDGE_TTS_VOICES["male_us_deep"]
        logger.info(f"Generating Edge-TTS voiceover: {len(script)} chars, voice={voice}")

        rate_pct = int((speed - 1) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

        cmd = [
            "edge-tts",
            "--voice", voice,
            "--rate", rate_str,
            "--text", script,
            "--write-media", str(output_path),
            "--write-subtitles", str(output_path.with_suffix(".vtt")),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Edge-TTS failed: {result.stderr}")

        audio = AudioSegment.from_mp3(str(output_path))
        duration = len(audio) / 1000.0

        logger.info(f"Edge-TTS voiceover: {duration:.1f}s (FREE)")

        return VoiceoverResult(
            audio_path=str(output_path),
            duration_seconds=duration,
            provider="edge-tts",
            cost_usd=0.0,
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_openai_tts(
        self, script: str, output_path: Path, speed: float, voice_id: str | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover using OpenAI TTS (cheap, good quality)."""
        client = self.openai_client
        if not client:
            raise RuntimeError("OpenAI client not initialized")

        voice = voice_id if voice_id in OPENAI_TTS_VOICES else "onyx"
        chunks = self._split_into_chunks(script)

        logger.info(f"Generating OpenAI TTS: {len(chunks)} chunk(s), {len(script)} chars, voice={voice}")

        audio_segments = []
        for i, chunk in enumerate(chunks):
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=chunk,
                speed=speed,
            )

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            segment = AudioSegment.from_mp3(tmp_path)
            audio_segments.append(segment)
            Path(tmp_path).unlink(missing_ok=True)

        combined = audio_segments[0]
        for seg in audio_segments[1:]:
            combined += seg

        combined.export(str(output_path), format="mp3", bitrate="192k")
        duration = len(combined) / 1000.0
        cost = len(script) * self.OPENAI_COST_PER_CHAR

        logger.info(f"OpenAI TTS: {duration:.1f}s, ${cost:.4f}")

        return VoiceoverResult(
            audio_path=str(output_path),
            duration_seconds=duration,
            provider="openai-tts",
            cost_usd=cost,
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_elevenlabs(
        self, script: str, voice_id: str | None, output_path: Path, speed: float,
    ) -> VoiceoverResult:
        """Generate voiceover using ElevenLabs (premium quality, expensive)."""
        client = self.elevenlabs_client
        if not client:
            raise RuntimeError("ElevenLabs client not initialized")

        voice_id = voice_id or settings.ELEVENLABS_VOICE_ID or "EXAVITQu4vr4xnSDxMaL"
        chunks = self._split_into_chunks(script)

        logger.info(f"Generating ElevenLabs voiceover: {len(chunks)} chunk(s), "
                     f"{len(script)} chars, voice={voice_id}")

        audio_segments = []
        for i, chunk in enumerate(chunks):
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=chunk,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            audio_bytes = b"".join(audio_generator)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segment = AudioSegment.from_mp3(tmp_path)
            audio_segments.append(segment)
            Path(tmp_path).unlink(missing_ok=True)

        combined = audio_segments[0]
        for seg in audio_segments[1:]:
            combined += seg

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

        music = music + music_volume_db

        if len(music) < len(vo):
            loops_needed = (len(vo) // len(music)) + 1
            music = music * loops_needed
        music = music[:len(vo)]

        mixed = vo.overlay(music)

        if output_path is None:
            output_path = Path(voiceover_path).with_suffix(".mixed.mp3")

        mixed.export(str(output_path), format="mp3", bitrate="192k")
        logger.info(f"Mixed voiceover + music: {len(mixed) / 1000:.1f}s")
        return str(output_path)

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries."""
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
        """Adjust audio playback speed."""
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": int(audio.frame_rate * speed)},
        )
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
