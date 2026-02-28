#!/usr/bin/env python3
"""Seed the database with pre-built niche configurations for 10 profitable YouTube niches."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import settings
from app.database import async_session_factory, engine, Base
from app.models.niche_config import NicheConfig

NICHE_SEEDS = [
    {
        "name": "Tech Facts & AI News",
        "target_audience": "Tech enthusiasts, 18-35, curious about AI and gadgets",
        "tone": "excited, informative, mind-blowing",
        "keywords": ["AI", "technology", "gadgets", "artificial intelligence", "tech news", "future tech", "robots", "ChatGPT", "machine learning"],
        "competitor_channels": ["Fireship", "Two Minute Papers", "Matt Wolfe"],
        "content_pillars": ["AI breakthroughs", "Did you know tech facts", "Future predictions", "Tech comparisons"],
        "avoid_topics": ["political tech regulation", "crypto scams"],
        "preferred_voice_style": "energetic male",
        "thumbnail_style": "shocking",
        "posting_frequency": "daily",
    },
    {
        "name": "Personal Finance",
        "target_audience": "Young professionals, 22-40, wanting financial freedom",
        "tone": "authoritative, motivating, practical",
        "keywords": ["money", "investing", "passive income", "financial freedom", "stocks", "budget", "savings", "wealth building", "side hustle"],
        "competitor_channels": ["Graham Stephan", "Andrei Jikh", "Nate O'Brien"],
        "content_pillars": ["Investment strategies", "Money habits", "Passive income ideas", "Financial mistakes to avoid"],
        "avoid_topics": ["specific stock picks", "get-rich-quick schemes", "gambling"],
        "preferred_voice_style": "confident male",
        "thumbnail_style": "bold",
        "posting_frequency": "daily",
    },
    {
        "name": "Motivation & Self-Improvement",
        "target_audience": "Ambitious individuals, 18-45, seeking personal growth",
        "tone": "inspiring, powerful, emotional",
        "keywords": ["motivation", "success", "habits", "mindset", "discipline", "self improvement", "productivity", "goals", "confidence"],
        "competitor_channels": ["Motivation Madness", "Be Inspired", "Mulligan Brothers"],
        "content_pillars": ["Success stories", "Daily habits of winners", "Mindset shifts", "Overcoming adversity"],
        "avoid_topics": ["toxic positivity", "unrealistic promises"],
        "preferred_voice_style": "deep authoritative male",
        "thumbnail_style": "bold",
        "posting_frequency": "daily",
    },
    {
        "name": "History & Mysteries",
        "target_audience": "History buffs, mystery lovers, 20-55, curious minds",
        "tone": "mysterious, storytelling, dramatic",
        "keywords": ["history", "mystery", "unsolved", "ancient", "conspiracy", "lost civilization", "what if", "historical events"],
        "competitor_channels": ["History Matters", "Kurzgesagt", "Ridddle"],
        "content_pillars": ["Unsolved mysteries", "What if scenarios", "Ancient civilizations", "Historical events retold"],
        "avoid_topics": ["harmful conspiracy theories", "Holocaust denial"],
        "preferred_voice_style": "narrative male",
        "thumbnail_style": "shocking",
        "posting_frequency": "3x_week",
    },
    {
        "name": "Health & Science",
        "target_audience": "Health-conscious adults, 25-50, science enthusiasts",
        "tone": "educational, eye-opening, trustworthy",
        "keywords": ["health", "science", "body facts", "nutrition", "medical", "brain", "human body", "diet", "wellness"],
        "competitor_channels": ["Kurzgesagt", "What If", "SciShow"],
        "content_pillars": ["Body facts you didn't know", "Nutrition myths busted", "Medical breakthroughs", "Science experiments explained"],
        "avoid_topics": ["anti-vaccine content", "unproven miracle cures"],
        "preferred_voice_style": "clear professional",
        "thumbnail_style": "minimal",
        "posting_frequency": "3x_week",
    },
    {
        "name": "Gaming News & Rankings",
        "target_audience": "Gamers, 14-30, competitive and trend-aware",
        "tone": "hyped, opinionated, fun",
        "keywords": ["gaming", "top 10", "best games", "gaming news", "PS5", "Xbox", "PC gaming", "game rankings", "upcoming games"],
        "competitor_channels": ["gameranx", "WatchMojo Gaming", "MrBeast Gaming"],
        "content_pillars": ["Top 10 lists", "Gaming industry news", "Game comparisons", "Upcoming releases"],
        "avoid_topics": ["gambling in games for minors", "real-money exploits"],
        "preferred_voice_style": "energetic young male",
        "thumbnail_style": "bold",
        "posting_frequency": "daily",
    },
    {
        "name": "Psychology & Human Behavior",
        "target_audience": "Intellectually curious adults, 20-45, self-aware",
        "tone": "fascinating, analytical, relatable",
        "keywords": ["psychology", "human behavior", "mind tricks", "social experiments", "cognitive bias", "manipulation", "body language", "persuasion"],
        "competitor_channels": ["Psych2Go", "Charisma on Command", "Academy of Ideas"],
        "content_pillars": ["Mind tricks and biases", "Social experiments explained", "Dark psychology awareness", "How to read people"],
        "avoid_topics": ["manipulation tactics for harm", "diagnosing individuals"],
        "preferred_voice_style": "calm intellectual",
        "thumbnail_style": "minimal",
        "posting_frequency": "3x_week",
    },
    {
        "name": "Luxury & Wealth",
        "target_audience": "Aspirational viewers, 18-40, fascinated by wealth",
        "tone": "awe-inspiring, luxurious, exclusive",
        "keywords": ["luxury", "billionaire", "expensive", "rich lifestyle", "supercar", "mansion", "wealth", "most expensive"],
        "competitor_channels": ["Luxe Listings", "King Luxury", "Alux.com"],
        "content_pillars": ["Most expensive things", "Billionaire habits", "Luxury comparisons", "How the ultra-rich live"],
        "avoid_topics": ["promoting irresponsible spending", "fake flexing"],
        "preferred_voice_style": "smooth sophisticated",
        "thumbnail_style": "bold",
        "posting_frequency": "3x_week",
    },
    {
        "name": "Scary Stories & Creepypasta",
        "target_audience": "Horror fans, 16-35, thrill seekers",
        "tone": "eerie, suspenseful, immersive",
        "keywords": ["scary", "horror", "creepypasta", "true crime", "ghost stories", "haunted", "paranormal", "dark web", "unsolved"],
        "competitor_channels": ["MrNightmare", "Nexpo", "Lazy Masquerade"],
        "content_pillars": ["True scary stories", "Creepypasta narration", "Unsolved true crime", "Dark internet mysteries"],
        "avoid_topics": ["glorifying violence", "targeting real victims"],
        "preferred_voice_style": "deep ominous male",
        "thumbnail_style": "shocking",
        "posting_frequency": "3x_week",
    },
    {
        "name": "Space & Universe",
        "target_audience": "Space enthusiasts, 15-50, wonder-seekers",
        "tone": "awe-inspiring, educational, mind-expanding",
        "keywords": ["space", "universe", "NASA", "alien", "cosmos", "black hole", "planets", "galaxy", "astronomy", "James Webb"],
        "competitor_channels": ["Kurzgesagt", "Ridddle", "SEA", "Anton Petrov"],
        "content_pillars": ["Mind-blowing space facts", "NASA discoveries", "Alien life possibilities", "Cosmic scale comparisons"],
        "avoid_topics": ["flat earth claims", "alien abduction hoaxes"],
        "preferred_voice_style": "calm wonder-filled",
        "thumbnail_style": "shocking",
        "posting_frequency": "3x_week",
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        for niche_data in NICHE_SEEDS:
            existing = await session.execute(
                NicheConfig.__table__.select().where(NicheConfig.name == niche_data["name"])
            )
            if existing.first():
                print(f"  Skipping (exists): {niche_data['name']}")
                continue

            niche = NicheConfig(**niche_data)
            session.add(niche)
            print(f"  Added: {niche_data['name']}")

        await session.commit()
        print(f"\nSeeded {len(NICHE_SEEDS)} niche configurations.")


if __name__ == "__main__":
    asyncio.run(seed())
