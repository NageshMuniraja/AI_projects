#!/usr/bin/env python3
"""One-time setup script for YouTube OAuth2 credentials.

Usage:
    1. Go to Google Cloud Console → APIs & Services → Credentials
    2. Create OAuth 2.0 Client ID (Desktop application)
    3. Download the JSON as 'client_secret.json' into this directory
    4. Run: python scripts/setup_youtube_oauth.py
    5. Follow the browser prompt to authorize
    6. The refresh token will be printed — add it to your .env file
"""

import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Install dependencies first: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CLIENT_SECRET_FILE = Path(__file__).parent / "client_secret.json"


def main():
    if not CLIENT_SECRET_FILE.exists():
        print(f"Error: {CLIENT_SECRET_FILE} not found.")
        print("Download OAuth 2.0 credentials from Google Cloud Console.")
        print("Save as 'client_secret.json' in the scripts/ directory.")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    credentials = flow.run_local_server(port=8090)

    print("\n" + "=" * 60)
    print("OAuth setup complete!")
    print("=" * 60)
    print(f"\nAccess Token:  {credentials.token[:20]}...")
    print(f"Refresh Token: {credentials.refresh_token}")
    print(f"Client ID:     {credentials.client_id}")
    print(f"Client Secret: {credentials.client_secret[:10]}...")
    print("\nAdd these to your .env file:")
    print(f"  YOUTUBE_CLIENT_ID={credentials.client_id}")
    print(f"  YOUTUBE_CLIENT_SECRET={credentials.client_secret}")
    print(f"  # Store refresh token encrypted in the channel DB record")
    print("=" * 60)

    # Save credentials to a JSON file for reference
    creds_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": SCOPES,
    }
    output_file = Path(__file__).parent / "youtube_token.json"
    with open(output_file, "w") as f:
        json.dump(creds_data, f, indent=2)
    print(f"\nCredentials saved to: {output_file}")
    print("WARNING: Keep this file secure and DO NOT commit it to git!")


if __name__ == "__main__":
    main()
