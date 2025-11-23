"""
YouTube Uploader Module
Upload videos to YouTube using YouTube Data API v3
"""
import logging
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config

logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeUploader:
    """Upload videos to YouTube"""
    
    def __init__(self):
        self.credentials = None
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube API"""
        token_file = Config.BASE_DIR / 'youtube_token.pickle'
        
        # Load existing credentials
        if token_file.exists():
            with open(token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing YouTube credentials...")
                self.credentials.refresh(Request())
            else:
                logger.info("Starting YouTube OAuth flow...")
                # This requires a credentials.json file from Google Cloud Console
                credentials_file = Config.BASE_DIR / 'youtube_credentials.json'
                
                if not credentials_file.exists():
                    logger.error(f"YouTube credentials file not found: {credentials_file}")
                    logger.error("Please download OAuth 2.0 credentials from Google Cloud Console")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file), SCOPES
                )
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
        
        # Build YouTube API client
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        logger.info("YouTube API authenticated successfully")
    
    def upload_video(
        self,
        video_path,
        title,
        description,
        tags=None,
        category_id='22',  # People & Blogs
        privacy_status='public',
        is_shorts=False
    ):
        """
        Upload a video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title (max 100 chars)
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: 'public', 'private', or 'unlisted'
            is_shorts: Whether this is a YouTube Short
        """
        if not self.youtube:
            logger.error("YouTube API not authenticated")
            return None
        
        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # Max 100 characters
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': True  # Important for kids content
                }
            }
            
            # Add #Shorts to title if it's a short
            if is_shorts and '#Shorts' not in body['snippet']['title']:
                body['snippet']['title'] = f"{body['snippet']['title']} #Shorts"
            
            # Prepare file upload
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Execute upload
            logger.info(f"Uploading video to YouTube: {title}")
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Video uploaded successfully: {video_url}")
            
            return {
                'video_id': video_id,
                'url': video_url,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error uploading video to YouTube: {e}")
            return None
    
    def upload_shorts(self, video_path, title, description, tags=None):
        """Upload a YouTube Short"""
        return self.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status='public',
            is_shorts=True
        )
    
    def upload_regular_video(self, video_path, title, description, tags=None):
        """Upload a regular YouTube video"""
        return self.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status='public',
            is_shorts=False
        )
    
    def get_video_details(self, video_id):
        """Get details of an uploaded video"""
        try:
            request = self.youtube.videos().list(
                part='snippet,status,statistics',
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return None
    
    def update_video_metadata(self, video_id, title=None, description=None, tags=None):
        """Update metadata of an existing video"""
        try:
            # Get current video details
            video = self.get_video_details(video_id)
            if not video:
                return False
            
            # Update fields
            if title:
                video['snippet']['title'] = title[:100]
            if description:
                video['snippet']['description'] = description
            if tags:
                video['snippet']['tags'] = tags
            
            # Update video
            request = self.youtube.videos().update(
                part='snippet',
                body=video
            )
            request.execute()
            
            logger.info(f"Updated video metadata for {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating video metadata: {e}")
            return False


if __name__ == "__main__":
    # Test YouTube uploader
    logging.basicConfig(level=logging.INFO)
    
    print("YouTube Uploader Module")
    print("=" * 50)
    print("\nTo use this module, you need:")
    print("1. Google Cloud Project with YouTube Data API v3 enabled")
    print("2. OAuth 2.0 credentials downloaded as 'youtube_credentials.json'")
    print("3. Place 'youtube_credentials.json' in the project root")
    print("\nSetup guide: https://developers.google.com/youtube/v3/quickstart/python")
    
    # Uncomment to test authentication
    # uploader = YouTubeUploader()
    # print("\nAuthentication successful!" if uploader.youtube else "Authentication failed")
