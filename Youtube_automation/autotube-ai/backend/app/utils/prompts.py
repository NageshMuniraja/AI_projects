"""AI prompt templates for script generation, SEO, and content strategy.

Full prompt implementations will be added in Phase 2 (script gen) and Phase 4 (SEO).
"""

SCRIPT_SYSTEM_PROMPT = """You are an expert YouTube scriptwriter who creates viral,
engaging scripts for faceless YouTube channels. You write in a conversational,
high-energy style that maximizes viewer retention."""

SCRIPT_GENERATION_PROMPT = """Write a YouTube script about: {topic}

Niche: {niche}
Target duration: {duration_minutes} minutes ({word_count} words)
Tone: {tone}

Structure the script as follows:

**HOOK** (0-30 seconds):
Write a pattern-interrupt opening. Use a shocking statement, surprising question,
or bold claim that stops the scroll. Do NOT use generic openings like "In today's
digital landscape" or "Let's dive in."

**INTRO** (30-60 seconds):
Provide context and promise value. Tell the viewer exactly what they'll learn and
why it matters to them personally.

**BODY** (5-7 key points):
For each point:
- Start with a transition hook
- Make a clear claim
- Provide evidence or data
- Give a relatable example
- End with an emotional hook or curiosity gap

After each point, include one of these markers on its own line:
[B-ROLL: brief visual description for stock footage]
[MUSIC: mood descriptor like "tension building" or "uplifting"]

Every 60-90 seconds, insert a "curiosity gap" — a teaser about what's coming next
to prevent viewers from clicking away.

**CTA** (30 seconds):
Natural call-to-action for subscribe, like, and comment. Ask a specific question
related to the topic.

**OUTRO** (15 seconds):
Tease the next video topic to build anticipation.

Rules:
- Write conversationally, as if talking to a friend
- Include specific numbers, dates, and data points
- Use emotional triggers: surprise, fear, excitement, humor
- Mark emphasis with [EMPHASIS] before important lines
- NO AI-sounding phrases
- NO generic transitions
- Make every sentence earn its place
"""

SEO_TITLE_PROMPT = """Generate 5 YouTube video titles for a video about: {topic}

Niche: {niche}
Target audience: {target_audience}

Rules:
- Each title under 60 characters
- Include the primary keyword naturally
- Use proven viral patterns:
  - "How X Changed Y Forever"
  - "I Tried X for 30 Days"
  - "Why X is [shocking adjective]"
  - "X Things About Y That Will Blow Your Mind"
  - "The Truth About X Nobody Tells You"
- Create curiosity gaps
- Use power words (shocking, secret, insane, genius)
- Do NOT use clickbait that the video can't deliver on

Return as a numbered list, ranked by predicted CTR (best first).
"""

SEO_DESCRIPTION_PROMPT = """Write a YouTube video description for:
Title: {title}
Topic: {topic}

Requirements:
- First 2 lines: compelling hook with primary keyword (visible in search results)
- Timestamps section with chapter markers
- 300-500 words total
- Natural keyword placement (not keyword stuffing)
- Include: "Subscribe for more {niche} content"
- End with channel branding footer
"""

SEO_TAGS_PROMPT = """Generate 30 YouTube tags for a video about: {topic}
Niche: {niche}

Mix of:
- 10 broad tags (high volume)
- 10 medium-tail tags
- 10 long-tail specific tags

Return as a comma-separated list.
"""

CONTENT_STRATEGY_PROMPT = """Analyze these top-performing videos and suggest next topics:

Channel niche: {niche}
Top performing videos (last 30 days):
{top_videos_data}

Recent topics covered (avoid repeating):
{recent_topics}

Generate 10 topic suggestions with:
1. Topic title
2. Why it would perform well (1 sentence)
3. Estimated virality score (1-100)
4. Whether it's trending or evergreen

Balance: 70% trending, 30% evergreen content.
"""

VIRALITY_SCORING_PROMPT = """Score this topic's viral potential for YouTube:

Topic: {topic}
Niche: {niche}
Current trends: {current_trends}

Score from 1-100 considering:
- Search volume / demand
- Competition level
- Emotional engagement potential
- Shareability
- Timeliness / relevance

Return ONLY a JSON object: {{"score": N, "reasoning": "brief explanation"}}
"""
