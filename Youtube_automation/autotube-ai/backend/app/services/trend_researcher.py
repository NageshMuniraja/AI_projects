"""Trend Researcher Service — finds viral topics using Google Trends, YouTube search, Reddit, and AI scoring."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import anthropic
import feedparser
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.prompts import VIRALITY_SCORING_PROMPT


@dataclass
class TrendingTopic:
    title: str
    source: str
    virality_score: int = 0
    reasoning: str = ""
    related_queries: list[str] = field(default_factory=list)
    is_trending: bool = True
    suggested_angle: str = ""
    suggested_title: str = ""


@dataclass
class VideoIdea:
    title: str
    channel_url: str
    views: int = 0
    published_at: str = ""


# Niche-to-subreddit mapping for Reddit trending
NICHE_SUBREDDITS = {
    "tech": ["technology", "gadgets", "programming", "artificial"],
    "ai": ["artificial", "MachineLearning", "ChatGPT", "LocalLLaMA"],
    "finance": ["personalfinance", "investing", "stocks", "CryptoCurrency"],
    "motivation": ["GetMotivated", "selfimprovement", "productivity", "Entrepreneur"],
    "history": ["history", "HistoryMemes", "AskHistorians", "todayilearned"],
    "health": ["health", "science", "Fitness", "nutrition"],
    "gaming": ["gaming", "Games", "pcgaming", "PS5"],
    "psychology": ["psychology", "neuroscience", "behavioral", "socialskills"],
    "luxury": ["luxury", "watches", "cars", "RealEstate"],
    "scary": ["nosleep", "creepypasta", "UnresolvedMysteries", "TrueCrime"],
    "horror": ["nosleep", "creepypasta", "horror", "TrueCrime"],
    "space": ["space", "astronomy", "nasa", "astrophysics"],
}

# Niche-to-YouTube search keywords
NICHE_SEARCH_KEYWORDS = {
    "tech": ["tech news 2026", "new technology", "best gadgets"],
    "ai": ["AI news", "artificial intelligence", "ChatGPT"],
    "finance": ["investing tips", "make money", "passive income"],
    "motivation": ["motivation", "success habits", "discipline"],
    "history": ["history documentary", "ancient civilization", "unsolved mystery"],
    "health": ["health tips", "nutrition science", "fitness"],
    "gaming": ["gaming news", "best games 2026", "game review"],
    "psychology": ["psychology facts", "human behavior", "cognitive bias"],
    "luxury": ["luxury lifestyle", "billionaire", "expensive"],
    "scary": ["scary story", "true crime", "creepy"],
    "horror": ["horror story", "true crime", "paranormal"],
    "space": ["space discovery", "NASA", "universe"],
}

# Source weights for composite scoring
SOURCE_WEIGHTS = {
    "google_trends": 0.25,
    "youtube_search": 0.30,
    "reddit": 0.20,
    "ai_suggested": 0.15,
    "ai_assessment": 0.10,
}


class TrendResearcher:
    GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=US"

    def __init__(self):
        self.http = httpx.Client(timeout=30.0, follow_redirects=True)
        self.claude = None
        if settings.ANTHROPIC_API_KEY:
            self.claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def get_trending_topics(
        self, niche: str, count: int = 10
    ) -> list[TrendingTopic]:
        """Find trending topics for a niche from multiple sources."""
        all_topics = []

        # 1. Google Trends
        google_topics = self._fetch_google_trends()
        all_topics.extend(google_topics)

        # 2. YouTube Search (top recent videos in niche)
        youtube_topics = self._fetch_youtube_trending(niche)
        all_topics.extend(youtube_topics)

        # 3. Reddit trending
        reddit_topics = self._fetch_reddit_trending(niche)
        all_topics.extend(reddit_topics)

        # 4. Deduplicate by title similarity
        all_topics = self._deduplicate(all_topics)

        # 5. Filter and rank for niche using AI
        niche_topics = self._filter_for_niche(all_topics, niche)

        # 6. Score virality with AI (enhanced 12-dimension scoring)
        scored_topics = []
        current_trends = ", ".join(t.title for t in all_topics[:10])
        for topic in niche_topics[:count * 2]:
            scored = self._score_virality(topic, niche, current_trends)
            scored_topics.append(scored)

        # Sort by composite virality score
        scored_topics.sort(key=lambda t: t.virality_score, reverse=True)

        logger.info(
            f"Found {len(scored_topics)} trending topics for '{niche}' "
            f"(Google: {len(google_topics)}, YouTube: {len(youtube_topics)}, "
            f"Reddit: {len(reddit_topics)})"
        )
        return scored_topics[:count]

    def _fetch_google_trends(self) -> list[TrendingTopic]:
        """Fetch trending searches from Google Trends RSS feed."""
        topics = []
        try:
            feed = feedparser.parse(self.GOOGLE_TRENDS_RSS)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                if title:
                    topics.append(TrendingTopic(
                        title=title,
                        source="google_trends",
                    ))
            logger.info(f"Fetched {len(topics)} Google Trends topics")
        except Exception as e:
            logger.warning(f"Google Trends fetch failed: {e}")
        return topics

    def _fetch_youtube_trending(self, niche: str) -> list[TrendingTopic]:
        """Find top recent videos in the niche via YouTube Data API search."""
        topics = []

        # Get search keywords for this niche
        niche_lower = niche.lower()
        keywords = []
        for key, kws in NICHE_SEARCH_KEYWORDS.items():
            if key in niche_lower:
                keywords.extend(kws)
                break
        if not keywords:
            keywords = [niche]

        if not settings.YOUTUBE_CLIENT_ID:
            logger.debug("YouTube API not configured, skipping YouTube trend search")
            return topics

        try:
            for keyword in keywords[:2]:
                response = self.http.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": keyword,
                        "type": "video",
                        "order": "viewCount",
                        "publishedAfter": self._days_ago_iso(7),
                        "maxResults": 10,
                        "key": settings.YOUTUBE_CLIENT_ID,
                    },
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                for item in data.get("items", []):
                    title = item["snippet"]["title"]
                    topics.append(TrendingTopic(
                        title=title,
                        source="youtube_search",
                        related_queries=[keyword],
                    ))

            logger.info(f"Fetched {len(topics)} YouTube trending topics")
        except Exception as e:
            logger.warning(f"YouTube trending fetch failed: {e}")

        return topics

    def _fetch_reddit_trending(self, niche: str) -> list[TrendingTopic]:
        """Fetch top posts from niche-relevant subreddits (no API key needed)."""
        topics = []

        niche_lower = niche.lower()
        subreddits = []
        for key, subs in NICHE_SUBREDDITS.items():
            if key in niche_lower:
                subreddits.extend(subs)
                break
        if not subreddits:
            subreddits = ["popular"]

        for sub in subreddits[:3]:
            try:
                response = self.http.get(
                    f"https://www.reddit.com/r/{sub}/top.json",
                    params={"t": "week", "limit": 10},
                    headers={"User-Agent": "AutoTubeAI/1.0"},
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    title = post_data.get("title", "").strip()
                    score = post_data.get("score", 0)

                    if title and score > 100:
                        topics.append(TrendingTopic(
                            title=title,
                            source=f"reddit_r/{sub}",
                            related_queries=[sub],
                        ))

            except Exception as e:
                logger.debug(f"Reddit fetch failed for r/{sub}: {e}")
                continue

        logger.info(f"Fetched {len(topics)} Reddit trending topics")
        return topics

    def _deduplicate(self, topics: list[TrendingTopic]) -> list[TrendingTopic]:
        """Remove near-duplicate topics based on title similarity."""
        seen_titles = set()
        unique = []
        for topic in topics:
            normalized = topic.title.lower().strip()
            is_dup = False
            for seen in seen_titles:
                if normalized in seen or seen in normalized:
                    is_dup = True
                    break
            if not is_dup:
                seen_titles.add(normalized)
                unique.append(topic)
        return unique

    def _filter_for_niche(
        self, topics: list[TrendingTopic], niche: str
    ) -> list[TrendingTopic]:
        """Filter topics relevant to the given niche using AI."""
        if not self.claude or not topics:
            return topics

        topic_titles = [f"[{t.source}] {t.title}" for t in topics]

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": (
                        f"From these trending topics (with their sources), select the ones "
                        f"most relevant to the '{niche}' YouTube niche. For each selected topic, "
                        f"also suggest a specific YouTube video angle.\n\n"
                        f"Return ONLY relevant topic titles (without source tags), one per line. "
                        f"If fewer than 5 are relevant, suggest evergreen topics for this niche "
                        f"to fill up to 10 topics.\n\nTopics:\n"
                        + "\n".join(f"- {t}" for t in topic_titles)
                    ),
                }],
            )

            relevant_titles = set()
            for line in response.content[0].text.strip().split("\n"):
                cleaned = line.strip().lstrip("- •").strip()
                if cleaned:
                    relevant_titles.add(cleaned)

            filtered = []
            matched_titles = set()
            for topic in topics:
                if topic.title in relevant_titles:
                    filtered.append(topic)
                    matched_titles.add(topic.title)

            for title in relevant_titles - matched_titles:
                filtered.append(TrendingTopic(
                    title=title,
                    source="ai_suggested",
                    is_trending=False,
                ))

            return filtered

        except Exception as e:
            logger.warning(f"Niche filtering failed: {e}")
            return topics

    def _score_virality(
        self, topic: TrendingTopic, niche: str, current_trends: str
    ) -> TrendingTopic:
        """Score a topic's viral potential using Claude (12-dimension scoring)."""
        if not self.claude:
            topic.virality_score = 50
            return topic

        try:
            prompt = VIRALITY_SCORING_PROMPT.format(
                topic=topic.title,
                niche=niche,
                current_trends=current_trends,
            )

            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                topic.virality_score = min(100, max(0, int(data.get("overall_score", 50))))
                topic.reasoning = data.get("reasoning", "")
                topic.suggested_angle = data.get("recommended_angle", "")
                topic.suggested_title = data.get("suggested_title", "")
            else:
                topic.virality_score = 50

        except Exception as e:
            logger.debug(f"Virality scoring failed for '{topic.title}': {e}")
            topic.virality_score = 50

        return topic

    def get_seasonal_topics(self, niche: str, month: int) -> list[str]:
        """Get seasonal/evergreen topics for a niche and month."""
        if not self.claude:
            return []

        try:
            month_name = datetime(2024, month, 1).strftime("%B")
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Suggest 10 YouTube video topics for the '{niche}' niche "
                        f"that are particularly relevant in {month_name}. Consider "
                        f"seasonal events, holidays, and recurring trends. "
                        f"Return one topic per line, no numbering."
                    ),
                }],
            )

            topics = [
                line.strip().lstrip("- •").strip()
                for line in response.content[0].text.strip().split("\n")
                if line.strip()
            ]
            return topics[:10]

        except Exception as e:
            logger.warning(f"Seasonal topics failed: {e}")
            return []

    @staticmethod
    def _days_ago_iso(days: int) -> str:
        """Return ISO 8601 timestamp for N days ago."""
        dt = datetime.utcnow() - timedelta(days=days)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def __del__(self):
        try:
            self.http.close()
        except Exception:
            pass
