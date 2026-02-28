"""SEO Optimizer Service — generates optimized titles, descriptions, and tags using Claude."""

import json
import re
from dataclasses import dataclass, field

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.prompts import SEO_DESCRIPTION_PROMPT, SEO_TAGS_PROMPT, SEO_TITLE_PROMPT


@dataclass
class VideoMetadata:
    titles: list[str] = field(default_factory=list)
    selected_title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    category_id: str = "22"
    cost_usd: float = 0.0


class SEOOptimizer:
    INPUT_COST_PER_M = 3.0
    OUTPUT_COST_PER_M = 15.0

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY required for SEO optimization")
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    def optimize_metadata(
        self,
        topic: str,
        script: str,
        niche: str,
        target_audience: str = "general audience",
    ) -> VideoMetadata:
        """Generate fully optimized video metadata."""
        metadata = VideoMetadata()
        total_cost = 0.0

        # Generate titles
        titles, cost = self._generate_titles(topic, niche, target_audience)
        metadata.titles = titles
        metadata.selected_title = titles[0] if titles else topic[:60]
        total_cost += cost

        # Generate description
        desc, cost = self._generate_description(
            metadata.selected_title, topic, script
        )
        metadata.description = desc
        total_cost += cost

        # Generate tags
        tags, cost = self._generate_tags(topic, niche)
        metadata.tags = tags
        total_cost += cost

        # Generate hashtags (top 3 from tags)
        metadata.hashtags = [f"#{t.replace(' ', '')}" for t in tags[:3]]

        # Set category based on niche
        metadata.category_id = self._niche_to_category(niche)
        metadata.cost_usd = total_cost

        logger.info(f"SEO optimized: '{metadata.selected_title}', "
                     f"{len(tags)} tags, ${total_cost:.4f}")

        return metadata

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_titles(
        self, topic: str, niche: str, target_audience: str
    ) -> tuple[list[str], float]:
        """Generate ranked title options."""
        prompt = SEO_TITLE_PROMPT.format(
            topic=topic, niche=niche, target_audience=target_audience
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        cost = (
            (response.usage.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (response.usage.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

        # Parse numbered list
        titles = []
        for line in text.strip().split("\n"):
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
            cleaned = cleaned.strip('"').strip("'").strip()
            if cleaned and len(cleaned) <= 100:
                titles.append(cleaned)

        return titles[:5], cost

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_description(
        self, title: str, topic: str, script: str
    ) -> tuple[str, float]:
        """Generate an SEO-optimized description."""
        # Truncate script to avoid huge prompts
        script_excerpt = script[:2000] if len(script) > 2000 else script

        prompt = SEO_DESCRIPTION_PROMPT.format(
            title=title, topic=topic
        ) + f"\n\nScript excerpt for context:\n{script_excerpt}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        cost = (
            (response.usage.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (response.usage.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

        return response.content[0].text.strip(), cost

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _generate_tags(self, topic: str, niche: str) -> tuple[list[str], float]:
        """Generate 30 relevant tags."""
        prompt = SEO_TAGS_PROMPT.format(topic=topic, niche=niche)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        cost = (
            (response.usage.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (response.usage.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

        text = response.content[0].text
        tags = [t.strip().strip('"').strip("'") for t in text.split(",")]
        tags = [t for t in tags if t and len(t) <= 30]

        return tags[:30], cost

    @staticmethod
    def _niche_to_category(niche: str) -> str:
        """Map niche name to YouTube category ID."""
        niche_lower = niche.lower()
        mapping = {
            "tech": "28",        # Science & Technology
            "ai": "28",
            "finance": "22",     # People & Blogs
            "motivation": "22",
            "history": "27",     # Education
            "health": "27",
            "science": "28",
            "gaming": "20",      # Gaming
            "psychology": "27",
            "luxury": "22",
            "scary": "24",       # Entertainment
            "horror": "24",
            "space": "28",
        }
        for keyword, cat_id in mapping.items():
            if keyword in niche_lower:
                return cat_id
        return "22"  # Default: People & Blogs
