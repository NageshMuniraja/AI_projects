# AutoTube AI

Fully automated faceless YouTube channel engine. Researches trending topics, generates scripts with AI, creates voiceovers, sources visuals, assembles professional videos, optimizes SEO, and uploads to YouTube — all on autopilot.

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (v2+)
- API keys (see below)

### 1. Configure Environment

```bash
cd autotube-ai
cp .env.example .env
```

Edit `.env` and add your API keys:

| Variable | Required | Where to Get It |
|----------|----------|-----------------|
| `ANTHROPIC_API_KEY` | Yes | https://console.anthropic.com/settings/keys |
| `ELEVENLABS_API_KEY` | Yes* | https://elevenlabs.io/app/settings/api-keys |
| `PEXELS_API_KEY` | Yes | https://www.pexels.com/api/new/ |
| `PIXABAY_API_KEY` | Yes | https://pixabay.com/api/docs/ |
| `STABILITY_API_KEY` | No | https://platform.stability.ai/account/keys |
| `YOUTUBE_CLIENT_ID` | For upload | Google Cloud Console (see YouTube Setup below) |
| `YOUTUBE_CLIENT_SECRET` | For upload | Google Cloud Console |

*If no ElevenLabs key, the system automatically falls back to Edge-TTS (free, no key needed).

### 2. Start the System

```bash
docker compose up -d
```

This starts 5 containers:

| Container | Port | Role |
|-----------|------|------|
| `postgres` | internal | Database |
| `redis` | internal | Message broker |
| `backend` | **8001** | FastAPI API server |
| `celery-worker` | — | Async video processing |
| `celery-beat` | — | Scheduled automation |

### 3. Verify It's Running

```bash
curl http://localhost:8001/health
# {"status":"healthy","service":"autotube-ai"}
```

### 4. Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Seed Niche Configurations (Optional)

```bash
docker compose exec backend python -m scripts.seed_niches
```

This loads 10 pre-built niches: Tech/AI, Finance, Motivation, History, Health, Gaming, Psychology, Luxury, Horror, Space.

### 6. Create a Channel

```bash
curl -X POST http://localhost:8001/api/channels/ \
  -H "Content-Type: application/json" \
  -d '{"name": "AI Facts Daily", "niche": "Tech Facts & AI News"}'
```

Response:
```json
{
  "id": 1,
  "name": "AI Facts Daily",
  "niche": "Tech Facts & AI News",
  "caption_style": "hormozi",
  "thumbnail_style": "bold",
  "posting_frequency": "daily",
  "is_active": true
}
```

### 7. Generate Your First Video

```bash
curl -X POST http://localhost:8001/api/pipeline/trigger \
  -H "Content-Type: application/json" \
  -d '{"channel_id": 1, "topic": "5 AI Tools That Will Replace Your Job in 2026"}'
```

This dispatches a Celery task that runs the full pipeline asynchronously. Check progress:

```bash
curl http://localhost:8001/api/pipeline/status/1
```

---

## Architecture

```
                          +------------------+
                          |   FastAPI API     |
                          |   (port 8001)     |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
             +------+------+              +------+------+
             | PostgreSQL  |              |    Redis    |
             |  (database) |              |  (broker)   |
             +-------------+              +------+------+
                                                 |
                                    +------------+------------+
                                    |                         |
                             +------+------+           +------+------+
                             |   Celery    |           | Celery Beat |
                             |   Worker    |           | (scheduler) |
                             +------+------+           +-------------+
                                    |
                    +---------------+---------------+
                    |       |       |       |       |
                 Claude  Eleven  Pexels  Stability  YouTube
                  API    Labs    API      AI API    API v3
```

### 12 Services

| Service | Purpose | API Used |
|---------|---------|----------|
| Script Generator | AI-written YouTube scripts | Claude Sonnet |
| Voiceover Generator | Text-to-speech audio | ElevenLabs / Edge-TTS |
| Asset Collector | Stock footage + AI images | Pexels, Pixabay, Stability AI |
| Caption Generator | Word-level subtitles | faster-whisper |
| Video Assembler | Composite final video | MoviePy + FFmpeg |
| Thumbnail Generator | Click-worthy thumbnails | Pillow |
| SEO Optimizer | Titles, descriptions, tags | Claude Sonnet |
| YouTube Uploader | Upload + set metadata | YouTube Data API v3 |
| YouTube Analytics | Pull performance data | YouTube Analytics API |
| Trend Researcher | Find viral topics | Google Trends + Claude |
| Content Strategy | AI content planning | Claude Sonnet |
| Scheduler | Automated daily/weekly tasks | Celery Beat |

---

## How the Pipeline Works

When you trigger a pipeline, the system runs through these steps automatically:

```
  TRIGGER (POST /api/pipeline/trigger)
      |
      v
  [Step 3] SCRIPT GENERATION
      |   Claude Sonnet writes a 1500-word YouTube script
      |   with [B-ROLL] markers and sections
      v
  [Step 4] VOICEOVER
      |   ElevenLabs (or Edge-TTS fallback) generates audio
      |   Split into chunks, normalized to -14 LUFS
      v
  [Step 5] ASSET COLLECTION
      |   Parse script for [B-ROLL: description] markers
      |   Search Pexels -> Pixabay -> generate with Stability AI
      v
  [Step 6] CAPTION GENERATION
      |   faster-whisper transcribes audio with word timestamps
      |   Groups 4-6 words per subtitle entry -> SRT file
      v
  [Step 7] THUMBNAIL
      |   Pillow renders 3 variants (bold/minimal/shocking)
      |   1280x720, JPEG, text overlay with stroke/shadow
      v
  [Step 8] VIDEO ASSEMBLY
      |   MoviePy composites: assets + captions + intro + outro
      |   1920x1080, 30fps, H.264, ~10 Mbps
      v
  [Step 9] SEO OPTIMIZATION
      |   Claude generates optimized title, description, 30 tags
      v
  [Step 10] YOUTUBE UPLOAD
      |   Resumable upload via YouTube Data API v3
      |   Sets thumbnail, metadata, publish schedule
      v
  [Step 11] TRACKING
      |   Saves youtube_video_id, starts analytics tracking
      v
    DONE
```

### Resumability

If any step fails, the pipeline stores the error and last successful step. Resume it:

```bash
curl -X POST http://localhost:8001/api/pipeline/resume/1
```

It picks up exactly where it left off — no wasted API calls.

### Estimated Cost per Video

| Component | Cost |
|-----------|------|
| Claude script | ~$0.02 |
| ElevenLabs voice (10 min) | ~$0.45 |
| Stock footage | Free (Pexels/Pixabay) |
| Stability AI images (2-3) | ~$0.06 |
| YouTube upload | Free |
| **Total** | **~$0.50 per video** |

With Edge-TTS (free voice): **~$0.08 per video**.

---

## API Reference

Base URL: `http://localhost:8001`

### Health Check
```bash
GET /health
```

### Channels

```bash
# List all channels
GET /api/channels/

# Create channel
POST /api/channels/
{
  "name": "My Channel",
  "niche": "Tech Facts & AI News",
  "caption_style": "hormozi",       # hormozi | standard | karaoke
  "thumbnail_style": "bold",        # bold | minimal | shocking
  "posting_frequency": "daily"      # daily | 3x_week | weekly
}

# Update channel
PATCH /api/channels/{id}
{
  "voice_id": "EXAVITQu4vr4xnSDxMaL",    # ElevenLabs voice ID
  "posting_frequency": "3x_week"
}

# Delete channel
DELETE /api/channels/{id}
```

### Pipeline

```bash
# Trigger new video pipeline
POST /api/pipeline/trigger
{
  "channel_id": 1,
  "topic": "Why AI Will Change Everything"    # Optional - auto-researched if omitted
}
# Returns: video object with status "queued"

# Check pipeline progress
GET /api/pipeline/status/{video_id}
# Returns: step-by-step status (pending/in_progress/completed/failed)

# Resume failed pipeline
POST /api/pipeline/resume/{video_id}
```

### Videos

```bash
# List videos (with filters)
GET /api/videos/?channel_id=1&status=published&limit=20&offset=0

# Get video details
GET /api/videos/{video_id}

# Delete video
DELETE /api/videos/{video_id}
```

### Analytics

```bash
# Video analytics (daily breakdown)
GET /api/analytics/video/{video_id}

# Channel summary (last 30 days)
GET /api/analytics/channel/{channel_id}?days=30
```

### Settings

```bash
# View system configuration
GET /api/settings/
# Returns: env, resolution, caption style, which APIs are configured
```

---

## Configuration Reference

All settings in `.env`:

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key for script + SEO generation | `sk-ant-api03-...` |
| `PEXELS_API_KEY` | Free stock video/image API | `abc123...` |
| `PIXABAY_API_KEY` | Free stock footage API | `12345-abc...` |

### Recommended

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_API_KEY` | Premium TTS voices | Falls back to Edge-TTS |
| `STABILITY_API_KEY` | AI image generation | Uses only stock footage |

### YouTube (for uploading)

| Variable | Description |
|----------|-------------|
| `YOUTUBE_CLIENT_ID` | OAuth2 client ID from Google Cloud |
| `YOUTUBE_CLIENT_SECRET` | OAuth2 client secret |
| `YOUTUBE_REDIRECT_URI` | OAuth callback URL |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | `development` or `production` |
| `SECRET_KEY` | (change this) | Encryption key for OAuth tokens |
| `MEDIA_DIR` | `/app/media` | Where generated files are stored |
| `MAX_CONCURRENT_PIPELINES` | `3` | Max parallel video generations |
| `DEFAULT_VIDEO_RESOLUTION` | `1080p` | `1080p` or `4K` |
| `DEFAULT_CAPTION_STYLE` | `hormozi` | Caption overlay style |
| `DEFAULT_FPS` | `30` | Video frame rate |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Database & Redis (defaults work with Docker)

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://autotube:autotube_secret@postgres:5432/autotube` |
| `REDIS_URL` | `redis://redis:6379/0` |

---

## Automated Scheduling

Celery Beat runs these tasks automatically:

| Schedule | Task | What It Does |
|----------|------|--------------|
| **Daily 6:00 AM UTC** | Trend Research | Finds trending topics for all active channels |
| **Daily 6:30 AM UTC** | Pull Analytics | Fetches YouTube stats for all published videos |
| **Monday 3:00 AM UTC** | Content Calendar | Generates weekly content plan per channel |
| **Monday 4:00 AM UTC** | Cleanup | Deletes temp files (>24h) and old videos (>30 days) |

View Celery worker logs:
```bash
docker compose logs -f celery-worker
```

View scheduler logs:
```bash
docker compose logs -f celery-beat
```

---

## YouTube OAuth Setup

To enable automatic uploading to YouTube:

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3**
4. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the credentials JSON

### 2. Run OAuth Setup Script

```bash
# Place your downloaded credentials file
cp ~/Downloads/client_secret_xxx.json autotube-ai/client_secrets.json

# Run the setup script
docker compose exec backend python scripts/setup_youtube_oauth.py
```

This opens a browser window for Google authentication. After authorizing, the script displays your tokens.

### 3. Add Tokens to Channel

The tokens are stored encrypted in the database per-channel. Use the API to update a channel with OAuth credentials after running the setup script.

---

## Niche Configurations

10 pre-built niches with optimized settings:

| Niche | Tone | Voice Style | Frequency | Content Pillars |
|-------|------|-------------|-----------|-----------------|
| Tech Facts & AI News | Excited | Energetic male | Daily | AI breakthroughs, gadgets, coding, startups |
| Personal Finance | Authoritative | Confident male | Daily | Investing, saving, passive income, budgeting |
| Motivation | Inspiring | Deep male | Daily | Success stories, habits, mindset, discipline |
| History & Mysteries | Mysterious | Narrative male | 3x/week | Ancient civilizations, unsolved mysteries, wars |
| Health & Science | Educational | Professional | 3x/week | Nutrition, medical facts, psychology, fitness |
| Gaming News | Hyped | Young male | Daily | Rankings, industry news, reviews, tips |
| Psychology | Analytical | Calm intellectual | 3x/week | Cognitive biases, social experiments, behavior |
| Luxury & Wealth | Awe-inspiring | Sophisticated | 3x/week | Billionaires, expensive items, lifestyle |
| Scary Stories | Eerie | Deep ominous | 3x/week | Creepypasta, true crime, paranormal |
| Space & Universe | Wonder-filled | Calm | 3x/week | Cosmos, NASA, planets, alien theories |

Seed them:
```bash
docker compose exec backend python scripts/seed_niches.py
```

---

## Common Operations

### Generate a Batch of Videos

```bash
# Generate 5 videos for channel 1 (topics auto-researched)
curl -X POST http://localhost:8001/api/pipeline/trigger \
  -H "Content-Type: application/json" \
  -d '{"channel_id": 1, "count": 5}'
```

### Check All Video Statuses

```bash
curl http://localhost:8001/api/videos/?channel_id=1
```

### Stop the System

```bash
docker compose down          # Stop containers (keep data)
docker compose down -v       # Stop and delete all data
```

### Rebuild After Code Changes

```bash
docker compose build backend
docker compose up -d
```

### View Logs

```bash
docker compose logs -f backend         # API server
docker compose logs -f celery-worker   # Video processing
docker compose logs -f celery-beat     # Scheduler
```

### Run Tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

---

## File Structure

```
autotube-ai/
├── docker-compose.yml          # 5-container setup
├── .env                        # Your API keys (never commit)
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── config.py           # Settings
│   │   ├── database.py         # PostgreSQL connection
│   │   ├── api/                # REST endpoints
│   │   ├── models/             # Database tables
│   │   ├── schemas/            # Request/response models
│   │   ├── services/           # 12 business logic services
│   │   ├── pipeline/           # 11-step video pipeline
│   │   ├── workers/            # Celery async tasks
│   │   └── utils/              # Helpers, prompts, validators
│   └── tests/                  # 19 passing tests
├── scripts/                    # Setup & utility scripts
├── templates/thumbnails/       # Thumbnail style configs
└── media/                      # Generated content (gitignored)
    ├── voiceovers/
    ├── footage/
    ├── thumbnails/
    ├── final_videos/
    └── temp/
```
