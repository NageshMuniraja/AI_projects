"""
Configuration module for loading environment variables and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default voice
    RUNWAY_API_KEY = os.getenv('RUNWAY_API_KEY')
    RUNWAY_API_VERSION = os.getenv('RUNWAY_API_VERSION')
    
    # YouTube Configuration
    YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
    YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
    YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN')
    
    # Instagram Configuration
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID')
    FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
    
    # Directories
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './output'))
    TEMP_DIR = Path(os.getenv('TEMP_DIR', './temp'))
    LOG_DIR = Path(os.getenv('LOG_DIR', './logs'))
    
    # Video Settings
    SHORTS_DURATION = 60  # seconds (for reels/shorts)
    SHORT_VIDEO_DURATION = 180  # seconds (3 minutes)
    VIDEO_RESOLUTION = (1080, 1920)  # 9:16 for shorts/reels
    SHORT_VIDEO_RESOLUTION = (1920, 1080)  # 16:9 for regular videos
    FPS = 30
    
    # Content Categories
    CONTENT_CATEGORIES = [
        "kids learning",
        "educational fun facts",
        "trending AI topics for kids",
        "funny kids activities",
        "kids playing games",
        "devotional stories for children",
        "science experiments for kids",
        "moral stories",
        "creative arts and crafts"
    ]
    
    # Scheduling
    TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
    DAILY_RUN_TIME = os.getenv('DAILY_RUN_TIME', '08:00')
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (cls.OUTPUT_DIR / 'shorts').mkdir(exist_ok=True)
        (cls.OUTPUT_DIR / 'videos').mkdir(exist_ok=True)
        (cls.TEMP_DIR / 'audio').mkdir(exist_ok=True)
        (cls.TEMP_DIR / 'video').mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate that all required API keys are set"""
        required_keys = {
            'OPENAI_API_KEY': cls.OPENAI_API_KEY,
            'ELEVENLABS_API_KEY': cls.ELEVENLABS_API_KEY,
            'RUNWAY_API_KEY': cls.RUNWAY_API_KEY,
        }
        
        missing = [key for key, value in required_keys.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required API keys: {', '.join(missing)}")
        
        return True
