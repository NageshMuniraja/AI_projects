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
    
    def generate_video_from_text(self, prompt, duration=5, output_path=None):
        """
        Generate video from text prompt using Runway Gen-3
        
        Args:
            prompt: Text description of the video
            duration: Duration in seconds (5 or 10)
            output_path: Where to save the video
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create generation request
        data = {
            "promptText": prompt,
            "model": "gen3a_turbo",  # Fast model for quick generation
            "duration": duration,
            "ratio": "9:16",  # Vertical for shorts/reels
            "watermark": False
        }
        
        try:
            logger.info(f"Generating video: {prompt[:50]}...")
            
            # Start generation
            response = requests.post(
                f"{self.base_url}/image_to_video",
                headers=headers,
                json=data
            )
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
                    video_url = status.get('output', [{}])[0].get('url')
                    logger.info(f"Video generated successfully: {video_url}")
                    return video_url
                elif state == 'FAILED':
                    logger.error(f"Video generation failed: {status.get('failure')}")
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
    
    def generate_multiple_clips(self, visual_prompts, output_dir, prefix="clip"):
        """Generate multiple video clips from visual prompts"""
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
                output_path=output_path
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
                text,
                fontsize=70,
                color='white',
                size=(900, None),
                method='caption',
                align='center'
            )
            txt = txt.set_position('center').set_duration(duration)
            
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
    output_path = Config.TEMP_DIR / "video" / "test_video.mp4"
    
    print("Testing video generation...")
    print("Note: This will take 1-3 minutes and uses API credits")
    
    # Uncomment to test actual API
    # result = generator.generate_video_from_text(test_prompt, duration=5, output_path=output_path)
    
    # Test placeholder instead
    result = generator.create_placeholder_video(
        "Test Video\nColorful Kids Content",
        duration=5,
        output_path=output_path
    )
    
    if result:
        print(f"Video created: {result}")
