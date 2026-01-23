"""
Video Generator Module
Generates video clips using Runway API
"""
import logging
import requests
import time
import json
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class VideoGenerator:
    """Generate video clips using Runway Gen-3 API"""
    
    def __init__(self):
        self.api_key = Config.RUNWAY_API_KEY
        self.base_url = "https://api.dev.runwayml.com/v1"
    
    def generate_video_from_text(self, prompt, duration=5, output_path=None, video_type="shorts"):
        """
        Generate video from text prompt using Runway Gen-3
        
        Args:
            prompt: Text description of the video
            duration: Duration in seconds (4, 6, or 8)
            output_path: Where to save the video
            video_type: "shorts" for 9:16 vertical, "video" for 16:9 horizontal
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"
        }
        
        # Create generation request for text-to-video
        # Valid durations: 4, 6, 8 seconds
        # Valid ratios: 1280:720, 720:1280, 1080:1920, 1920:1080
        valid_duration = 4 if duration <= 4 else (6 if duration <= 6 else 8)
        
        # Determine aspect ratio based on video type
        if video_type.lower() in ["shorts", "reel", "reels", "vertical"]:
            ratio = "1080:1920"  # 9:16 vertical for Shorts/Reels
        else:
            ratio = "1920:1080"  # 16:9 horizontal for regular videos
        
        data = {
            "promptText": prompt,
            "model": "veo3.1_fast",
            "duration": valid_duration,
            "ratio": ratio,
            "watermark": False
        }
        
        try:
            logger.info(f"Generating video: {prompt[:50]}...")
            logger.info(f"API Key present: {bool(self.api_key)}")
            logger.info(f"API Key length: {len(self.api_key) if self.api_key else 0}")
            
            # Start generation using text-to-video endpoint
            response = requests.post(
                f"{self.base_url}/text_to_video",
                headers=headers,
                json=data
            )
            
            # Log response details before raising
            logger.info(f"Response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            task = response.json()
            task_id = task.get('id')
            
            if not task_id:
                logger.error("No task ID returned")
                return None
            
            logger.info(f"Task created: {task_id}")
            
            # Poll for completion
            video_url = self._wait_for_completion(task_id, headers)
            
            if video_url and output_path:
                # Download video
                return self._download_video(video_url, output_path)
            
            return video_url
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def _wait_for_completion(self, task_id, headers, max_wait=300):
        """Wait for video generation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers=headers
                )
                response.raise_for_status()
                status = response.json()
                
                state = status.get('status')
                logger.info(f"Task status: {state}")
                
                if state == 'SUCCEEDED':
                    # Handle different response formats
                    output = status.get('output')
                    if isinstance(output, list) and len(output) > 0:
                        video_url = output[0].get('url') if isinstance(output[0], dict) else output[0]
                    elif isinstance(output, str):
                        video_url = output
                    else:
                        video_url = status.get('outputUrl') or status.get('url')
                    
                    logger.info(f"Video generated successfully: {video_url}")
                    return video_url
                elif state == 'FAILED':
                    failure_info = status.get('failure', {})
                    error_msg = failure_info if isinstance(failure_info, str) else failure_info.get('message', 'Unknown error')
                    logger.error(f"Video generation failed: {error_msg}")
                    logger.warning("This may be a temporary API issue. You can:")
                    logger.warning("1. Try again later")
                    logger.warning("2. Use a different prompt")
                    logger.warning("3. System will create placeholder video as fallback")
                    return None
                
                # Wait before polling again
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking task status: {e}")
                return None
        
        logger.error("Video generation timed out")
        return None
    
    def _download_video(self, url, output_path):
        """Download video from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    def generate_multiple_clips(self, visual_prompts, output_dir, prefix="clip", video_type="shorts"):
        """Generate multiple video clips from visual prompts
        
        Args:
            visual_prompts: List of prompts for video generation
            output_dir: Directory to save clips
            prefix: Filename prefix
            video_type: "shorts" for 9:16 vertical, "video" for 16:9 horizontal
        """
        video_clips = []
        
        for i, prompt_data in enumerate(visual_prompts):
            prompt = prompt_data.get('prompt', '')
            timestamp = prompt_data.get('timestamp', f'clip_{i}')
            
            if not prompt:
                continue
            
            # Enhance prompt for better results
            enhanced_prompt = self._enhance_prompt(prompt)
            
            output_path = Path(output_dir) / f"{prefix}_{i:02d}.mp4"
            
            logger.info(f"Generating clip {i+1}/{len(visual_prompts)}")
            video_path = self.generate_video_from_text(
                enhanced_prompt,
                duration=5,
                output_path=output_path,
                video_type=video_type
            )
            
            if video_path:
                video_clips.append({
                    'index': i,
                    'timestamp': timestamp,
                    'path': video_path,
                    'prompt': prompt
                })
            
            # Rate limiting - wait between requests
            if i < len(visual_prompts) - 1:
                time.sleep(5)
        
        logger.info(f"Generated {len(video_clips)}/{len(visual_prompts)} video clips")
        return video_clips
    
    def _enhance_prompt(self, prompt):
        """Enhance prompt for better video generation"""
        # Add style keywords for kids content
        style_keywords = [
            "vibrant colors",
            "bright and cheerful",
            "child-friendly",
            "high quality",
            "smooth motion"
        ]
        
        # Check if prompt already has style keywords
        has_style = any(keyword in prompt.lower() for keyword in style_keywords)
        
        if not has_style:
            enhanced = f"{prompt}, vibrant colors, bright and cheerful, high quality, smooth motion"
        else:
            enhanced = prompt
        
        return enhanced
    
    def create_placeholder_video(self, text, duration, output_path, color=(255, 200, 100)):
        """
        Create a simple placeholder video with text (fallback if API fails)
        """
        try:
            from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
            
            # Create colored background
            bg = ColorClip(
                size=(1080, 1920),
                color=color,
                duration=duration
            )
            
            # Create text
            txt = TextClip(
                text=text,
                font_size=70,
                color='white',
                size=(900, None),
                method='caption'
            )
            txt = txt.with_position('center').with_duration(duration)
            
            # Composite
            video = CompositeVideoClip([bg, txt])
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio=False,
                logger=None
            )
            
            logger.info(f"Created placeholder video: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating placeholder video: {e}")
            return None


if __name__ == "__main__":
    # Test the video generator
    logging.basicConfig(level=logging.INFO)
    Config.create_directories()
    
    generator = VideoGenerator()
    
    # Test with a sample prompt
    test_prompt = "A colorful animated scene of children playing in a sunny park with trees and flowers, bright and cheerful, 3D animation style"
    
    print("Testing video generation...")
    print("Choose video type:")
    print("1. Shorts/Reels (9:16 vertical)")
    print("2. Regular Video (16:9 horizontal)")
    
    choice = input("Enter 1 or 2 (default: 1): ").strip() or "1"
    
    if choice == "2":
        video_type = "video"
        output_path = Config.TEMP_DIR / "video" / "test_regular_video.mp4"
        print("\nGenerating REGULAR VIDEO (16:9 horizontal)...")
    else:
        video_type = "shorts"
        output_path = Config.TEMP_DIR / "video" / "test_shorts_video.mp4"
        print("\nGenerating SHORTS/REEL (9:16 vertical)...")
    
    print("Note: This will take 1-3 minutes and uses API credits")
    
    # Test actual API with selected format
    result = generator.generate_video_from_text(
        test_prompt, 
        duration=5, 
        output_path=output_path,
        video_type=video_type
    )
    
    # If API fails, create placeholder as fallback
    if not result:
        print("\n⚠️ API generation failed. Creating placeholder video as fallback...")
        result = generator.create_placeholder_video(
            "Test Video\nColorful Kids Content\n\nAPI Error\nTry again later",
            duration=5,
            output_path=output_path
        )
    #     output_path=output_path
    # )
    
    if result:
        print(f"Video created: {result}")
