"""
Instagram Uploader Module
Upload reels to Instagram using Instagram Graph API
"""
import logging
import requests
import time
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class InstagramUploader:
    """Upload reels to Instagram Business/Creator accounts"""
    
    def __init__(self):
        self.access_token = Config.INSTAGRAM_ACCESS_TOKEN
        self.user_id = Config.INSTAGRAM_USER_ID
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def upload_reel(
        self,
        video_path,
        caption,
        cover_image_url=None,
        share_to_feed=True
    ):
        """
        Upload a reel to Instagram
        
        Args:
            video_path: Path to video file (must be publicly accessible URL or upload to hosting)
            caption: Caption for the reel (max 2200 chars)
            cover_image_url: Optional cover image URL
            share_to_feed: Whether to share to main feed
        
        Note: Instagram API requires video to be accessible via URL
        You'll need to host the video temporarily (e.g., on your server, S3, etc.)
        """
        if not self.access_token or not self.user_id:
            logger.error("Instagram credentials not configured")
            return None
        
        try:
            # Step 1: Upload video to a hosting service and get URL
            # (This is a placeholder - you'll need to implement actual hosting)
            video_url = self._get_video_url(video_path)
            
            if not video_url:
                logger.error("Could not get video URL for Instagram upload")
                return None
            
            # Step 2: Create media container
            container_id = self._create_reel_container(
                video_url,
                caption,
                cover_image_url,
                share_to_feed
            )
            
            if not container_id:
                logger.error("Failed to create reel container")
                return None
            
            # Step 3: Publish reel
            result = self._publish_reel(container_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading reel to Instagram: {e}")
            return None
    
    def _get_video_url(self, video_path):
        """
        Get publicly accessible URL for video
        
        You need to implement this based on your hosting solution:
        - Upload to AWS S3 and get presigned URL
        - Upload to your own server
        - Use a temporary hosting service
        
        For testing, you can manually upload and provide URL
        """
        logger.warning("Video hosting not implemented - provide video URL manually")
        # Placeholder - return None or implement actual hosting
        return None
    
    def _create_reel_container(self, video_url, caption, cover_url=None, share_to_feed=True):
        """Create a reel media container"""
        endpoint = f"{self.base_url}/{self.user_id}/media"
        
        params = {
            'access_token': self.access_token,
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption[:2200],  # Max 2200 characters
            'share_to_feed': share_to_feed
        }
        
        if cover_url:
            params['cover_url'] = cover_url
        
        try:
            logger.info("Creating Instagram reel container...")
            response = requests.post(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            container_id = data.get('id')
            
            logger.info(f"Container created: {container_id}")
            
            # Wait for container to be ready
            if container_id:
                self._wait_for_container(container_id)
            
            return container_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating reel container: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return None
    
    def _wait_for_container(self, container_id, max_wait=300):
        """Wait for container to be ready for publishing"""
        endpoint = f"{self.base_url}/{container_id}"
        params = {
            'access_token': self.access_token,
            'fields': 'status_code'
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                
                data = response.json()
                status = data.get('status_code')
                
                logger.info(f"Container status: {status}")
                
                if status == 'FINISHED':
                    logger.info("Container ready for publishing")
                    return True
                elif status == 'ERROR':
                    logger.error("Container processing failed")
                    return False
                
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking container status: {e}")
                return False
        
        logger.error("Container processing timed out")
        return False
    
    def _publish_reel(self, container_id):
        """Publish the reel"""
        endpoint = f"{self.base_url}/{self.user_id}/media_publish"
        
        params = {
            'access_token': self.access_token,
            'creation_id': container_id
        }
        
        try:
            logger.info("Publishing reel to Instagram...")
            response = requests.post(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            media_id = data.get('id')
            
            logger.info(f"Reel published successfully: {media_id}")
            
            # Get permalink
            permalink = self._get_media_permalink(media_id)
            
            return {
                'media_id': media_id,
                'permalink': permalink
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error publishing reel: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return None
    
    def _get_media_permalink(self, media_id):
        """Get the permalink for published media"""
        endpoint = f"{self.base_url}/{media_id}"
        params = {
            'access_token': self.access_token,
            'fields': 'permalink'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('permalink', '')
            
        except Exception as e:
            logger.error(f"Error getting permalink: {e}")
            return ''
    
    def get_account_info(self):
        """Get Instagram account information"""
        endpoint = f"{self.base_url}/{self.user_id}"
        params = {
            'access_token': self.access_token,
            'fields': 'id,username,account_type,media_count'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def verify_credentials(self):
        """Verify Instagram API credentials"""
        info = self.get_account_info()
        
        if info:
            logger.info(f"Instagram account verified: @{info.get('username')}")
            logger.info(f"Account type: {info.get('account_type')}")
            logger.info(f"Media count: {info.get('media_count')}")
            return True
        else:
            logger.error("Failed to verify Instagram credentials")
            return False


# Helper function for video hosting (example with basic HTTP server)
class SimpleVideoHosting:
    """
    Simple video hosting solution for Instagram uploads
    You can replace this with S3, Cloudinary, or your own solution
    """
    
    @staticmethod
    def upload_to_temporary_hosting(video_path):
        """
        Upload video to temporary hosting and return public URL
        
        Options:
        1. Upload to AWS S3 and generate presigned URL
        2. Upload to your own server with public access
        3. Use services like Cloudinary, Imgur, etc.
        
        For production, implement one of these solutions
        """
        logger.warning("Temporary video hosting not implemented")
        logger.info("Please implement video hosting solution:")
        logger.info("- AWS S3 with presigned URLs")
        logger.info("- Your own web server")
        logger.info("- Cloud storage service (Cloudinary, etc.)")
        
        return None


if __name__ == "__main__":
    # Test Instagram uploader
    logging.basicConfig(level=logging.INFO)
    
    print("Instagram Uploader Module")
    print("=" * 50)
    print("\nTo use this module, you need:")
    print("1. Instagram Business or Creator account")
    print("2. Facebook App with Instagram Graph API access")
    print("3. Long-lived access token")
    print("4. Instagram User ID")
    print("\nSetup guide: https://developers.facebook.com/docs/instagram-api/")
    print("\nIMPORTANT: Videos must be hosted on a publicly accessible URL")
    print("You'll need to implement video hosting (S3, your server, etc.)")
    
    # Uncomment to test credentials
    # uploader = InstagramUploader()
    # uploader.verify_credentials()
