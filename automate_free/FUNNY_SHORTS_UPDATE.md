# Updated Features: Funny Viral Shorts with Background Music

## What Changed

Your video automation system has been updated to create **funny, viral shorts and reels** with **background music** for a broader audience, not just kids.

### 🎯 Content Focus

**Before:** Educational kids content (ages 3-12)
**After:** Funny, viral, entertaining content for all ages (10+)

New content categories include:
- 😂 Funny viral moments
- 🎭 Comedy skits and jokes
- 🤝 Relatable life situations
- 🔥 Trending memes and humor
- 😮 Unexpected twists and surprises
- 🎬 Funny fails and bloopers
- ✨ Satisfying and oddly satisfying
- 🤯 Mind-blowing facts
- 💡 Life hacks and tips
- 💪 Motivational and inspirational

### 🎵 Background Music Support

#### New Features:
1. **Automatic music selection** based on content mood
2. **Music mixing** - Voice narration + background music (30% volume)
3. **Mood-based selection** - Matches music to video tone

#### Supported Music Moods:
- `upbeat` - Energetic, bouncy, happy
- `funny` - Comedy, playful, silly
- `suspenseful` - Tension, mystery, dramatic
- `calm` - Chill, relaxed, peaceful
- `epic` - Powerful, grand, cinematic
- `motivational` - Inspiring, uplifting
- `energetic` - Exciting, dynamic, intense
- `chill` - Smooth, mellow, ambient

## 📁 New Files

### 1. `music/` Directory
Store your background music files here (MP3 format).

**File naming convention:**
- `upbeat.mp3` or `upbeat_happy.mp3`
- `funny.mp3` or `funny_comedy.mp3`
- `suspense.mp3` or `suspenseful_dramatic.mp3`
- etc.

### 2. `music_selector.py`
Automatically selects appropriate background music based on script mood.

**Features:**
- Scans `music/` directory for available tracks
- Matches mood keywords to music files
- Random selection from matched tracks
- Fallback to any music if no exact match

### 3. `music/README.md`
Complete guide with:
- Free royalty-free music sources
- Naming conventions
- Download instructions
- Music recommendations

## 🎬 Content Generation Changes

### Shorts/Reels (60 seconds)
- **Focus:** Funny, entertaining, viral-worthy
- **Tone:** Conversational, relatable, humorous
- **Structure:** Hook → Build-up → Punchline/Twist
- **Music:** Auto-selected based on script mood

### Regular Videos (3 minutes)
- **Focus:** Entertaining with educational/inspirational elements
- **Tone:** Engaging, fun, not boring
- **Structure:** Intro → 3 Points → Memorable Conclusion
- **Music:** Background ambiance throughout

## 🎨 Script Changes

### Updated Prompts:
- Emphasize **humor** and **entertainment**
- Focus on **viral potential** and **shareability**
- Use **conversational language**
- Include **comedic timing** with [PAUSE] markers
- Build to **unexpected twists** or punchlines

### New Metadata:
- `humor_type` - Type of humor (situational, clever, relatable)
- `music_mood` - Background music mood description

## ⚙️ Configuration Updates

### config.py
```python
# New content categories (funny, viral, entertaining)
CONTENT_CATEGORIES = [
    "funny viral moments",
    "comedy skits and jokes",
    "relatable life situations",
    ...
]

# Background music settings
BACKGROUND_MUSIC_DIR = Path('./music')
DEFAULT_BGM_VOLUME = 0.3  # 30% volume
```

### video_assembler.py
```python
# New parameter for background music
def assemble_shorts_video(
    ...
    background_music_path=None  # Optional BGM
)

# Automatic audio mixing
def _mix_audio_with_bgm(voice_audio, bgm_path, target_duration)
```

### main.py
```python
# Music selection added to pipeline
# Step 6: Select background music based on script mood
background_music = self.music_selector.get_music_for_mood(music_mood)

# Step 7: Assemble with background music
final_video = self.video_assembler.assemble_shorts_video(
    ...
    background_music_path=background_music
)
```

## 🎵 How to Add Background Music

### Option 1: Download Free Music

Visit these royalty-free sources:
1. **YouTube Audio Library** - https://studio.youtube.com (best option)
2. **Pixabay Music** - https://pixabay.com/music/
3. **Free Music Archive** - https://freemusicarchive.org/
4. **Incompetech** - https://incompetech.com/music/royalty-free/
5. **Bensound** - https://www.bensound.com/

### Option 2: Use Existing Music

```powershell
# Copy your music files to the music directory
Copy-Item "C:\path\to\your\music.mp3" "c:\Users\nagesh.m\Desktop\automate\music\upbeat.mp3"
```

### Option 3: Programmatic Addition

```python
from music_selector import MusicSelector

selector = MusicSelector()
selector.add_music_file(
    source_path="path/to/music.mp3",
    mood_category="funny"
)
```

## 🚀 Quick Start

1. **Add background music:**
   ```powershell
   # Download at least 2-3 tracks to music/ directory
   # Name them: upbeat.mp3, funny.mp3, suspense.mp3
   ```

2. **Ensure .env file has API keys:**
   ```
   OPENAI_API_KEY=sk-proj-...
   ELEVENLABS_API_KEY=...
   RUNWAY_API_KEY=...
   ```

3. **Run automation:**
   ```powershell
   python main.py
   ```

4. **Check output:**
   - Videos saved to `output/shorts/` or `output/videos/`
   - Will include voice + background music
   - Automatic upload to YouTube

## 🎯 Example Content Types

### Funny Shorts Examples:
- "3 Things That Make Zero Sense" (comedic observations)
- "When You Try to Adult" (relatable situations)
- "Plot Twist: This Will Blow Your Mind" (unexpected reveals)
- "Life Hacks Nobody Asked For" (silly but useful tips)

### Regular Video Examples:
- "5 Mind-Blowing Facts About AI" (educational + entertaining)
- "Why Everyone Is Talking About This" (trending topics)
- "The Funniest Way to Learn Science" (education with humor)
- "Stories That Will Make You Smile" (feel-good content)

## 📊 Music Volume Control

Default: Background music plays at **30% volume**

To adjust:
```python
# In config.py or .env file
DEFAULT_BGM_VOLUME = 0.3  # 30% (range: 0.0 to 1.0)
```

Recommendations:
- **Comedy/Funny:** 0.2-0.3 (20-30%) - Don't overpower punchlines
- **Dramatic/Epic:** 0.4-0.5 (40-50%) - More emphasis
- **Calm/Chill:** 0.15-0.25 (15-25%) - Subtle background

## ⚠️ Important Notes

1. **Music Required:** Without music files, videos will still generate (just no BGM)
2. **Royalty-Free Only:** Always use licensed or royalty-free music
3. **Attribution:** Check if music requires attribution (add to video description)
4. **File Format:** Use MP3 format for compatibility
5. **File Size:** Keep music files under 10MB for faster processing

## 🔧 Troubleshooting

### No music playing in videos?
1. Check if `music/` directory has MP3 files
2. Verify file names contain mood keywords (upbeat, funny, etc.)
3. Check logs: "Selected background music: filename.mp3"

### Music too loud/quiet?
```python
# Adjust in config.py
DEFAULT_BGM_VOLUME = 0.2  # Lower = quieter (0.0 to 1.0)
```

### Want specific music for specific videos?
```python
# In main.py, manually specify:
background_music = "c:/path/to/specific/track.mp3"
```

## 📝 System Architecture

```
Content Generation Flow:
1. Generate funny/viral idea → includes music_mood
2. Generate script → includes background_music field
3. Generate voice narration (ElevenLabs)
4. Generate video clips (Runway AI)
5. Select background music → based on mood
6. Mix audio → voice + BGM at 30% volume
7. Assemble final video → clips + mixed audio + text overlays
8. Upload to YouTube/Instagram
```

## 🎉 What You Get

- **Funnier content** that appeals to broader audiences
- **Professional videos** with background music
- **Viral potential** with trending topics and humor
- **Automatic music selection** based on content mood
- **Clean, family-friendly** but not just for little kids

Enjoy creating viral funny shorts! 🚀😂🎵
