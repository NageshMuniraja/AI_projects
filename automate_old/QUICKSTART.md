# Quick Setup Guide

## Fast Track Installation (15 minutes)

### 1. Install Prerequisites (5 min)

```powershell
# Check Python version (need 3.9+)
python --version

# Install FFmpeg
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

### 2. Install Python Packages (2 min)

```powershell
cd c:\AI_Learn\my_project\automate
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure API Keys (5 min)

```powershell
# Copy template
copy .env.example .env

# Edit .env with your keys
notepad .env
```

Required keys:
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys
- Runway: https://app.runwayml.com/account

### 4. Setup YouTube (3 min)

1. Download OAuth credentials from Google Cloud Console
2. Save as `youtube_credentials.json`
3. Run: `python youtube_uploader.py`
4. Authorize in browser

### 5. Test Run

```powershell
# Test individual components
python content_generator.py

# Full test run (WARNING: Uses API credits!)
python main.py
```

## First Time Run Checklist

Before running `python main.py`, verify:

✅ All API keys in `.env`  
✅ FFmpeg in PATH (`ffmpeg -version`)  
✅ YouTube authenticated  
✅ At least $10 in API credits  
✅ Directories created automatically  

## Expected Runtime

- **Shorts/Reel**: 10-15 minutes
  - Idea generation: 30 sec
  - Script: 1 min
  - Audio: 1 min
  - Video clips (4x): 8-12 min
  - Assembly: 1 min
  - Upload: 1-2 min

- **Short Video**: 20-30 minutes
  - Similar but more clips and longer duration

**Total daily runtime: ~30-45 minutes**

## Cost Estimates (Per Day)

- OpenAI GPT-4: ~$0.10-0.20
- ElevenLabs: ~1000 characters (~$0.10-0.30)
- Runway Gen-3: 60-90 seconds video (~$3-9)
- **Total: ~$5-15/day**

## Common Issues

### "Module not found"
```powershell
# Make sure venv is activated
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "FFmpeg not found"
```powershell
# Add FFmpeg to PATH or specify full path
```

### "API key invalid"
- Double-check keys in `.env`
- No quotes needed around keys
- No spaces after `=`

### "YouTube upload failed"
- Re-run authentication
- Check OAuth credentials file
- Verify API is enabled in Google Cloud

## Quick Test (No API Costs)

```powershell
# Test config
python -c "from config import Config; Config.validate(); print('Config OK!')"

# Test modules
python -c "from content_generator import ContentIdeaGenerator; print('Modules OK!')"
```

## Production Deployment

### Option 1: Windows Task Scheduler
- Runs at specific time daily
- Best for reliability

### Option 2: Python Scheduler
```powershell
python scheduler.py
```
- Runs continuously
- Checks every minute

### Option 3: Cloud Deployment
- Deploy to AWS EC2, Azure VM, or Google Cloud
- Use cron jobs on Linux
- Set up monitoring

## Next Steps

1. ✅ Complete setup following this guide
2. 🧪 Test with `python main.py`
3. 📊 Review logs in `logs/` directory
4. 🎬 Check output in `output/shorts/` and `output/videos/`
5. 🚀 Enable scheduler for automation
6. 📈 Monitor daily and adjust

## Support Resources

- **Documentation**: README.md
- **Code Comments**: Each module has detailed comments
- **Logs**: Check `logs/` for error details
- **Test Scripts**: Each module can run standalone

---

**Ready to start?** Run `python main.py` and watch the magic happen! 🎬✨
