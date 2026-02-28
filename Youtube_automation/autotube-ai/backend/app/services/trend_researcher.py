"""Trend Researcher Service — finds viral topics using Google Trends, YouTube search, and AI scoring."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime

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


@dataclass
class VideoIdea:
    title: str
    channel_url: str
    views: int = 0
    published_at: str = ""


class TrendResearcher:
    GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=US"

    def __init__(self):
        self.http = httpx.Client(timeout=30.0)
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

        # 2. Filter and rank for niche
        niche_topics = self._filter_for_niche(all_topics, niche)

        # 3. Score virality with AI
        scored_topics = []
        for topic in niche_topics[:count * 2]:  # Score more than needed, then pick top
            scored = self._score_virality(topic, niche)
            scored_topics.append(scored)

        # Sort by virality score
        scored_topics.sort(key=lambda t: t.virality_score, reverse=True)

        logger.info(f"Found {len(scored_topics)} trending topics for '{niche}'")
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

    def _filter_for_niche(
        self, topics: list[TrendingTopic], niche: str
    ) -> list[TrendingTopic]:
        """Filter topics relevant to the given niche using AI."""
        if not self.claude or not topics:
            return topics

        topic_titles = [t.title for t in topics]

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": (
                        f"From these trending topics, select the ones most relevant to "
                        f"the '{niche}' YouTube niche. Return ONLY relevant topic titles, "
                        f"one per line. If none are relevant, suggest 5 evergreen topics "
                        f"for this niche instead.\n\nTopics:\n"
                        + "\n".join(f"- {t}" for t in topic_titles)
                    ),
                }],
            )

            relevant_titles = set()
            for line in response.content[0].text.strip().split("\n"):
                cleaned = line.strip().lstrip("- •").strip()
                if cleaned:
                    relevant_titles.add(cleaned)

            # Match back to existing topics or create new ones
            filtered = []
            matched_titles = set()
            for topic in topics:
                if topic.title in relevant_titles:
                    filtered.append(topic)
                    matched_titles.add(topic.title)

            # Add suggested topics that weren't in original list
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
        self, topic: TrendingTopic, niche: str
    ) -> TrendingTopic:
        """Score a topic's viral potential using Claude."""
        if not self.claude:
            topic.virality_score = 50
            return topic

        try:
            prompt = VIRALITY_SCORING_PROMPT.format(
                topic=topic.title,
                niche=niche,
                current_trends="(from Google Trends)",
            )

            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()

            # Parse JSON response
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                topic.virality_score = min(100, max(0, int(data.get("score", 50))))
                topic.reasoning = data.get("reasoning", "")
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

    def __del__(self):
        try:
            self.http.close()
        except Exception:
            pass
