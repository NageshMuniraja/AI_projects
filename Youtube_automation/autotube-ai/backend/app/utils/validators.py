import re


def validate_youtube_channel_id(channel_id: str) -> bool:
    """Validate a YouTube channel ID format (UC + 22 chars)."""
    return bool(re.match(r"^UC[\w-]{22}$", channel_id))


def validate_youtube_video_id(video_id: str) -> bool:
    """Validate a YouTube video ID format (11 chars)."""
    return bool(re.match(r"^[\w-]{11}$", video_id))


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a string for use as a filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
    sanitized = re.sub(r"\s+", "_", sanitized)
    return sanitized[:max_length]


def truncate_title(title: str, max_length: int = 100) -> str:
    """Truncate a YouTube title to max length without cutting words."""
    if len(title) <= max_length:
        return title
    truncated = title[:max_length].rsplit(" ", 1)[0]
    return truncated if truncated else title[:max_length]
