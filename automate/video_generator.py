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
        if not self.api_key:
            logger.error("RUNWAY_API_KEY is not set. Set RUNWAY_API_KEY in your environment or .env file.")
            raise ValueError("Missing RUNWAY_API_KEY")
        self.base_url = "https://api.dev.runwayml.com/v1"
    
    def generate_video_from_text(self, prompt, duration=5, output_path=None):
        """
        Generate video from text prompt using Runway Gen-3
        
        Args:
            prompt: Text description of the video
            duration: Duration in seconds (5 or 10)
            output_path: Where to save the video
        """
        # Validate duration
        if duration not in [5, 10]:
            logger.error("Invalid duration. Must be 5 or 10 seconds.")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"  # required by Runway API; update if needed per docs
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

            # If API returns non-2xx, log details and attempt a single retry with alternate payload
            if not response.ok:
                # Try to parse JSON error body if possible
                try:
                    err_body = response.json()
                except Exception:
                    err_body = response.text
                logger.error(f"Runway API returned HTTP {response.status_code}: {err_body}")

                # If 400 Bad Request, retry with alternate field names (some endpoints expect 'prompt') and fewer params
                if response.status_code == 400:
                    logger.info("Retrying with alternate payload (using 'prompt' key and removing 'ratio'/'watermark')")
                    alt_data = {
                        "prompt": prompt,
                        "model": data.get("model"),
                        "duration": data.get("duration")
                    }
                    try:
                        retry_resp = requests.post(
                            f"{self.base_url}/image_to_video",
                            headers=headers,
                            json=alt_data
                        )
                        if not retry_resp.ok:
                            try:
                                retry_err = retry_resp.json()
                            except Exception:
                                retry_err = retry_resp.text
                            logger.error(f"Retry failed HTTP {retry_resp.status_code}: {retry_err}")
                            return None
                        else:
                            response = retry_resp
                    except Exception as re:
                        logger.error(f"Retry request error: {re}")
                        return None
                else:
                    return None

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
            # If it's an HTTPError from requests, include response body when available
            if hasattr(e, 'response') and e.response is not None:
                try:
                    logger.error(f"Response: {e.response.json()}")
                except Exception:
                    logger.error(f"Response text: {e.response.text}")
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
        Uses Pillow to render text into an image and MoviePy ImageClip to avoid ImageMagick/TextClip.
        """
        try:
            # Lazy imports to avoid top-level dependency issues
            from moviepy.editor import ColorClip, ImageClip, CompositeVideoClip
            from PIL import Image, ImageDraw, ImageFont

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create background color clip
            bg = ColorClip(
                size=(1080, 1920),
                color=color,
                duration=duration
            )

            # Render text to an image using Pillow
            img_w, img_h = 900, 600
            img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Try to load a reasonable truetype font; fall back to default
            try:
                font = ImageFont.truetype("Arial.ttf", 70)
            except Exception:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 70)
                except Exception:
                    font = ImageFont.load_default()

            # Simple word-wrap
            max_w = img_w - 40
            words = text.split()
            lines = []
            line = ""
            for w in words:
                test_line = (line + " " + w).strip()
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] > max_w and line:
                    lines.append(line)
                    line = w
                else:
                    line = test_line
            if line:
                lines.append(line)

            # Compute vertical position to center text
            line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
            total_h = line_height * len(lines)
            y = (img_h - total_h) // 2

            # Draw each line centered
            for l in lines:
                bbox = draw.textbbox((0, 0), l, font=font)
                w = bbox[2]
                x = (img_w - w) // 2
                draw.text((x, y), l, font=font, fill="white")
                y += line_height

            # Save temp image
            temp_img_path = output_path.with_suffix('.png')
            img.save(temp_img_path)

            # Create ImageClip and composite
            txt_clip = ImageClip(str(temp_img_path)).set_duration(duration)
            # No resize to avoid Pillow ANTIALIAS / Resampling compatibility issues
            txt_clip = txt_clip.set_position(('center', 'center'))

            video = CompositeVideoClip([bg, txt_clip])

            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio=False,
                logger=None
            )

            # Clean up temp image
            try:
                temp_img_path.unlink()
            except Exception:
                pass

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
