"""YouTube OAuth2 authentication helper with multi-channel support."""

import json

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger

from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def get_fernet() -> Fernet:
    """Get Fernet cipher using the app secret key."""
    # Derive a 32-byte key from SECRET_KEY
    import hashlib
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    import base64
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_credentials(credentials_dict: dict) -> str:
    """Encrypt OAuth credentials for storage in DB."""
    fernet = get_fernet()
    data = json.dumps(credentials_dict).encode()
    return fernet.encrypt(data).decode()


def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt OAuth credentials from DB storage."""
    fernet = get_fernet()
    data = fernet.decrypt(encrypted.encode())
    return json.loads(data.decode())


def build_youtube_client(encrypted_credentials: str):
    """Build an authenticated YouTube API client from encrypted credentials."""
    creds_data = decrypt_credentials(encrypted_credentials)

    credentials = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data.get("client_id", settings.YOUTUBE_CLIENT_ID),
        client_secret=creds_data.get("client_secret", settings.YOUTUBE_CLIENT_SECRET),
        scopes=creds_data.get("scopes", SCOPES),
    )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        logger.info("Refreshing YouTube OAuth token...")
        credentials.refresh(Request())

        # Update stored token
        creds_data["token"] = credentials.token
        # Re-encrypt and update would happen at the caller level

    youtube = build("youtube", "v3", credentials=credentials)
    return youtube, credentials


def build_youtube_analytics_client(encrypted_credentials: str):
    """Build an authenticated YouTube Analytics API client."""
    creds_data = decrypt_credentials(encrypted_credentials)

    credentials = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data.get("client_id", settings.YOUTUBE_CLIENT_ID),
        client_secret=creds_data.get("client_secret", settings.YOUTUBE_CLIENT_SECRET),
        scopes=creds_data.get("scopes", SCOPES),
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    analytics = build("youtubeAnalytics", "v2", credentials=credentials)
    return analytics, credentials
