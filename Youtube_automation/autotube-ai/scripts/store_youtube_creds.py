#!/usr/bin/env python3
"""Store YouTube OAuth credentials from .env into the channel DB record.

Run inside Docker:
    docker compose exec backend python /app/../scripts/store_youtube_creds.py [channel_id]

Or from the backend container:
    python scripts/store_youtube_creds.py [channel_id]
"""

import asyncio
import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


async def main():
    from app.config import settings
    from app.database import async_session_factory
    from app.models.channel import Channel
    from app.utils.youtube_auth import encrypt_credentials

    channel_id = int(sys.argv[1]) if len(sys.argv) > 1 else None

    # Build credentials dict from env vars
    creds = {
        "refresh_token": settings.YOUTUBE_REFRESH_TOKEN,
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "client_secret": settings.YOUTUBE_CLIENT_SECRET,
        "token": None,
        "scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ],
    }

    if not creds["refresh_token"]:
        print("ERROR: YOUTUBE_REFRESH_TOKEN is not set in .env")
        sys.exit(1)

    if not creds["client_id"] or not creds["client_secret"]:
        print("ERROR: YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET is not set in .env")
        sys.exit(1)

    encrypted = encrypt_credentials(creds)
    print(f"Encrypted credentials: {encrypted[:50]}...")

    async with async_session_factory() as db:
        if channel_id:
            channel = await db.get(Channel, channel_id)
            if not channel:
                print(f"ERROR: Channel {channel_id} not found")
                sys.exit(1)
        else:
            # Find the first active channel
            from sqlalchemy import select
            result = await db.execute(select(Channel).where(Channel.is_active == True).limit(1))
            channel = result.scalar_one_or_none()
            if not channel:
                print("ERROR: No active channels found in database")
                sys.exit(1)

        channel.oauth_credentials_encrypted = encrypted
        await db.commit()
        print(f"YouTube OAuth credentials stored for channel '{channel.name}' (id={channel.id})")


if __name__ == "__main__":
    asyncio.run(main())
