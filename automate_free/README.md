# AI Video Automation System

Fully automated system that generates and uploads kids' educational content daily to YouTube and Instagram using AI.

## 🎯 Features

- **Daily Automation**: Generates 1 YouTube Short/Instagram Reel + 1 short educational video every day
- **AI-Powered Content**: Uses OpenAI GPT-4 for trending topic discovery and script generation
- **Text-to-Speech**: ElevenLabs API for natural voiceovers
- **AI Video Generation**: Runway Gen-3 for creating engaging visuals
- **Auto Publishing**: Uploads to YouTube and Instagram automatically
- **Smart Content Mix**: Combines kids learning, trending topics, and AI-related content

## 📋 Content Types

### YouTube Shorts / Instagram Reels (60 seconds)
- Fun facts for kids
- Quick learning moments
- Trending topics explained simply
- Devotional stories
- Funny activities

### Short Videos (3 minutes)
- Educational lessons
- Science experiments
- Moral stories
- Creative activities
- Learning concepts

## 🛠️ System Architecture

```
Daily Job
   ↓
Generate Ideas (OpenAI GPT-4)
   ↓
Generate Script (OpenAI GPT-4)
   ↓
Text-to-Speech (ElevenLabs)
   ↓
Generate Video Clips (Runway API)
   ↓
Assemble Video (FFmpeg/MoviePy)
   ↓
Upload to YouTube (YouTube Data API)
   ↓
Upload to Instagram (Instagram Graph API)
   ↓
Log Results
```

## 📦 Prerequisites

### Required Software
- Python 3.9 or higher
- FFmpeg (for video processing)
- Git (optional)

### API Keys Required

1. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Create API key
   - Billing required for GPT-4 access

2. **ElevenLabs API Key**
   - Sign up at https://elevenlabs.io/
   - Get API key from settings
   - Choose a voice ID for narration

3. **Runway API Key**
   - Sign up at https://runwayml.com/
   - Get API access (requires paid plan)
   - Gen-3 API for video generation

4. **YouTube OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download as `youtube_credentials.json`

5. **Instagram Access Token**
   - Instagram Business or Creator account required
   - Create Facebook App at https://developers.facebook.com/
   - Get Instagram Graph API access
   - Generate long-lived access token
   - Get Instagram User ID and Page ID

## 🚀 Installation

### Step 1: Clone/Download the Project

```powershell
cd c:\AI_Learn\my_project\automate
```

### Step 2: Install Python Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install FFmpeg

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to System PATH
4. Verify: `ffmpeg -version`

### Step 4: Configure API Keys

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ELEVENLABS_API_KEY=your-key-here
   ELEVENLABS_VOICE_ID=voice-id-here
   RUNWAY_API_KEY=your-key-here
   
   # YouTube - will be generated during setup
   # Instagram
   INSTAGRAM_ACCESS_TOKEN=your-token-here
   INSTAGRAM_USER_ID=your-user-id
   FACEBOOK_PAGE_ID=your-page-id
   ```

### Step 5: Setup YouTube Authentication

1. Place `youtube_credentials.json` in project root
2. Run authentication:
   ```powershell
   python youtube_uploader.py
   ```
3. Follow browser prompts to authorize
4. Token will be saved as `youtube_token.pickle`

### Step 6: Verify Instagram Setup

```powershell
python instagram_uploader.py
```

**Important:** Instagram requires videos to be hosted on a publicly accessible URL. You'll need to implement video hosting (AWS S3, your own server, etc.). See `instagram_uploader.py` for details.

## 🎬 Usage

### Run Once (Manual Test)

```powershell
# Generate and upload all content once
python main.py
```

This will:
1. Generate 1 shorts/reel
2. Generate 1 short video
3. Upload both to YouTube
4. Attempt Instagram upload (requires hosting setup)

### Run on Schedule (Automated)

```powershell
# Run scheduler for daily automation
python scheduler.py
```

The scheduler will run daily at the time specified in `.env` (default 8:00 AM).

**To run as background service on Windows:**

1. Using Task Scheduler:
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: Daily at your desired time
   - Action: Start a Program
   - Program: `C:\AI_Learn\my_project\automate\venv\Scripts\python.exe`
   - Arguments: `C:\AI_Learn\my_project\automate\main.py`
   - Start in: `C:\AI_Learn\my_project\automate`

2. Using `pythonw.exe` (hidden console):
   ```powershell
   start pythonw scheduler.py
   ```

## 📁 Project Structure

```
automate/
├── config.py                 # Configuration and settings
├── content_generator.py      # AI idea generation
├── script_generator.py       # Script writing with GPT-4
├── audio_generator.py        # Text-to-speech with ElevenLabs
├── video_generator.py        # AI video generation with Runway
├── video_assembler.py        # Video assembly with FFmpeg
├── youtube_uploader.py       # YouTube API integration
├── instagram_uploader.py     # Instagram API integration
├── main.py                   # Main orchestrator
├── scheduler.py              # Daily scheduler
├── requirements.txt          # Python dependencies
├── .env                      # API keys (create from .env.example)
├── .env.example              # Template for API keys
├── output/                   # Generated videos
│   ├── shorts/              # Shorts/reels
│   └── videos/              # Longer videos
├── temp/                     # Temporary files
│   ├── audio/               # Generated audio
│   └── video/               # Video clips
└── logs/                     # Logs and session data
```

## ⚙️ Configuration

Edit `config.py` or `.env` to customize:

- **Content Categories**: Types of content to generate
- **Video Duration**: Shorts (60s), Videos (180s)
- **Resolution**: 9:16 for shorts, 16:9 for videos
- **Schedule Time**: When to run daily
- **Output Directories**: Where to save files

## 🔧 Troubleshooting

### FFmpeg Errors
- Make sure FFmpeg is installed and in PATH
- Test: `ffmpeg -version`

### OpenAI API Errors
- Check API key is valid
- Ensure billing is set up
- Monitor usage at https://platform.openai.com/usage

### ElevenLabs Errors
- Verify API key and voice ID
- Check character quota
- Test with simple text first

### Runway API Errors
- Ensure API access is enabled (paid plan)
- Check credits/quota
- Video generation takes 1-3 minutes per clip

### YouTube Upload Errors
- Verify OAuth credentials are correct
- Check API quotas in Google Cloud Console
- Ensure YouTube Data API v3 is enabled
- For kids content, `madeForKids` must be true

### Instagram Upload Errors
- Video must be hosted at public URL
- Implement video hosting (see `instagram_uploader.py`)
- Verify access token and permissions
- Check Instagram Graph API limits

## 💡 Tips for Success

1. **Test Individual Modules First**
   ```powershell
   python content_generator.py  # Test idea generation
   python audio_generator.py    # Test TTS
   python video_generator.py    # Test video generation
   ```

2. **Monitor Costs**
   - OpenAI GPT-4: ~$0.03-0.10 per video
   - ElevenLabs: Characters vary by plan
   - Runway: Credits per second of video
   - Budget ~$5-15 per day depending on usage

3. **Start Small**
   - Test with placeholder videos first
   - Use shorter clips during testing
   - Verify uploads before full automation

4. **Content Strategy**
   - Review generated content quality
   - Adjust prompts in script_generator.py
   - Fine-tune categories in config.py
   - Monitor audience engagement

## 📊 Monitoring

- **Logs**: Check `logs/` directory for detailed execution logs
- **Session Data**: JSON files with metadata for each video
- **Output Videos**: Review generated videos in `output/`

## 🔐 Security Notes

- Never commit `.env` or credential files to Git
- Keep API keys secure
- Regularly rotate access tokens
- Monitor API usage for unauthorized access
- Use environment variables in production

## 📈 Scaling

To increase output:
1. Run multiple times per day (adjust scheduler)
2. Generate multiple variations per run
3. Add more content categories
4. Implement parallel processing for video generation

## 🤝 Support

For issues with:
- **OpenAI**: https://help.openai.com/
- **ElevenLabs**: https://help.elevenlabs.io/
- **Runway**: https://help.runwayml.com/
- **YouTube API**: https://developers.google.com/youtube/v3/support
- **Instagram API**: https://developers.facebook.com/support/

## 📝 License

This project is for educational purposes. Ensure compliance with:
- YouTube Terms of Service
- Instagram Terms of Service
- Content licensing for kids' content
- COPPA regulations for children's content

## 🎉 Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] FFmpeg installed and in PATH
- [ ] All API keys obtained
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] YouTube OAuth completed
- [ ] Instagram credentials verified
- [ ] Test run successful (`python main.py`)
- [ ] Scheduler configured
- [ ] Monitoring set up

---

**Happy Automating! 🚀🎬**

For questions or improvements, check the code comments or create an issue.
