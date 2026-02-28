"""Content Strategy Service — AI-driven content planning that learns from analytics."""

from dataclasses import dataclass, field
from datetime import date, timedelta

import anthropic
from loguru import logger
from sqlalchemy import func, select
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.database import async_session_factory
from app.models.analytics import VideoAnalytics
from app.models.channel import Channel
from app.models.schedule import CalendarStatus, ContentCalendar
from app.models.video import Video, VideoStatus
from app.utils.prompts import CONTENT_STRATEGY_PROMPT


@dataclass
class TopicSuggestion:
    title: str
    reasoning: str
    virality_score: int
    is_trending: bool
    is_evergreen: bool


@dataclass
class TimeSlot:
    day_of_week: int  # 0=Monday
    hour: int
    estimated_views_multiplier: float = 1.0


class ContentStrategy:
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY required for content strategy")
        self.claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def suggest_next_topics(
        self, channel_id: int, count: int = 10
    ) -> list[TopicSuggestion]:
        """Suggest next topics based on performance data and niche."""
        async with async_session_factory() as db:
            channel = await db.get(Channel, channel_id)
            if not channel:
                return []

            # Get top performing videos (by views)
            top_result = await db.execute(
                select(
                    Video.topic,
                    Video.title,
                    func.sum(VideoAnalytics.views).label("total_views"),
                )
                .join(VideoAnalytics, VideoAnalytics.video_id == Video.id)
                .where(Video.channel_id == channel_id)
                .group_by(Video.id, Video.topic, Video.title)
                .order_by(func.sum(VideoAnalytics.views).desc())
                .limit(10)
            )
            top_videos = top_result.all()

            # Get recent topics (last 30 days) to avoid repetition
            recent_result = await db.execute(
                select(Video.topic)
                .where(Video.channel_id == channel_id)
                .where(Video.created_at >= func.now() - timedelta(days=30))
            )
            recent_topics = [r[0] for r in recent_result.all() if r[0]]

        # Format data for AI prompt
        top_videos_data = "\n".join(
            f"- '{v.title or v.topic}' — {v.total_views} views"
            for v in top_videos
        ) or "No published videos yet"

        recent_str = "\n".join(f"- {t}" for t in recent_topics) or "None"

        return self._generate_suggestions(
            channel.niche, top_videos_data, recent_str, count
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_suggestions(
        self,
        niche: str,
        top_videos_data: str,
        recent_topics: str,
        count: int,
    ) -> list[TopicSuggestion]:
        """Use Claude to generate topic suggestions."""
        prompt = CONTENT_STRATEGY_PROMPT.format(
            niche=niche,
            top_videos_data=top_videos_data,
            recent_topics=recent_topics,
        )

        response = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        suggestions = self._parse_suggestions(text)
        return suggestions[:count]

    def _parse_suggestions(self, text: str) -> list[TopicSuggestion]:
        """Parse AI response into TopicSuggestion objects."""
        suggestions = []

        # Try to parse structured output
        lines = text.strip().split("\n")
        current_topic = None
        current_reasoning = ""
        current_score = 50
        current_trending = False
        current_evergreen = False

        for line in lines:
            line = line.strip()
            if not line:
                if current_topic:
                    suggestions.append(TopicSuggestion(
                        title=current_topic,
                        reasoning=current_reasoning,
                        virality_score=current_score,
                        is_trending=current_trending,
                        is_evergreen=current_evergreen,
                    ))
                    current_topic = None
                    current_reasoning = ""
                    current_score = 50
                    current_trending = False
                    current_evergreen = False
                continue

            # Detect topic line (numbered or starts with title-like pattern)
            import re
            topic_match = re.match(r"^\d+[\.\)]\s*(.+)", line)
            if topic_match:
                if current_topic:
                    suggestions.append(TopicSuggestion(
                        title=current_topic,
                        reasoning=current_reasoning,
                        virality_score=current_score,
                        is_trending=current_trending,
                        is_evergreen=current_evergreen,
                    ))
                current_topic = topic_match.group(1).strip().strip('"').strip("*")
                current_reasoning = ""
                current_score = 50
                continue

            # Detect score
            score_match = re.search(r"score[:\s]*(\d+)", line, re.IGNORECASE)
            if score_match:
                current_score = min(100, max(0, int(score_match.group(1))))

            # Detect trending/evergreen
            if "trending" in line.lower():
                current_trending = True
            if "evergreen" in line.lower():
                current_evergreen = True

            if current_topic:
                current_reasoning += line + " "

        # Don't forget the last one
        if current_topic:
            suggestions.append(TopicSuggestion(
                title=current_topic,
                reasoning=current_reasoning.strip(),
                virality_score=current_score,
                is_trending=current_trending,
                is_evergreen=current_evergreen,
            ))

        return suggestions

    async def generate_content_calendar(
        self, channel_id: int, weeks: int = 4
    ) -> list[dict]:
        """Generate a content calendar for the specified number of weeks."""
        suggestions = await self.suggest_next_topics(channel_id, count=weeks * 3)

        async with async_session_factory() as db:
            channel = await db.get(Channel, channel_id)
            frequency = channel.posting_frequency if channel else "3x_week"

        # Determine posting days
        if frequency == "daily":
            posts_per_week = 7
        elif frequency == "3x_week":
            posts_per_week = 3
        else:
            posts_per_week = 1

        calendar_entries = []
        today = date.today()
        suggestion_idx = 0

        for week in range(weeks):
            for day_offset in range(0, 7, max(1, 7 // posts_per_week)):
                if suggestion_idx >= len(suggestions):
                    break

                scheduled = today + timedelta(weeks=week, days=day_offset)
                suggestion = suggestions[suggestion_idx]

                entry = {
                    "channel_id": channel_id,
                    "topic": suggestion.title,
                    "scheduled_date": scheduled.isoformat(),
                    "priority_score": suggestion.virality_score,
                    "is_trending": suggestion.is_trending,
                    "is_evergreen": suggestion.is_evergreen,
                }
                calendar_entries.append(entry)
                suggestion_idx += 1

        # Save to DB
        async with async_session_factory() as db:
            for entry in calendar_entries:
                cal = ContentCalendar(
                    channel_id=entry["channel_id"],
                    topic=entry["topic"],
                    scheduled_date=date.fromisoformat(entry["scheduled_date"]),
                    priority_score=entry["priority_score"],
                    is_trending=entry["is_trending"],
                    is_evergreen=entry["is_evergreen"],
                    status=CalendarStatus.PLANNED,
                )
                db.add(cal)
            await db.commit()

        logger.info(f"Generated {len(calendar_entries)} calendar entries for {weeks} weeks")
        return calendar_entries

    def get_optimal_post_times(self, niche: str) -> list[TimeSlot]:
        """Return optimal posting times based on niche (static defaults for now)."""
        # Data-backed defaults for YouTube posting (EST/PST prime time)
        return [
            TimeSlot(day_of_week=0, hour=14, estimated_views_multiplier=1.1),  # Monday 2PM
            TimeSlot(day_of_week=2, hour=15, estimated_views_multiplier=1.2),  # Wednesday 3PM
            TimeSlot(day_of_week=4, hour=14, estimated_views_multiplier=1.15),  # Friday 2PM
            TimeSlot(day_of_week=5, hour=10, estimated_views_multiplier=1.3),  # Saturday 10AM
            TimeSlot(day_of_week=6, hour=10, estimated_views_multiplier=1.25),  # Sunday 10AM
        ]
