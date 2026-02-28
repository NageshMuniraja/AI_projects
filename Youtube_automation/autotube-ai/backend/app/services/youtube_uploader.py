"""YouTube Uploader Service — uploads videos via YouTube Data API v3."""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.utils.youtube_auth import build_youtube_client


@dataclass
class UploadResult:
    video_id: str
    url: str
    title: str
    status: str
    quota_cost: int = 1600  # Upload costs 1600 quota units


class YouTubeUploader:
    # YouTube API quota: 10,000 units/day, uploads cost 1600 each
    UPLOAD_QUOTA_COST = 1600

    def __init__(self, encrypted_credentials: str):
        self.youtube, self.credentials = build_youtube_client(encrypted_credentials)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=5, min=10, max=120))
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str = "22",
        privacy_status: str = "private",
        publish_at: datetime | None = None,
        thumbnail_path: str | None = None,
    ) -> UploadResult:
        """Upload a video to YouTube with metadata."""
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Build request body
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": (tags or [])[:30],
                "categoryId": category_id,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Schedule publish time
        if publish_at and privacy_status == "private":
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = publish_at.isoformat()

        # Prepare media upload (resumable)
        media = MediaFileUpload(
            video_path,
            chunksize=256 * 1024,  # 256KB chunks
            resumable=True,
            mimetype="video/mp4",
        )

        logger.info(f"Uploading to YouTube: '{title}' ({privacy_status})")

        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        # Execute upload with progress tracking
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")

        video_id = response["id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(f"Video uploaded: {video_url}")

        # Set thumbnail if provided
        if thumbnail_path and Path(thumbnail_path).exists():
            self._set_thumbnail(video_id, thumbnail_path)

        return UploadResult(
            video_id=video_id,
            url=video_url,
            title=title,
            status=privacy_status,
        )

    def _set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Set a custom thumbnail for a video."""
        try:
            media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ).execute()
            logger.info(f"Thumbnail set for video {video_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set thumbnail: {e}")
            return False

    def schedule_publish(
        self, video_id: str, publish_at: datetime
    ) -> bool:
        """Schedule a private video for future publishing."""
        try:
            self.youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": "private",
                        "publishAt": publish_at.isoformat(),
                    },
                },
            ).execute()
            logger.info(f"Scheduled video {video_id} for {publish_at}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule publish: {e}")
            return False

    def add_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """Add a video to a YouTube playlist."""
        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            logger.info(f"Added video {video_id} to playlist {playlist_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to add to playlist: {e}")
            return False

    def get_video_status(self, video_id: str) -> dict | None:
        """Get the current status of an uploaded video."""
        try:
            response = self.youtube.videos().list(
                part="status,statistics,snippet",
                id=video_id,
            ).execute()

            items = response.get("items", [])
            if items:
                return items[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get video status: {e}")
            return None
