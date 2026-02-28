"""Asset Collector Service — sources stock footage and AI-generated images."""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.file_manager import get_unique_path


@dataclass
class CollectedAsset:
    type: str  # "stock_video", "ai_image", "stock_image"
    source: str  # "pexels", "pixabay", "stability_ai"
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


class AssetCollector:
    PEXELS_BASE = "https://api.pexels.com"
    PIXABAY_BASE = "https://pixabay.com/api"
    STABILITY_BASE = "https://api.stability.ai/v1"
    # Stability AI pricing: ~$0.02 per image
    STABILITY_COST_PER_IMAGE = 0.02

    def __init__(self):
        self.pexels_key = settings.PEXELS_API_KEY
        self.pixabay_key = settings.PIXABAY_API_KEY
        self.stability_key = settings.STABILITY_API_KEY
        self.http = httpx.Client(timeout=60.0)

    def collect_assets_for_script(
        self,
        script_text: str,
        output_dir: Path | None = None,
    ) -> AssetCollection:
        """Parse script for [B-ROLL: description] markers and collect assets."""
        if output_dir is None:
            output_dir = settings.footage_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        markers = re.findall(r"\[B-ROLL:\s*(.+?)\]", script_text)
        collection = AssetCollection()

        if not markers:
            logger.warning("No B-ROLL markers found in script")
            return collection

        logger.info(f"Collecting assets for {len(markers)} B-ROLL markers")

        for i, description in enumerate(markers):
            logger.info(f"Asset {i + 1}/{len(markers)}: '{description}'")
            asset = self._collect_single_asset(description, output_dir)
            if asset:
                collection.assets.append(asset)
                collection.total_cost_usd += asset.cost_usd
            else:
                logger.warning(f"No asset found for: '{description}'")

        logger.info(
            f"Collected {len(collection.assets)}/{len(markers)} assets, "
            f"cost: ${collection.total_cost_usd:.4f}"
        )
        return collection

    def _collect_single_asset(
        self, description: str, output_dir: Path
    ) -> CollectedAsset | None:
        """Try to collect a single asset from all sources in priority order."""
        # 1. Try Pexels stock video
        if self.pexels_key:
            asset = self._search_pexels_video(description, output_dir)
            if asset:
                return asset

        # 2. Try Pixabay stock video
        if self.pixabay_key:
            asset = self._search_pixabay_video(description, output_dir)
            if asset:
                return asset

        # 3. Try Pexels stock image
        if self.pexels_key:
            asset = self._search_pexels_image(description, output_dir)
            if asset:
                return asset

        # 4. Generate AI image
        if self.stability_key:
            asset = self._generate_stability_image(description, output_dir)
            if asset:
                return asset

        return None

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

            # Pick the first video with a suitable file
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

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    def _search_pexels_image(
        self, query: str, output_dir: Path
    ) -> CollectedAsset | None:
        """Search and download a stock image from Pexels."""
        try:
            resp = self.http.get(
                f"{self.PEXELS_BASE}/v1/search",
                params={"query": query, "per_page": 3, "orientation": "landscape"},
                headers={"Authorization": self.pexels_key},
            )
            resp.raise_for_status()
            data = resp.json()

            photos = data.get("photos", [])
            if not photos:
                return None

            photo = photos[0]
            image_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
            if not image_url:
                return None

            output_path = get_unique_path(output_dir, "pexels_img", ".jpg")
            self._download_file(image_url, output_path)

            return CollectedAsset(
                type="stock_image",
                source="pexels",
                local_path=str(output_path),
                source_url=photo.get("url", ""),
                description=query,
                attribution=f"Photo by {photo.get('photographer', 'Unknown')} from Pexels",
            )
        except Exception as e:
            logger.debug(f"Pexels image search failed for '{query}': {e}")
        return None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    def _generate_stability_image(
        self, description: str, output_dir: Path
    ) -> CollectedAsset | None:
        """Generate an AI image using Stability AI REST API."""
        try:
            resp = self.http.post(
                f"{self.STABILITY_BASE}/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "text_prompts": [
                        {"text": f"{description}, cinematic, 4K, professional photography", "weight": 1}
                    ],
                    "cfg_scale": 7,
                    "width": 1344,
                    "height": 768,
                    "steps": 30,
                    "samples": 1,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

            artifacts = data.get("artifacts", [])
            if not artifacts:
                return None

            import base64
            image_data = base64.b64decode(artifacts[0]["base64"])
            output_path = get_unique_path(output_dir, "ai_img", ".png")
            output_path.write_bytes(image_data)

            return CollectedAsset(
                type="ai_image",
                source="stability_ai",
                local_path=str(output_path),
                source_url="",
                description=description,
                cost_usd=self.STABILITY_COST_PER_IMAGE,
            )
        except Exception as e:
            logger.debug(f"Stability AI image generation failed: {e}")
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
