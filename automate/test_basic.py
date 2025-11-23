"""
Simple Test Script
Quick test of core functionality without using API credits
"""
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*60)
    print("Testing Module Imports")
    print("="*60)
    
    modules = [
        'config',
        'content_generator',
        'script_generator',
        'audio_generator',
        'video_generator',
        'video_assembler',
        'youtube_uploader',
        'instagram_uploader',
        'main',
        'scheduler'
    ]
    
    success = True
    for module in modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except Exception as e:
            logger.error(f"✗ {module}: {str(e)[:50]}")
            success = False
    
    return success

def test_config():
    """Test configuration setup"""
    print("\n" + "="*60)
    print("Testing Configuration")
    print("="*60)
    
    try:
        from config import Config
        
        # Test directory creation
        Config.create_directories()
        logger.info("✓ Directories created")
        
        # Check directories exist
        dirs = [Config.OUTPUT_DIR, Config.TEMP_DIR, Config.LOG_DIR]
        for d in dirs:
            if d.exists():
                logger.info(f"✓ {d}")
            else:
                logger.error(f"✗ {d} not created")
                return False
        
        # Test configuration validation
        try:
            Config.validate()
            logger.info("✓ Configuration valid")
            return True
        except ValueError as e:
            logger.warning(f"⚠ Configuration incomplete: {e}")
            logger.warning("  This is expected if you haven't added API keys yet")
            return True
            
    except Exception as e:
        logger.error(f"✗ Configuration error: {e}")
        return False

def test_simple_generation():
    """Test simple content generation (no API calls)"""
    print("\n" + "="*60)
    print("Testing Basic Functionality")
    print("="*60)
    
    try:
        # Test creating a simple test file
        from config import Config
        
        test_file = Config.TEMP_DIR / "test.txt"
        with open(test_file, 'w') as f:
            f.write("Test successful!")
        
        if test_file.exists():
            logger.info("✓ File I/O working")
            test_file.unlink()  # Delete test file
        else:
            logger.error("✗ File I/O failed")
            return False
        
        # Test JSON handling
        import json
        test_data = {"test": "data", "number": 123}
        json_str = json.dumps(test_data)
        parsed = json.loads(json_str)
        
        if parsed["test"] == "data":
            logger.info("✓ JSON handling working")
        else:
            logger.error("✗ JSON handling failed")
            return False
        
        logger.info("✓ Basic functionality tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic functionality error: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("Next Steps")
    print("="*60)
    print("""
To complete setup:

1. Add API Keys
   - Edit .env file with your API keys
   - Get keys from:
     • OpenAI: https://platform.openai.com/
     • ElevenLabs: https://elevenlabs.io/
     • Runway: https://runwayml.com/

2. Setup YouTube
   - Download OAuth credentials
   - Save as 'youtube_credentials.json'
   - Run: python youtube_uploader.py

3. Validate Setup
   - Run: python setup_check.py
   - This will test API connections

4. First Run
   - Run: python main.py
   - Or: run.bat (Windows)
   - Monitor logs/ directory

5. Enable Automation
   - Run: python scheduler.py
   - Or: Set up Windows Task Scheduler

For detailed instructions:
- See README.md for complete guide
- See QUICKSTART.md for quick setup
- See PROJECT_SUMMARY.md for overview
    """)

def main():
    """Run all tests"""
    print("\n" + "🧪 AI Video Automation - Quick Test".center(60))
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Basic Functions": test_simple_generation()
    }
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All basic tests passed!")
        print("The system structure is set up correctly.")
        show_next_steps()
    else:
        print("\n⚠️ Some tests failed.")
        print("Please check the errors above and:")
        print("1. Make sure all dependencies are installed")
        print("2. Run: pip install -r requirements.txt")
        print("3. Check that .env file exists (copy from .env.example)")
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
