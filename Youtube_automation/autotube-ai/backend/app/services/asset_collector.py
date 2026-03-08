"""Asset Collector Service — sources AI-generated video clips and stock footage.

Pipeline per asset:
1. Generate DALL-E 3 image (cinematic, topic-matched)
2. Convert image to dynamic video clip (Stability SVD or motion synthesis)
3. Fallback: stock video from Pexels/Pixabay

All assets are VIDEO CLIPS — no static images in the final output.
"""

import base64
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.file_manager import get_unique_path


@dataclass
class CollectedAsset:
    type: str  # "ai_video", "stock_video"
    source: str  # "dall_e_3", "pexels", "pixabay", "stability_svd"
    local_path: str
    source_url: str
    description: str
    attribution: str = ""
    duration_seconds: float = 0.0
    cost_usd: float = 0.0


@dataclass
class AssetCollection:
    assets: list[CollectedAsset] = field(default_factory=list)
    total_cost_usd: float = 0.0


DALLE_PROMPT_TEMPLATE = (
    "A photorealistic scene: {description}. "
    "Shot on Sony A7IV, 35mm lens, f/1.8 aperture. "
    "Cinematic color grading with teal and orange tones, "
    "volumetric god rays, shallow depth of field, "
    "dramatic rim lighting, ultra-sharp details, "
    "no text, no watermarks, no logos, no people's faces"
)


class AssetCollector:
    PEXELS_BASE = "https://api.pexels.com"
    PIXABAY_BASE = "https://pixabay.com/api"
    STABILITY_BASE = "https://api.stability.ai/v1"

    DALLE_COST_PER_IMAGE = 0.040
    STABILITY_COST_PER_IMAGE = 0.02
    MAX_PARALLEL_WORKERS = 3

    def __init__(self):
        self.pexels_key = settings.PEXELS_API_KEY
        self.pixabay_key = settings.PIXABAY_API_KEY
        self.stability_key = settings.STABILITY_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.http = httpx.Client(timeout=60.0)

        self.openai_client = None
        if self.openai_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_key)
            except ImportError:
                logger.warning("openai package not installed")

        self._video_generator = None

    @property
    def video_generator(self):
        if self._video_generator is None:
            from app.services.ai_video_generator import AIVideoGenerator
            self._video_generator = AIVideoGenerator()
        return self._video_generator

    def collect_assets_for_script(
        self,
        script_text: str,
        output_dir: Path | None = None,
        orientation: str = "landscape",
    ) -> AssetCollection:
        """Parse script for [B-ROLL: description] markers and collect video assets.

        All assets are converted to video clips — no static images in output.
        Uses parallel generation for speed (up to 3 concurrent DALL-E calls).
        """
        if output_dir is None:
            output_dir = settings.footage_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        markers = re.findall(r"\[B-ROLL:\s*(.+?)\]", script_text)
        collection = AssetCollection()

        if not markers:
            logger.warning("No B-ROLL markers found in script")
            return collection

        logger.info(f"Collecting {len(markers)} video assets (parallel, orientation={orientation})")

        # Parallel generation for speed
        with ThreadPoolExecutor(max_workers=self.MAX_PARALLEL_WORKERS) as executor:
            futures = {}
            for i, description in enumerate(markers):
                future = executor.submit(
                    self._collect_single_asset, description, output_dir, orientation
                )
                futures[future] = (i, description)

            for future in as_completed(futures):
                idx, desc = futures[future]
                try:
                    asset = future.result()
                    if asset:
                        collection.assets.append(asset)
                        collection.total_cost_usd += asset.cost_usd
                        logger.info(f"Asset {idx + 1}/{len(markers)}: {asset.type} ({asset.source})")
                    else:
                        logger.warning(f"No asset for: '{desc}'")
                except Exception as e:
                    logger.error(f"Asset generation failed for '{desc}': {e}")

        # Sort assets back to script order
        marker_order = {desc: i for i, desc in enumerate(markers)}
        collection.assets.sort(key=lambda a: marker_order.get(a.description, 999))

        logger.info(
            f"Collected {len(collection.assets)}/{len(markers)} video assets, "
            f"cost: ${collection.total_cost_usd:.4f}"
        )
        return collection

    def _collect_single_asset(
        self, description: str, output_dir: Path, orientation: str = "landscape"
    ) -> CollectedAsset | None:
        """Generate a single video asset — DALL-E image → video clip pipeline."""
        # 1. DALL-E 3 → Video clip (primary)
        if self.openai_client:
            asset = self._generate_dalle_video(description, output_dir, orientation)
            if asset:
                return asset

        # 2. Pexels stock video (fallback)
        if self.pexels_key:
            asset = self._search_pexels_video(description, output_dir)
            if asset:
                return asset

        # 3. Pixabay stock video
        if self.pixabay_key:
            asset = self._search_pixabay_video(description, output_dir)
            if asset:
                return asset

        return None

    # =========================================================================
    # DALL-E 3 IMAGE → VIDEO CLIP PIPELINE
    # =========================================================================

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=3, max=15))
    def _generate_dalle_video(
        self, description: str, output_dir: Path, orientation: str = "landscape"
    ) -> CollectedAsset | None:
        """Generate DALL-E 3 image, then convert to dynamic video clip."""
        try:
            prompt = DALLE_PROMPT_TEMPLATE.format(description=description)

            if orientation == "portrait":
                size = "1024x1792"
                resolution = (1080, 1920)
            else:
                size = "1792x1024"
                resolution = (1920, 1080)

            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
                response_format="b64_json",
            )

            image_data = base64.b64decode(response.data[0].b64_json)
            image_path = get_unique_path(output_dir, "dalle3", ".png")
            image_path.write_bytes(image_data)

            total_cost = self.DALLE_COST_PER_IMAGE

            # Convert image to video clip
            video_path, video_cost = self.video_generator.generate_video_clip(
                str(image_path),
                duration=5.0,
                resolution=resolution,
            )
            total_cost += video_cost

            logger.info(f"AI video clip: {video_path} ({size})")

            return CollectedAsset(
                type="ai_video",
                source="dall_e_3",
                local_path=video_path,
                source_url="",
                description=description,
                duration_seconds=5.0,
                cost_usd=total_cost,
            )

        except Exception as e:
            logger.warning(f"DALL-E video pipeline failed for '{description}': {e}")
        return None

    # =========================================================================
    # STOCK VIDEO SOURCES (fallbacks)
    # =========================================================================

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    def _search_pexels_video(
        self, query: str, output_dir: Path
    ) -> CollectedAsset | None:
        """Search and download a stock video from Pexels."""
        try:
            resp = self.http.get(
                f"{self.PEXELS_BASE}/videos/search",
                params={"query": query, "per_page": 5, "orientation": "landscape"},
                headers={"Authorization": self.pexels_key},
            )
            resp.raise_for_status()
            data = resp.json()

            videos = data.get("videos", [])
            if not videos:
                return None

            for video in videos:
                for vf in video.get("video_files", []):
                    if (
                        vf.get("width", 0) >= 1280
                        and vf.get("file_type") == "video/mp4"
                    ):
                        download_url = vf["link"]
                        output_path = get_unique_path(output_dir, "pexels", ".mp4")
                        self._download_file(download_url, output_path)

                        return CollectedAsset(
                            type="stock_video",
                            source="pexels",
                            local_path=str(output_path),
                            source_url=video.get("url", ""),
                            description=query,
                            attribution=f"Video by {video.get('user', {}).get('name', 'Unknown')} from Pexels",
                            duration_seconds=video.get("duration", 10),
                        )
        except Exception as e:
            logger.debug(f"Pexels video search failed for '{query}': {e}")
        return None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    def _search_pixabay_video(
        self, query: str, output_dir: Path
    ) -> CollectedAsset | None:
        """Search and download a stock video from Pixabay."""
        try:
            resp = self.http.get(
                f"{self.PIXABAY_BASE}/videos/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "per_page": 5,
                    "min_width": 1280,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("hits", [])
            if not hits:
                return None

            video = hits[0]
            video_url = video.get("videos", {}).get("large", {}).get("url")
            if not video_url:
                video_url = video.get("videos", {}).get("medium", {}).get("url")
            if not video_url:
                return None

            output_path = get_unique_path(output_dir, "pixabay", ".mp4")
            self._download_file(video_url, output_path)

            return CollectedAsset(
                type="stock_video",
                source="pixabay",
                local_path=str(output_path),
                source_url=video.get("pageURL", ""),
                description=query,
                attribution=f"Video by {video.get('user', 'Unknown')} from Pixabay",
                duration_seconds=video.get("duration", 10),
            )
        except Exception as e:
            logger.debug(f"Pixabay video search failed for '{query}': {e}")
        return None

    def _download_file(self, url: str, output_path: Path) -> None:
        """Download a file from URL to local path."""
        with self.http.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

    def __del__(self):
        try:
            self.http.close()
        except Exception:
            pass
