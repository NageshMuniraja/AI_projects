"""
Video Assembly Module
Combines audio, video clips, and text overlays using FFmpeg and MoviePy
"""
import logging
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, TextClip, ColorClip
)
from config import Config

# Pillow compatibility shim: older code and libraries may reference Image.ANTIALIAS
try:
    from PIL import Image as PILImage
    if not hasattr(PILImage, 'ANTIALIAS'):
        # Pillow 10+ moved ANTIALIAS to Resampling.LANCZOS
        try:
            PILImage.ANTIALIAS = PILImage.Resampling.LANCZOS
        except Exception:
            # Fallback to LANCZOS constant if available
            if hasattr(PILImage, 'LANCZOS'):
                PILImage.ANTIALIAS = PILImage.LANCZOS
            else:
                PILImage.ANTIALIAS = 1
except Exception:
    # If PIL is not available, let imports/error handling later surface the issue
    pass

logger = logging.getLogger(__name__)

class VideoAssembler:
    """Assemble final videos from components"""
    
    def __init__(self):
        self.fps = Config.FPS
    
    def assemble_shorts_video(
        self, 
        video_clips, 
        audio_path, 
        text_overlays=None,
        output_path=None,
        target_duration=60
    ):
        """
        Assemble a 60-second shorts/reel video
        
        Args:
            video_clips: List of video clip paths
            audio_path: Path to audio file
            text_overlays: List of dicts with text, start, duration
            output_path: Where to save final video
            target_duration: Target duration in seconds
        """
        try:
            logger.info("Assembling shorts video...")
            
            # Load audio
            audio = AudioFileClip(audio_path)
            actual_duration = min(audio.duration, target_duration)
            
            # Load and prepare video clips
            clips = []
            for clip_path in video_clips:
                if Path(clip_path).exists():
                    clip = VideoFileClip(clip_path)
                    clips.append(clip)
            
            if not clips:
                logger.error("No valid video clips found")
                return None
            
            # Arrange clips to match audio duration
            final_clip = self._arrange_clips(clips, actual_duration)
            
            # Resize to shorts format (9:16)
            final_clip = final_clip.resize(Config.VIDEO_RESOLUTION)
            
            # Add audio
            final_clip = final_clip.set_audio(audio)
            
            # Add text overlays if provided
            if text_overlays:
                final_clip = self._add_text_overlays(final_clip, text_overlays)
            
            # Set output path
            if output_path is None:
                output_path = Config.OUTPUT_DIR / "shorts" / f"short_{int(time.time())}.mp4"
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write final video
            logger.info(f"Writing video to {output_path}...")
            final_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None
            )
            
            # Cleanup
            audio.close()
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Shorts video created: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error assembling shorts video: {e}")
            return None
    
    def assemble_short_video(
        self,
        video_clips,
        audio_path,
        text_overlays=None,
        output_path=None,
        target_duration=180
    ):
        """
        Assemble a 3-minute educational video
        
        Args:
            video_clips: List of video clip paths
            audio_path: Path to audio file
            text_overlays: List of dicts with text, start, duration
            output_path: Where to save final video
            target_duration: Target duration in seconds
        """
        try:
            logger.info("Assembling short video...")
            
            # Load audio
            audio = AudioFileClip(audio_path)
            actual_duration = min(audio.duration, target_duration)
            
            # Load video clips
            clips = []
            for clip_path in video_clips:
                if Path(clip_path).exists():
                    clip = VideoFileClip(clip_path)
                    clips.append(clip)
            
            if not clips:
                logger.error("No valid video clips found")
                return None
            
            # Arrange clips
            final_clip = self._arrange_clips(clips, actual_duration)
            
            # Resize to standard video format (16:9)
            final_clip = final_clip.resize(Config.SHORT_VIDEO_RESOLUTION)
            
            # Add audio
            final_clip = final_clip.set_audio(audio)
            
            # Add text overlays
            if text_overlays:
                final_clip = self._add_text_overlays(final_clip, text_overlays)
            
            # Set output path
            if output_path is None:
                output_path = Config.OUTPUT_DIR / "videos" / f"video_{int(time.time())}.mp4"
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write final video
            logger.info(f"Writing video to {output_path}...")
            final_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None
            )
            
            # Cleanup
            audio.close()
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Short video created: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error assembling short video: {e}")
            return None
    
    def _arrange_clips(self, clips, target_duration):
        """Arrange video clips to match target duration"""
        total_clip_duration = sum(clip.duration for clip in clips)
        
        if total_clip_duration >= target_duration:
            # Trim clips to fit
            return self._trim_clips_to_duration(clips, target_duration)
        else:
            # Loop clips to fill duration
            return self._loop_clips_to_duration(clips, target_duration)
    
    def _trim_clips_to_duration(self, clips, target_duration):
        """Trim clips to match target duration"""
        result_clips = []
        remaining_duration = target_duration
        
        for clip in clips:
            if remaining_duration <= 0:
                break
            
            if clip.duration <= remaining_duration:
                result_clips.append(clip)
                remaining_duration -= clip.duration
            else:
                # Trim the last clip
                trimmed = clip.subclip(0, remaining_duration)
                result_clips.append(trimmed)
                remaining_duration = 0
        
        return concatenate_videoclips(result_clips)
    
    def _loop_clips_to_duration(self, clips, target_duration):
        """Loop clips to fill target duration"""
        result_clips = []
        remaining_duration = target_duration
        clip_index = 0
        
        while remaining_duration > 0:
            clip = clips[clip_index % len(clips)]
            
            if clip.duration <= remaining_duration:
                result_clips.append(clip)
                remaining_duration -= clip.duration
            else:
                trimmed = clip.subclip(0, remaining_duration)
                result_clips.append(trimmed)
                remaining_duration = 0
            
            clip_index += 1
        
        return concatenate_videoclips(result_clips)
    
    def _add_text_overlays(self, video_clip, text_overlays):
        """Add text overlays to video"""
        composite_clips = [video_clip]
        
        for overlay in text_overlays:
            text = overlay.get('text', '')
            start_time = overlay.get('start', 0)
            duration = overlay.get('duration', 3)
            position = overlay.get('position', 'bottom')
            
            if not text:
                continue
            
            try:
                # Create text clip
                txt_clip = TextClip(
                    text,
                    fontsize=60,
                    color='white',
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=2,
                    size=(video_clip.w - 100, None),
                    method='caption',
                    align='center'
                )
                
                # Position text
                if position == 'bottom':
                    txt_clip = txt_clip.set_position(('center', video_clip.h - 200))
                elif position == 'top':
                    txt_clip = txt_clip.set_position(('center', 100))
                else:
                    txt_clip = txt_clip.set_position('center')
                
                # Set timing
                txt_clip = txt_clip.set_start(start_time).set_duration(duration)
                
                composite_clips.append(txt_clip)
                
            except Exception as e:
                logger.error(f"Error creating text overlay: {e}")
                continue
        
        return CompositeVideoClip(composite_clips)
    
    def add_intro_outro(self, video_path, intro_text=None, outro_text=None, output_path=None):
        """Add intro and outro screens to video"""
        try:
            main_video = VideoFileClip(video_path)
            clips = []
            
            # Add intro
            if intro_text:
                intro = self._create_text_screen(
                    intro_text,
                    duration=2,
                    size=main_video.size
                )
                clips.append(intro)
            
            clips.append(main_video)
            
            # Add outro
            if outro_text:
                outro = self._create_text_screen(
                    outro_text,
                    duration=2,
                    size=main_video.size
                )
                clips.append(outro)
            
            final_video = concatenate_videoclips(clips)
            
            if output_path is None:
                output_path = video_path.replace('.mp4', '_with_intro_outro.mp4')
            
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            main_video.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding intro/outro: {e}")
            return None
    
    def _create_text_screen(self, text, duration, size, bg_color=(100, 150, 255)):
        """Create a simple text screen"""
        bg = ColorClip(size=size, color=bg_color, duration=duration)
        
        txt = TextClip(
            text,
            fontsize=80,
            color='white',
            font='Arial-Bold',
            size=(size[0] - 100, None),
            method='caption',
            align='center'
        )
        txt = txt.set_position('center').set_duration(duration)
        
        return CompositeVideoClip([bg, txt])


if __name__ == "__main__":
    # Test the video assembler
    import time
    logging.basicConfig(level=logging.INFO)
    Config.create_directories()
    
    print("Video assembler module loaded successfully")
