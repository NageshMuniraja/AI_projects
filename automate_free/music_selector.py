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
        'upbeat':        ['upbeat', 'energetic', 'happy', 'bouncy'],
        'funny':         ['funny', 'comedy', 'comedic', 'playful', 'silly'],
        'suspenseful':   ['suspense', 'suspenseful', 'tension', 'mystery', 'dramatic', 'thriller'],
        'calm':          ['calm', 'chill', 'relaxed', 'peaceful', 'soft'],
        'epic':          ['epic', 'powerful', 'grand', 'cinematic'],
        'motivational':  ['motivational', 'inspiring', 'uplifting', 'positive'],
        'energetic':     ['energetic', 'exciting', 'dynamic', 'intense'],
        'chill':         ['chill', 'smooth', 'mellow', 'ambient']
    }

    # Audio file extensions to scan
    AUDIO_EXTENSIONS = ("*.mp3", "*.wav", "*.m4a", "*.ogg")

    def __init__(self):
        self.music_dir = Config.BACKGROUND_MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.available_music = {}
        self._scan_available_music()

    def _scan_available_music(self):
        """Scan music directory for available tracks and index them by mood."""
        self.available_music = {}

        if not self.music_dir.exists():
            logger.warning(f"Music directory not found: {self.music_dir}")
            return

        # Scan for supported audio files
        files_found = False
        for pattern in self.AUDIO_EXTENSIONS:
            for music_file in self.music_dir.glob(pattern):
                files_found = True
                filename = music_file.stem.lower()

                # Match filename to mood categories
                for mood, keywords in self.MOOD_MAPPING.items():
                    if any(keyword in filename for keyword in keywords):
                        self.available_music.setdefault(mood, []).append(music_file)

        if not files_found:
            logger.warning(f"No audio files found in music directory: {self.music_dir}")
        else:
            logger.info(
                "Found music for moods: %s",
                {mood: len(files) for mood, files in self.available_music.items()}
            )

    def get_music_for_mood(self, mood_description):
        """
        Get appropriate background music for a given mood description.

        Args:
            mood_description: String describing the desired mood
                             (e.g., "comedic and suspenseful")

        Returns:
            Path to music file (str) or None if no match found and no fallback available.
        """
        if not mood_description:
            logger.warning("No mood description provided for music selection")
            return None

        if not self.available_music:
            logger.warning("No available music indexed; cannot select BGM")
            return None

        mood_lower = mood_description.lower()

        # Try to match mood keywords from the description
        matched_moods = []
        for mood, keywords in self.MOOD_MAPPING.items():
            if any(keyword in mood_lower for keyword in keywords):
                matched_moods.append(mood)

        # Collect candidate files from matched moods
        candidate_files = []
        for mood in matched_moods:
            files = self.available_music.get(mood, [])
            candidate_files.extend(files)

        # If we have candidate files from specific moods, use them
        if candidate_files:
            music_file = random.choice(candidate_files)
            logger.info(f"Selected music for '{mood_description}': {music_file.name}")
            return str(music_file)

        # Fallback: no direct mood match → use any available track
        logger.warning(f"No music found for mood: {mood_description} - using fallback track if available")
        all_files = []
        for files in self.available_music.values():
            all_files.extend(files)

        if all_files:
            music_file = random.choice(all_files)
            logger.info(f"Using fallback music: {music_file.name}")
            return str(music_file)

        # No files at all
        logger.warning("No background music available at all")
        return None

    def list_available_music(self):
        """List all available music organized by mood."""
        result = {}
        for mood, files in self.available_music.items():
            result[mood] = [f.name for f in files]
        return result

    def add_music_file(self, source_path, mood_category):
        """
        Add a music file to the collection.

        Args:
            source_path: Path to the music file to add
            mood_category: Category/mood for the music (e.g., 'upbeat', 'funny')

        Returns:
            True if successfully added, False otherwise.
        """
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Source file not found: {source_path}")
                return False

            # Normalize mood category
            mood_category = (mood_category or "").lower().strip()

            # Derive filename
            filename = source.name
            filename_lower = filename.lower()

            # Check if filename already contains any known mood keyword
            contains_mood_keyword = any(
                keyword in filename_lower
                for keywords in self.MOOD_MAPPING.values()
                for keyword in keywords
            )

            # If no mood keyword present, prefix with mood category
            if mood_category and not contains_mood_keyword:
                filename = f"{mood_category}_{filename}"

            destination = self.music_dir / filename

            # Copy file
            import shutil
            shutil.copy2(source, destination)

            logger.info(f"Added music file: {destination.name}")
            # Re-scan to update index
            self._scan_available_music()
            return True

        except Exception as e:
            logger.error(f"Error adding music file: {e}")
            return False


# Convenience function
def get_background_music(mood_description):
    """
    Convenience function to get background music path for a mood description.

    This will create a new MusicSelector instance, scan the directory, and
    return a suitable track path or None.
    """
    selector = MusicSelector()
    return selector.get_music_for_mood(mood_description)
