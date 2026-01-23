"""
Audio Generator Module
Converts scripts to audio using ElevenLabs TTS API
"""
import logging
import requests
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class AudioGenerator:
    """Generate audio using ElevenLabs TTS API"""
    
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY is not set. Set ELEVENLABS_API_KEY in your environment or .env file.")
            raise ValueError("Missing ELEVENLABS_API_KEY")
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def list_voices(self):
        """List available voices"""
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            voices = response.json()
            logger.info(f"Available voices: {len(voices.get('voices', []))}")
            return voices.get('voices', [])
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []
    
    def clean_script(self, script):
        """Remove markers and clean script for TTS"""
        # Remove pause markers
        cleaned = script.replace('[PAUSE]', ', ')
        # Remove emphasis markers
        cleaned = cleaned.replace('*', '')
        return cleaned
    
    def generate_audio(self, script, output_path, voice_id=None):
        """Generate audio from script"""
        if voice_id is None:
            voice_id = self.voice_id
        
        # Clean the script
        text = self.clean_script(script)
        #text = self.clean_script(script)[:75] # remove this line after testing
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Voice settings optimized for children's content
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,  # More dynamic
                "similarity_boost": 0.75,
                "style": 0.5,  # Balanced
                "use_speaker_boost": True
            }
        }
        
        try:
            logger.info(f"Generating audio for {len(text)} characters...")
            response = requests.post(url, json=data, headers=headers)

            # Explicitly handle non-2xx responses
            if not response.ok:
                logger.error(f"Failed to generate audio: HTTP {response.status_code} - {response.text}")
                return None

            # Save audio file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Audio saved to {output_path}")
            return str(output_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating audio: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def generate_audio_with_sections(self, sections, output_dir, prefix="section"):
        """Generate audio for multiple script sections"""
        audio_files = []
        
        for i, section in enumerate(sections):
            section_name = section.get('name', f'section_{i}')
            script = section.get('script', '')
            
            if not script:
                continue
            
            output_path = Path(output_dir) / f"{prefix}_{section_name}.mp3"
            audio_path = self.generate_audio(script, output_path)
            
            if audio_path:
                audio_files.append({
                    'section': section_name,
                    'path': audio_path,
                    'duration': section.get('duration', 0)
                })
        
        logger.info(f"Generated {len(audio_files)} audio sections")
        return audio_files
    
    def get_audio_duration(self, audio_path):
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(audio_path)
            duration = len(audio) / 1000.0  # Convert to seconds
            return duration
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            return 0
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0
    
    def adjust_speech_speed(self, audio_path, target_duration, output_path=None):
        """Adjust audio speed to match target duration"""
        try:
            from pydub import AudioSegment
            from pydub.playback import play
            
            audio = AudioSegment.from_mp3(audio_path)
            current_duration = len(audio) / 1000.0
            
            if abs(current_duration - target_duration) < 2:
                logger.info("Audio duration is close enough to target")
                return audio_path
            
            # Calculate speed factor
            speed_factor = current_duration / target_duration
            
            # Adjust speed (only if reasonable, between 0.8 and 1.2)
            if 0.8 <= speed_factor <= 1.2:
                # This requires ffmpeg
                import ffmpeg
                if output_path is None:
                    output_path = audio_path.replace('.mp3', '_adjusted.mp3')
                
                stream = ffmpeg.input(audio_path)
                stream = ffmpeg.filter(stream, 'atempo', speed_factor)
                stream = ffmpeg.output(stream, output_path)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                logger.info(f"Adjusted audio speed by {speed_factor:.2f}x")
                return output_path
            else:
                logger.warning(f"Speed factor {speed_factor:.2f} out of range, using original")
                return audio_path
                
        except Exception as e:
            logger.error(f"Error adjusting audio speed: {e}")
            return audio_path


if __name__ == "__main__":
    # Test the audio generator
    logging.basicConfig(level=logging.INFO)
    Config.create_directories()
    
    generator = AudioGenerator()
    
    # Test with a sample script
    test_script = """
    *Hello kids!* [PAUSE] Have you ever wondered why the sky is blue? 
    Well, today we're going to find out! [PAUSE]
    It's all about something called *light scattering*. 
    When sunlight enters our atmosphere, it bounces off tiny air molecules. 
    Blue light scatters more than other colors, and that's why we see a blue sky! 
    *Isn't that amazing?* [PAUSE]
    """
    
    output_path = Config.TEMP_DIR / "audio" / "test_audio.mp3"
    result = generator.generate_audio(test_script, output_path)
    
    if result:
        print(f"Audio generated successfully: {result}")
        duration = generator.get_audio_duration(result)
        print(f"Duration: {duration:.2f} seconds")
