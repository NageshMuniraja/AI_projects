"""
Quick Setup Script - Switch from Runway to FREE Stock Videos
Saves you $6,000/month!
"""
import os
from pathlib import Path

def main():
    print("=" * 70)
    print("🎬 VIDEO GENERATION COST OPTIMIZER")
    print("=" * 70)
    print()
    
    # Show current costs
    print("💸 CURRENT RUNWAY COSTS:")
    print("   • Per Shorts video: $50")
    print("   • Per Regular video: $150")
    print("   • Daily (1 of each): $200")
    print("   • Monthly: $6,000")
    print("   • Yearly: $72,000")
    print()
    
    print("✅ WITH FREE STOCK VIDEOS:")
    print("   • Per video: $0")
    print("   • Monthly: $0")
    print("   • Yearly: $0")
    print("   • SAVINGS: $72,000/year!")
    print()
    print("=" * 70)
    print()
    
    # Check .env file
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ No .env file found!")
        print()
        print("Create .env file with these keys:")
        print()
        print_env_template()
        return
    
    # Read .env
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Check for Pexels key
    has_pexels = 'PEXELS_API_KEY' in env_content and 'your_' not in env_content.lower()
    has_pixabay = 'PIXABAY_API_KEY' in env_content and 'your_' not in env_content.lower()
    
    print("🔍 CHECKING CONFIGURATION:")
    print()
    
    if has_pexels:
        print("   ✅ Pexels API key configured")
    else:
        print("   ❌ Pexels API key missing")
        print("      Get free key: https://www.pexels.com/api/")
    
    if has_pixabay:
        print("   ✅ Pixabay API key configured")
    else:
        print("   ⚠️  Pixabay API key missing (optional backup)")
        print("      Get free key: https://pixabay.com/api/docs/")
    
    print()
    
    # Check main.py
    main_file = Path("main.py")
    with open(main_file, 'r') as f:
        main_content = f.read()
    
    using_stock = 'StockVideoGenerator' in main_content
    
    if using_stock:
        print("   ✅ Already using FREE stock videos!")
    else:
        print("   ⚠️  Still using expensive Runway AI")
        print()
        print("=" * 70)
        print("🔧 TO SWITCH TO FREE STOCK VIDEOS:")
        print("=" * 70)
        print()
        print("1. Get FREE Pexels API key:")
        print("   https://www.pexels.com/api/")
        print()
        print("2. Add to .env file:")
        print("   PEXELS_API_KEY=your_key_here")
        print()
        print("3. Change ONE line in main.py:")
        print()
        print("   Line 13, change:")
        print("   from video_generator import VideoGenerator")
        print()
        print("   to:")
        print("   from stock_video_generator import StockVideoGenerator as VideoGenerator")
        print()
        print("4. Run: python main.py")
        print()
        print("That's it! Save $6,000/month! 💰")
    
    print()
    print("=" * 70)
    print()
    
    # Offer to show .env template
    if not has_pexels or not has_pixabay:
        print("📝 COMPLETE .env TEMPLATE:")
        print()
        print_env_template()

def print_env_template():
    print("""
# ===== REQUIRED API KEYS =====
# For content and script generation
OPENAI_API_KEY=sk-proj-your_openai_key_here

# For voice narration
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# ===== VIDEO GENERATION (Choose one) =====
# Option 1: FREE Stock Videos (RECOMMENDED)
PEXELS_API_KEY=your_pexels_key_here
PIXABAY_API_KEY=your_pixabay_key_here

# Option 2: Expensive AI (OPTIONAL - costs $50-150 per video)
# RUNWAY_API_KEY=your_runway_key_here

# Set video source: 'pexels', 'pixabay', or 'runway'
VIDEO_SOURCE=pexels

# ===== OPTIONAL =====
# YouTube OAuth (if needed)
# YOUTUBE_CLIENT_ID=
# YOUTUBE_CLIENT_SECRET=
# YOUTUBE_REFRESH_TOKEN=

# Background Music Directory
# BACKGROUND_MUSIC_DIR=./music
# BGM_VOLUME=0.3
    """)

if __name__ == "__main__":
    main()
    print()
    print("Questions? Read COST_SOLUTIONS.md for detailed guide!")
    print()
