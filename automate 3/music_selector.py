"""
Background Music Selector Module
Automatically selects appropriate background music based on content mood
"""
import logging
from pathlib import Path
import random
from config import Config

logger = logging.getLogger(__name__)

class MusicSelector:
    """Select appropriate background music for videos"""
    
    # Map mood keywords to music file patterns
    MOOD_MAPPING = {
        'upbeat': ['upbeat', 'energetic', 'happy', 'bouncy'],
        'funny': ['funny', 'comedy', 'playful', 'silly'],
        'suspenseful': ['suspense', 'tension', 'mystery', 'dramatic'],
        'calm': ['calm', 'chill', 'relaxed', 'peaceful'],
        'epic': ['epic', 'powerful', 'grand', 'cinematic'],
        'motivational': ['motivational', 'inspiring', 'uplifting', 'positive'],
        'energetic': ['energetic', 'exciting', 'dynamic', 'intense'],
        'chill': ['chill', 'smooth', 'mellow', 'ambient']
    }
    
    def __init__(self):
        self.music_dir = Config.BACKGROUND_MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self._scan_available_music()
    
    def _scan_available_music(self):
        """Scan music directory for available tracks"""
        self.available_music = {}
        
        if not self.music_dir.exists():
            logger.warning(f"Music directory not found: {self.music_dir}")
            return
        
        # Scan for MP3 files
        for music_file in self.music_dir.glob('*.mp3'):
            filename = music_file.stem.lower()
            
            # Match filename to mood categories
            for mood, keywords in self.MOOD_MAPPING.items():
                if any(keyword in filename for keyword in keywords):
                    if mood not in self.available_music:
                        self.available_music[mood] = []
                    self.available_music[mood].append(music_file)
        
        logger.info(f"Found music for moods: {list(self.available_music.keys())}")
    
    def get_music_for_mood(self, mood_description):
        """
        Get appropriate background music for a given mood description
        
        Args:
            mood_description: String describing the desired mood (e.g., "upbeat and energetic")
        
        Returns:
            Path to music file or None if no match found
        """
        if not mood_description:
            return None
        
        mood_lower = mood_description.lower()
        
        # Try to match mood keywords
        matched_moods = []
        for mood, keywords in self.MOOD_MAPPING.items():
            if any(keyword in mood_lower for keyword in keywords):
                matched_moods.append(mood)
        
        # Get music files for matched moods
        available_files = []
        for mood in matched_moods:
            if mood in self.available_music:
                available_files.extend(self.available_music[mood])
        
        if not available_files:
            logger.warning(f"No music found for mood: {mood_description}")
            # Fallback: return any random music if available
            all_files = []
            for files in self.available_music.values():
                all_files.extend(files)
            if all_files:
                music_file = random.choice(all_files)
                logger.info(f"Using fallback music: {music_file.name}")
                return str(music_file)
            return None
        
        # Randomly select from matched files
        music_file = random.choice(available_files)
        logger.info(f"Selected music for '{mood_description}': {music_file.name}")
        return str(music_file)
    
    def list_available_music(self):
        """List all available music organized by mood"""
        result = {}
        for mood, files in self.available_music.items():
            result[mood] = [f.name for f in files]
        return result
    
    def add_music_file(self, source_path, mood_category):
        """
        Add a music file to the collection
        
        Args:
            source_path: Path to the music file to add
            mood_category: Category/mood for the music (e.g., 'upbeat', 'funny')
        """
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Source file not found: {source_path}")
                return False
            
            # Create a filename with mood prefix if not present
            filename = source.name
            if not any(keyword in filename.lower() for keywords in self.MOOD_MAPPING.values() for keyword in keywords):
                filename = f"{mood_category}_{filename}"
            
            destination = self.music_dir / filename
            
            # Copy file
            import shutil
            shutil.copy2(source, destination)
            
            logger.info(f"Added music file: {filename}")
            self._scan_available_music()
            return True
            
        except Exception as e:
            logger.error(f"Error adding music file: {e}")
            return False

# Convenience function
def get_background_music(mood_description):
    """Get background music path for a mood description"""
    selector = MusicSelector()
    return selector.get_music_for_mood(mood_description)
