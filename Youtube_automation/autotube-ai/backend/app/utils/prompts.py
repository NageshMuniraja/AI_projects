"""AI prompt templates for script generation, SEO, and content strategy.

Optimized for maximum viewer retention, CTR, and algorithmic reach.
"""

SCRIPT_SYSTEM_PROMPT = """You are a top-tier YouTube scriptwriter who deeply understands the algorithm.

Core algorithm knowledge you apply:
- The first 8 seconds determine if mobile viewers keep watching (thumb-stop moment)
- The 30-second mark is the biggest drop-off point — you MUST re-hook here
- Average View Duration (AVD) is YouTube's #1 ranking signal
- Curiosity gaps every 30-45 seconds prevent click-away
- Videos over 8 minutes can run mid-roll ads — build natural break points
- Emotional peaks (surprise, awe, anger) drive shares and comments — the algorithm amplifies these
- Pattern interrupts reset attention: change pacing, tone, or visual cue markers
- Short punchy sentences (5 words) alternated with longer explanatory ones (20 words) create rhythm
- Questions addressed directly to the viewer boost comments

You write scripts that feel like a friend sharing something incredible — never robotic, never generic.

BANNED phrases (instant viewer drop-off):
- "In today's video" / "In this video" / "Welcome back"
- "Let's dive in" / "Let's get started" / "Without further ado"
- "In today's digital landscape" / "In an ever-changing world"
- "It's important to note" / "It goes without saying"
- "At the end of the day" / "When all is said and done"
- "But wait, there's more" (infomercial vibes)
- "Make sure to like and subscribe" (save for CTA section only)
- Any form of "buckle up" or "strap in"
- "Did you know" as an opener (overused)"""

SCRIPT_GENERATION_PROMPT = """Write a YouTube script about: {topic}

Niche: {niche}
Target duration: {duration_minutes} minutes ({word_count} words)
Tone: {tone}

=== STRUCTURE (follow EXACTLY) ===

**SECOND 1-4 — PATTERN INTERRUPT** (one shocking line, NO setup):
Drop the viewer into the most surprising, counterintuitive, or emotionally charged fact.
Example formats: "A teenager just [shocking thing]." / "[Big number] people don't know this." / "This changes everything about [topic]."

**SECOND 4-8 — THUMB-STOP HOOK** (tell mobile scrollers why to stop):
Explain in one sentence what they'll discover and why it matters to THEM personally.
Create an open loop they can't resist closing.

**SECOND 8-30 — CONTEXT BRIDGE**:
Provide just enough context to understand the topic. Promise specific value.
Build credibility with one surprising data point. End with a micro-cliffhanger going into the body.

**SECOND 30 — THE RE-HOOK** (CRITICAL — biggest drop-off point):
Insert a dramatic shift: "But here's where it gets really crazy..." / "And that's not even the most insane part..." / "Now forget everything I just said, because..."
This line ALONE can save 15-20% of viewers from dropping off.

**BODY** (5-7 key points):
For each point:
1. Transition hook (never use "next" or "moving on" — use story bridges)
2. Bold claim or surprising statement
3. Evidence: specific numbers, dates, expert quotes, studies
4. Relatable analogy or "imagine this" scenario
5. Emotional spike: make them feel surprise, outrage, awe, or excitement
6. Micro-cliffhanger teasing the next point

After each point, include visual/audio markers on their own line:
[B-ROLL: specific visual description for stock footage — be descriptive]
[MUSIC: mood descriptor like "tension rising" or "triumphant swell"]
[EMPHASIS] before the single most impactful line in each section

**CURIOSITY GAPS** — Insert one every 30-45 seconds:
- "But what happened next shocked everyone..."
- "And this is where the story takes a dark turn..."
- "There's one detail nobody talks about..."
- "The answer will change how you think about [topic]..."

**AD-BREAK MARKERS** — If script exceeds 8 minutes, add `[AD-BREAK]` at 2-3 natural transition points after the 8-minute mark. These should feel like chapter breaks, not interruptions.

**PACING VARIATION**:
- Alternate short punchy sentences (3-7 words) with longer explanatory ones (15-25 words)
- Use sentence fragments for impact. Like this. Powerful.
- Rhetorical questions to engage: "So what does this mean for you?"
- Direct address: "You" should appear at least once every 3-4 sentences

**EMOTIONAL ARC**:
Build tension → small release → bigger tension → bigger release → CLIMAX → resolution
The climax should be in the final third of the body, not the end.

**CTA** (30 seconds):
- Ask a SPECIFIC opinion question related to the topic (drives comments)
- Mention subscribing naturally ("If this blew your mind, you'll love what's coming next week")
- Do NOT say "smash that like button" — instead give a reason: "Drop a like so I know to make more of these"

**OUTRO** (15 seconds):
- Tease the SPECIFIC next video topic with a hook
- End on an open loop or thought-provoking statement
- Final line should be quotable/memorable

=== RULES ===
- Write conversationally — read it aloud; if it sounds like an essay, rewrite it
- Include specific numbers, dates, dollar amounts, and names — vagueness kills retention
- Every sentence must earn its place — if removing it doesn't hurt, remove it
- Mark emphasis with [EMPHASIS] before the most impactful line per section
- [B-ROLL: description] markers should describe SPECIFIC visuals, not vague concepts
- NO phrases from the banned list
- NO generic transitions ("first," "second," "lastly")
- Use story bridges between sections: cause-effect, "but," "so," "which means"
"""

SEO_TITLE_PROMPT = """Generate 10 YouTube video titles for a video about: {topic}

Niche: {niche}
Target audience: {target_audience}

Use these PROVEN viral title patterns (mix at least 6 different ones):

1. Question-based: "Why Does X Do Y?" (40% CTR boost over statements)
2. Number listicle: "7 Reasons X Will Y" (odd numbers outperform even)
3. How-to split: "How I [achieved X]" (personal) AND "How to [achieve X]" (tutorial)
4. Fear/urgency: "X Before It's Too Late" / "Stop Doing X Immediately"
5. Controversy: "Nobody Is Talking About X" / "Why Everyone Is Wrong About X"
6. Secret reveal: "The Hidden Truth About X" / "What X Doesn't Want You to Know"
7. Comparison: "X vs Y — The Winner Surprised Me"
8. Challenge: "I Tried X for 30 Days — Here's What Happened"
9. Prediction: "X Will Change Everything in {current_year}"
10. Superlative: "The Most X Thing Ever" / "The Biggest X Mistake"
11. Specific number: "$X,XXX" or exact stats in title
12. Parenthetical: "Title (this changes everything)" — adds intrigue
13. Warning: "WARNING: X" / "Don't X Until You Watch This"
14. Social proof: "Why X Million People Are Doing Y"
15. Time-pressure: "X in 2026" / "The Future of X"

Rules:
- Each title MUST be under 60 characters (YouTube truncates longer ones)
- Front-load the primary keyword (first 3-4 words)
- Use power words: shocking, secret, insane, genius, hidden, brutal, incredible
- Create curiosity gaps — the title should raise a question the viewer needs answered
- Do NOT use clickbait that the video can't deliver on
- Capitalize key words for emphasis (but not ALL caps for entire title)
- Avoid colons — use dashes or pipes instead

Return as a numbered list. For each title, add a brief note in parentheses explaining why it would get clicks. Rank by predicted CTR (best first).

Example format:
1. "Title Here" (uses curiosity gap + specific number — high CTR)
2. "Another Title" (fear pattern + keyword front-loaded)
"""

SEO_DESCRIPTION_PROMPT = """Write a YouTube video description for:
Title: {title}
Topic: {topic}

=== CRITICAL RULES ===

**First 150 characters** (shown in YouTube search results — this is your ad copy):
- Compelling hook with the primary keyword
- Must make the viewer click — treat it like a Google ad headline
- Do NOT start with "In this video" or "Welcome to"

**Structure:**

[First 150 chars: hook with keyword]

[2-3 sentence expansion of what the viewer will learn]

[EMOJI] Timestamps:
00:00 - [Hook/Intro title]
[Generate accurate timestamps based on a {duration_minutes}-minute video with 5-7 sections]
[Space sections roughly evenly]

[Paragraph about the topic with natural keyword placement — 2-3% keyword density]

[EMOJI] Key Takeaways:
- [3-5 bullet points of main value propositions]

[EMOJI] Related Videos You'll Love:
- [Suggest 2-3 related topic titles the channel might cover]

---
Subscribe for more {niche} content [EMOJI]

#[PrimaryKeyword] #[SecondaryKeyword] #[NicheKeyword]

Requirements:
- Total length: 300-500 words
- Include 3 hashtags above (YouTube displays them above the title)
- Natural keyword placement — NOT keyword stuffing
- Use 3-5 relevant emojis as section markers
- Include a subscribe CTA
"""

SEO_TAGS_PROMPT = """Generate 30 YouTube tags for a video about: {topic}
Niche: {niche}
Title: {title}

Strategy:
- 5 exact-match tags (the exact topic phrase and close variants)
- 8 broad tags (high search volume, niche-level)
- 10 medium-tail tags (topic + modifier combinations)
- 7 long-tail specific tags (question-based, how-to phrases)

Rules:
- First tag should be the exact video title
- Include common misspellings of key terms if applicable
- Include "shorts" variant if topic works for Shorts
- Each tag max 30 characters
- Mix singular and plural forms
- Include competitor/related channel topic tags

Return as a comma-separated list with NO numbering.
"""

CONTENT_STRATEGY_PROMPT = """Analyze channel performance data and suggest the next 10 video topics.

Channel niche: {niche}

=== PERFORMANCE DATA ===

Top performing videos (last 30 days):
{top_videos_data}

Performance metrics breakdown:
{performance_metrics}

Recent topics covered (avoid repeating):
{recent_topics}

=== ANALYSIS INSTRUCTIONS ===

1. **Pattern Recognition**: Identify what the top videos have in common:
   - Title patterns (questions vs. listicles vs. how-to)
   - Topic themes that resonate
   - Engagement patterns (high comments = opinion topics)

2. **Gap Analysis**: What related topics haven't been covered yet?

3. **Trend Alignment**: Which topics are currently trending in this niche?

=== OUTPUT FORMAT ===

For each of the 10 topic suggestions:

**[Number]. [Topic Title]**
- Why it will perform: [1 sentence citing specific data from above]
- Virality score: [1-100]
- Type: [TRENDING / EVERGREEN / HYBRID]
- Suggested title pattern: [specific title using a viral pattern]
- Content angle: [unique twist that differentiates from competitors]

Balance: 60% trending topics (ride the wave), 30% evergreen (long-term search traffic), 10% experimental (test new angles).

Rank by predicted performance (best first). Weight recent performance data (last 7 days) 2x higher than older data.
"""

VIRALITY_SCORING_PROMPT = """Score this topic's viral potential for a YouTube video.

Topic: {topic}
Niche: {niche}
Current trends: {current_trends}

=== SCORING DIMENSIONS (rate each 1-10) ===

1. **Search Demand**: Is there high search volume? Is the trend growing or declining?
2. **Competition Gap**: How many recent videos cover this? Is there room to stand out?
3. **Emotional Intensity**: Does this topic trigger strong emotions (anger, surprise, awe, fear)? Stronger emotions = more shares
4. **Shareability**: Would someone send this to a friend? Does it make the sharer look smart/informed?
5. **Timeliness**: Is this trending RIGHT NOW or is it evergreen? Breaking news scores highest
6. **Watch Time Potential**: Can this topic sustain attention for 8-12 minutes? Or will viewers lose interest?
7. **Comment Bait**: Does this topic provoke opinions and debate? Controversial > informational for engagement
8. **Thumbnail Potential**: Can we create a visually compelling, click-worthy thumbnail for this?
9. **Niche Authority Fit**: Does this match the channel's established expertise and audience expectations?
10. **Series Potential**: Could this become a franchise (Part 2, monthly updates, etc.)?
11. **Monetization Value**: Do advertisers pay well for this topic's audience? (Finance/tech > entertainment)
12. **Cross-Platform Potential**: Would this work as a TikTok, Instagram Reel, or YouTube Short too?

=== OUTPUT FORMAT ===

Return ONLY a JSON object:
{{
  "overall_score": [1-100 weighted average],
  "dimensions": {{
    "search_demand": [1-10],
    "competition_gap": [1-10],
    "emotional_intensity": [1-10],
    "shareability": [1-10],
    "timeliness": [1-10],
    "watch_time_potential": [1-10],
    "comment_bait": [1-10],
    "thumbnail_potential": [1-10],
    "niche_fit": [1-10],
    "series_potential": [1-10],
    "monetization_value": [1-10],
    "cross_platform": [1-10]
  }},
  "reasoning": "[2-3 sentence explanation of the score]",
  "recommended_angle": "[specific unique angle to cover this topic]",
  "suggested_title": "[one viral title suggestion]"
}}
"""
