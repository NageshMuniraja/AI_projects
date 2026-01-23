"""
Stock Video Downloader Module
Downloads free stock videos from Pexels API as alternative to AI generation
ZERO COST - Completely free!
"""
import logging
import requests
import time
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class StockVideoGenerator:
    """Generate video clips using free stock footage from Pexels"""
    
    def __init__(self):
        # Get free API key from: https://www.pexels.com/api/
        self.api_key = Config.PEXELS_API_KEY or "YOUR_FREE_PEXELS_API_KEY"
        self.base_url = "https://api.pexels.com/videos"
    
    def search_videos(self, query, per_page=15, orientation="portrait"):
        """
        Search for stock videos
        
        Args:
            query: Search term (e.g., "happy kids playing", "nature sunset")
            per_page: Number of results
            orientation: "portrait" for Shorts (9:16), "landscape" for regular (16:9)
        """
        headers = {
            "Authorization": self.api_key
        }
        
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return None
    
    def download_video(self, video_url, output_path):
        """Download video file"""
        try:
            logger.info(f"Downloading video to {output_path}...")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    def generate_video_from_text(self, prompt, duration=5, output_path=None, video_type="shorts"):
        """
        Generate video clip by searching and downloading stock footage
        
        Args:
            prompt: Search query (e.g., "funny cat", "beautiful sunset")
            duration: Desired duration (will be trimmed in assembler)
            output_path: Where to save video
            video_type: "shorts" for vertical, "video" for horizontal
        """
        # Determine orientation
        orientation = "portrait" if video_type.lower() in ["shorts", "reel", "vertical"] else "landscape"
        
        # Search for videos
        results = self.search_videos(prompt, per_page=10, orientation=orientation)
        
        if not results or 'videos' not in results:
            logger.warning(f"No videos found for: {prompt}")
            return None
        
        videos = results['videos']
        if not videos:
            return None
        
        # Get first video
        video = videos[0]
        
        # Find best quality video file
        video_files = video.get('video_files', [])
        if not video_files:
            return None
        
        # Sort by quality (HD preferred)
        video_files.sort(key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
        
        # Get download URL
        download_url = video_files[0].get('link')
        if not download_url:
            return None
        
        # Download video
        if output_path is None:
            output_path = Config.TEMP_DIR / "video" / f"stock_{int(time.time())}.mp4"
        
        return self.download_video(download_url, output_path)
    
    def create_placeholder_video(self, text, duration=5, output_path=None):
        """Create a simple colored placeholder video"""
        try:
            from moviepy import ColorClip, TextClip, CompositeVideoClip
            
            # Create colored background
            color_clip = ColorClip(
                size=(1080, 1920) if "shorts" in str(output_path) else (1920, 1080),
                color=(50, 50, 150),
                duration=duration
            )
            
            # Add text
            txt_clip = TextClip(
                text=text,
                fontsize=70,
                color='white',
                size=color_clip.size
            ).set_position('center').set_duration(duration)
            
            # Composite
            video = CompositeVideoClip([color_clip, txt_clip])
            
            # Write
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                logger=None
            )
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {e}")
            return None


# Alternative: Pixabay Videos API (also free)
class PixabayVideoGenerator:
    """Generate video clips using Pixabay free stock videos"""
    
    def __init__(self):
        # Get free API key from: https://pixabay.com/api/docs/
        self.api_key = Config.PIXABAY_API_KEY or "YOUR_FREE_PIXABAY_API_KEY"
        self.base_url = "https://pixabay.com/api/videos/"
    
    def search_videos(self, query, per_page=20):
        """Search Pixabay for videos"""
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "video_type": "all"
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching Pixabay: {e}")
            return None
    
    def download_video(self, video_url, output_path):
        """Download video from Pixabay"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded from Pixabay: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading from Pixabay: {e}")
            return None
    
    def generate_video_from_text(self, prompt, duration=5, output_path=None, video_type="shorts"):
        """Get video from Pixabay based on text prompt"""
        results = self.search_videos(prompt)
        
        if not results or 'hits' not in results:
            logger.warning(f"No Pixabay videos found for: {prompt}")
            return None
        
        videos = results['hits']
        if not videos:
            return None
        
        # Get first video
        video = videos[0]
        video_files = video.get('videos', {})
        
        # Try to get HD quality
        video_url = (video_files.get('large', {}).get('url') or 
                     video_files.get('medium', {}).get('url') or 
                     video_files.get('small', {}).get('url'))
        
        if not video_url:
            return None
        
        if output_path is None:
            output_path = Config.TEMP_DIR / "video" / f"pixabay_{int(time.time())}.mp4"
        
        return self.download_video(video_url, output_path)
