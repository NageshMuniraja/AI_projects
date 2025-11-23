"""
Setup Helper Script
Validates configuration and tests all components
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_dependencies():
    """Check if all Python dependencies are installed"""
    print_section("Checking Python Dependencies")
    
    required = [
        'openai', 'requests', 'dotenv', 'elevenlabs',
        'google.auth', 'googleapiclient', 'schedule',
        'PIL', 'moviepy'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.split('.')[0])
            logger.info(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        logger.error(f"\nMissing packages: {', '.join(missing)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("\n✓ All Python dependencies installed")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print_section("Checking FFmpeg")
    
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"✓ FFmpeg installed: {version}")
            return True
    except FileNotFoundError:
        pass
    
    logger.error("✗ FFmpeg not found")
    logger.error("Install from: https://ffmpeg.org/download.html")
    logger.error("Add to system PATH")
    return False

def check_config():
    """Check configuration and API keys"""
    print_section("Checking Configuration")
    
    try:
        from config import Config
        
        # Check if .env exists
        env_file = Path('.env')
        if not env_file.exists():
            logger.error("✗ .env file not found")
            logger.error("Run: copy .env.example .env")
            logger.error("Then edit .env with your API keys")
            return False
        
        logger.info("✓ .env file exists")
        
        # Check API keys
        keys_status = []
        
        if Config.OPENAI_API_KEY:
            logger.info("✓ OpenAI API key configured")
            keys_status.append(True)
        else:
            logger.error("✗ OpenAI API key missing")
            keys_status.append(False)
        
        if Config.ELEVENLABS_API_KEY:
            logger.info("✓ ElevenLabs API key configured")
            keys_status.append(True)
        else:
            logger.error("✗ ElevenLabs API key missing")
            keys_status.append(False)
        
        if Config.RUNWAY_API_KEY:
            logger.info("✓ Runway API key configured")
            keys_status.append(True)
        else:
            logger.error("✗ Runway API key missing")
            keys_status.append(False)
        
        # Check YouTube credentials
        youtube_creds = Path('youtube_credentials.json')
        if youtube_creds.exists():
            logger.info("✓ YouTube credentials file found")
            keys_status.append(True)
        else:
            logger.warning("⚠ YouTube credentials file not found")
            logger.warning("  Download from Google Cloud Console")
            keys_status.append(False)
        
        # Check Instagram (optional)
        if Config.INSTAGRAM_ACCESS_TOKEN:
            logger.info("✓ Instagram access token configured")
        else:
            logger.warning("⚠ Instagram access token not configured (optional)")
        
        # Create directories
        Config.create_directories()
        logger.info("✓ Output directories created")
        
        return all(keys_status)
        
    except Exception as e:
        logger.error(f"✗ Configuration error: {e}")
        return False

def test_openai():
    """Test OpenAI API connection"""
    print_section("Testing OpenAI API")
    
    try:
        from openai import OpenAI
        from config import Config
        
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        logger.info(f"✓ OpenAI API working: {result}")
        return True
        
    except Exception as e:
        logger.error(f"✗ OpenAI API error: {e}")
        return False

def test_elevenlabs():
    """Test ElevenLabs API connection"""
    print_section("Testing ElevenLabs API")
    
    try:
        import requests
        from config import Config
        
        headers = {"xi-api-key": Config.ELEVENLABS_API_KEY}
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers
        )
        response.raise_for_status()
        
        voices = response.json().get('voices', [])
        logger.info(f"✓ ElevenLabs API working ({len(voices)} voices available)")
        
        # Show some voices
        for voice in voices[:3]:
            logger.info(f"  - {voice['name']} (ID: {voice['voice_id']})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ElevenLabs API error: {e}")
        return False

def check_youtube_auth():
    """Check YouTube authentication"""
    print_section("Checking YouTube Authentication")
    
    token_file = Path('youtube_token.pickle')
    
    if token_file.exists():
        logger.info("✓ YouTube token file exists")
        logger.info("  Run 'python youtube_uploader.py' to test upload")
        return True
    else:
        logger.warning("⚠ YouTube not authenticated yet")
        logger.warning("  Run: python youtube_uploader.py")
        logger.warning("  Follow browser prompts to authorize")
        return False

def run_setup_checks():
    """Run all setup checks"""
    print("\n" + "🚀 AI Video Automation - Setup Validator".center(60))
    print("=" * 60)
    
    checks = {
        "Python Dependencies": check_dependencies(),
        "FFmpeg": check_ffmpeg(),
        "Configuration": check_config(),
        "OpenAI API": False,
        "ElevenLabs API": False,
        "YouTube Auth": False
    }
    
    # Test APIs if config is OK
    if checks["Configuration"]:
        checks["OpenAI API"] = test_openai()
        checks["ElevenLabs API"] = test_elevenlabs()
        checks["YouTube Auth"] = check_youtube_auth()
    
    # Summary
    print_section("Setup Summary")
    
    passed = sum(checks.values())
    total = len(checks)
    
    for name, status in checks.items():
        icon = "✓" if status else "✗"
        logger.info(f"{icon} {name}")
    
    print("\n" + "-"*60)
    logger.info(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to run.")
        print("\nNext steps:")
        print("  1. Test run: python main.py")
        print("  2. Start scheduler: python scheduler.py")
        print("\nFor help, see README.md or QUICKSTART.md")
        return True
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - No .env file: copy .env.example .env")
        print("  - No API keys: Edit .env with your keys")
        print("  - YouTube: Run python youtube_uploader.py")
        return False

if __name__ == "__main__":
    success = run_setup_checks()
    sys.exit(0 if success else 1)
