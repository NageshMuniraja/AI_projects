"""
Main Orchestrator
Coordinates all modules to generate and publish videos daily
"""
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from config import Config
from content_generator import ContentIdeaGenerator
from script_generator import ScriptGenerator
from audio_generator import AudioGenerator
from video_generator import VideoGenerator
from video_assembler import VideoAssembler
from youtube_uploader import YouTubeUploader
from instagram_uploader import InstagramUploader

# Setup logging
def setup_logging():
    """Configure logging for the application"""
    Config.create_directories()
    
    log_file = Config.LOG_DIR / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

class VideoAutomation:
    """Main automation orchestrator"""
    
    def __init__(self):
        """Initialize all modules"""
        logger.info("Initializing Video Automation System...")
        
        try:
            Config.validate()
            Config.create_directories()
            
            self.idea_generator = ContentIdeaGenerator()
            self.script_generator = ScriptGenerator()
            self.audio_generator = AudioGenerator()
            self.video_generator = VideoGenerator()
            self.video_assembler = VideoAssembler()
            #self.youtube_uploader = YouTubeUploader()
            #self.instagram_uploader = InstagramUploader()
            
            logger.info("All modules initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing modules: {e}")
            raise
    
    def generate_and_upload_shorts(self):
        """Generate and upload a short/reel"""
        logger.info("=" * 60)
        logger.info("STARTING SHORTS/REEL GENERATION")
        logger.info("=" * 60)
        
        try:
            # Step 1: Generate idea
            logger.info("Step 1: Generating content idea...")
            idea = self.idea_generator.generate_shorts_idea()
            if not idea:
                logger.error("Failed to generate idea")
                return False
            
            logger.info(f"Idea: {idea['title']}")
            
            # Step 2: Generate script
            logger.info("Step 2: Generating script...")
            script_data = self.script_generator.generate_shorts_script(idea)
            if not script_data:
                logger.error("Failed to generate script")
                return False
            
            logger.info(f"Script generated: {script_data['word_count']} words")
            
            # Step 3: Generate metadata
            logger.info("Step 3: Generating metadata...")
            metadata = self.script_generator.generate_metadata(idea, script_data, "shorts")
            
            # Step 4: Generate audio
            logger.info("Step 4: Generating audio...")
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_path = Config.TEMP_DIR / "audio" / f"shorts_audio_{date_str}.mp3"
            
            audio_file = self.audio_generator.generate_audio(
                script_data['script'],
                audio_path
            )
            
            if not audio_file:
                logger.error("Failed to generate audio")
                return False
            
            logger.info(f"Audio generated: {audio_file}")
            
            # Step 5: Generate video clips
            logger.info("Step 5: Generating video clips...")
            visual_prompts = script_data.get('visual_prompts', [])
            
            if not visual_prompts:
                # Generate visual prompts if not in script
                visuals = self.script_generator.generate_visual_descriptions(script_data, "shorts")
                visual_prompts = visuals.get('visual_prompts', []) if visuals else []
            
            video_dir = Config.TEMP_DIR / "video" / f"shorts_{date_str}"
            video_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate video clips (this takes time!)
            video_clips = []
            logger.info(f"Generating {len(visual_prompts)} video clips...")
            
            for i, prompt_data in enumerate(visual_prompts[:1]):  # Limit to 4 clips
                prompt = prompt_data if isinstance(prompt_data, str) else prompt_data.get('prompt', '')
                output_path = video_dir / f"clip_{i:02d}.mp4"
                
                logger.info(f"Generating clip {i+1}/4...")
                clip_path = self.video_generator.generate_video_from_text(
                    prompt,
                    duration=5,
                    output_path=output_path
                )
                
                if clip_path:
                    video_clips.append(clip_path)
                else:
                    # Create placeholder if generation fails
                    logger.warning(f"Video generation failed for clip {i}, creating placeholder")
                    placeholder = self.video_generator.create_placeholder_video(
                        f"Clip {i+1}",
                        duration=5,
                        output_path=output_path
                    )
                    if placeholder:
                        video_clips.append(placeholder)
            
            if not video_clips:
                logger.error("No video clips generated")
                return False
            
            logger.info(f"Generated {len(video_clips)} video clips")
            
            # Step 6: Assemble final video
            logger.info("Step 6: Assembling final video...")
            output_path = Config.OUTPUT_DIR / "shorts" / f"short_{date_str}.mp4"
            
            text_overlays = []
            if metadata and 'instagram_caption' in metadata:
                # Add text overlay at the beginning
                text_overlays.append({
                    'text': idea['title'],
                    'start': 1,
                    'duration': 3,
                    'position': 'bottom'
                })
            
            final_video = self.video_assembler.assemble_shorts_video(
                video_clips=video_clips,
                audio_path=audio_file,
                text_overlays=text_overlays,
                output_path=output_path,
                target_duration=60
            )
            
            if not final_video:
                logger.error("Failed to assemble video")
                return False
            
            logger.info(f"Final video created: {final_video}")
            
            # Step 7: Upload to YouTube
            logger.info("Step 7: Uploading to YouTube...")
            if metadata:
                youtube_result = self.youtube_uploader.upload_shorts(
                    video_path=final_video,
                    title=metadata['youtube_title'],
                    description=metadata['youtube_description'],
                    tags=metadata['youtube_tags']
                )
                
                if youtube_result:
                    logger.info(f"YouTube upload successful: {youtube_result['url']}")
                else:
                    logger.warning("YouTube upload failed")
            
            # Step 8: Upload to Instagram
            logger.info("Step 8: Uploading to Instagram...")
            logger.warning("Instagram upload requires video hosting - see instagram_uploader.py")
            # Uncomment when video hosting is implemented:
            # if metadata:
            #     instagram_result = self.instagram_uploader.upload_reel(
            #         video_path=final_video,
            #         caption=metadata['instagram_caption']
            #     )
            #     if instagram_result:
            #         logger.info(f"Instagram upload successful: {instagram_result['permalink']}")
            
            # Save session data
            self._save_session_data('shorts', {
                'date': date_str,
                'idea': idea,
                'script': script_data,
                'metadata': metadata,
                'video_path': final_video,
                'youtube': youtube_result if 'youtube_result' in locals() else None
            })
            
            logger.info("SHORTS/REEL GENERATION COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            logger.error(f"Error in shorts generation pipeline: {e}", exc_info=True)
            return False
    
    def generate_and_upload_short_video(self):
        """Generate and upload a short educational video"""
        logger.info("=" * 60)
        logger.info("STARTING SHORT VIDEO GENERATION")
        logger.info("=" * 60)
        
        try:
            # Step 1: Generate idea
            logger.info("Step 1: Generating content idea...")
            idea = self.idea_generator.generate_short_video_idea()
            if not idea:
                logger.error("Failed to generate idea")
                return False
            
            logger.info(f"Idea: {idea['title']}")
            
            # Step 2: Generate script
            logger.info("Step 2: Generating script...")
            script_data = self.script_generator.generate_short_video_script(idea)
            if not script_data:
                logger.error("Failed to generate script")
                return False
            
            logger.info(f"Script generated: {script_data['word_count']} words")
            
            # Step 3: Generate metadata
            logger.info("Step 3: Generating metadata...")
            metadata = self.script_generator.generate_metadata(idea, script_data, "video")
            
            # Step 4: Generate audio
            logger.info("Step 4: Generating audio...")
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_path = Config.TEMP_DIR / "audio" / f"video_audio_{date_str}.mp3"
            
            audio_file = self.audio_generator.generate_audio(
                script_data['script'],
                audio_path
            )
            
            if not audio_file:
                logger.error("Failed to generate audio")
                return False
            
            logger.info(f"Audio generated: {audio_file}")
            
            # Step 5: Generate video clips
            logger.info("Step 5: Generating video clips...")
            visual_prompts = script_data.get('visual_prompts', [])
            
            if not visual_prompts:
                visuals = self.script_generator.generate_visual_descriptions(script_data, "video")
                visual_prompts = visuals.get('visual_prompts', []) if visuals else []
            
            video_dir = Config.TEMP_DIR / "video" / f"short_video_{date_str}"
            video_dir.mkdir(parents=True, exist_ok=True)
            
            video_clips = []
            logger.info(f"Generating {min(len(visual_prompts), 6)} video clips...")
            
            for i, prompt_data in enumerate(visual_prompts[:6]):  # Limit to 6 clips
                prompt = prompt_data if isinstance(prompt_data, str) else prompt_data.get('prompt', '')
                output_path = video_dir / f"clip_{i:02d}.mp4"
                
                logger.info(f"Generating clip {i+1}/6...")
                clip_path = self.video_generator.generate_video_from_text(
                    prompt,
                    duration=10,
                    output_path=output_path
                )
                
                if clip_path:
                    video_clips.append(clip_path)
                else:
                    placeholder = self.video_generator.create_placeholder_video(
                        f"Scene {i+1}",
                        duration=10,
                        output_path=output_path
                    )
                    if placeholder:
                        video_clips.append(placeholder)
            
            if not video_clips:
                logger.error("No video clips generated")
                return False
            
            logger.info(f"Generated {len(video_clips)} video clips")
            
            # Step 6: Assemble final video
            logger.info("Step 6: Assembling final video...")
            output_path = Config.OUTPUT_DIR / "videos" / f"video_{date_str}.mp4"
            
            text_overlays = []
            if script_data.get('text_overlays'):
                for i, text in enumerate(script_data['text_overlays'][:3]):
                    text_overlays.append({
                        'text': text,
                        'start': i * 60,
                        'duration': 5,
                        'position': 'bottom'
                    })
            
            final_video = self.video_assembler.assemble_short_video(
                video_clips=video_clips,
                audio_path=audio_file,
                text_overlays=text_overlays,
                output_path=output_path,
                target_duration=180
            )
            
            if not final_video:
                logger.error("Failed to assemble video")
                return False
            
            logger.info(f"Final video created: {final_video}")
            
            # Step 7: Upload to YouTube
            logger.info("Step 7: Uploading to YouTube...")
            if metadata:
                youtube_result = self.youtube_uploader.upload_regular_video(
                    video_path=final_video,
                    title=metadata['youtube_title'],
                    description=metadata['youtube_description'],
                    tags=metadata['youtube_tags']
                )
                
                if youtube_result:
                    logger.info(f"YouTube upload successful: {youtube_result['url']}")
                else:
                    logger.warning("YouTube upload failed")
            
            # Save session data
            self._save_session_data('video', {
                'date': date_str,
                'idea': idea,
                'script': script_data,
                'metadata': metadata,
                'video_path': final_video,
                'youtube': youtube_result if 'youtube_result' in locals() else None
            })
            
            logger.info("SHORT VIDEO GENERATION COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            logger.error(f"Error in video generation pipeline: {e}", exc_info=True)
            return False
    
    def run_daily_job(self):
        """Run the complete daily automation"""
        logger.info("=" * 70)
        logger.info(f"STARTING DAILY VIDEO AUTOMATION - {datetime.now()}")
        logger.info("=" * 70)
        
        results = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'shorts': False,
            'video': False
        }
        
        # Generate shorts/reel
        logger.info("\n🎬 Task 1: Generate and upload shorts/reel")
        results['shorts'] = self.generate_and_upload_shorts()
        
        # Wait between tasks
        logger.info("\nWaiting 30 seconds before next task...")
        time.sleep(30)
        
        # Generate short video
        logger.info("\n🎬 Task 2: Generate and upload short video")
        results['video'] = self.generate_and_upload_short_video()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("DAILY AUTOMATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Shorts/Reel: {'✓ SUCCESS' if results['shorts'] else '✗ FAILED'}")
        logger.info(f"Short Video: {'✓ SUCCESS' if results['video'] else '✗ FAILED'}")
        logger.info("=" * 70)
        
        return results
    
    def _save_session_data(self, video_type, data):
        """Save session data for record keeping"""
        session_file = Config.LOG_DIR / f"{video_type}_{data['date']}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Session data saved: {session_file}")
        except Exception as e:
            logger.error(f"Error saving session data: {e}")


def main():
    """Main entry point"""
    try:
        automation = VideoAutomation()
        automation.run_daily_job()
        
    except KeyboardInterrupt:
        logger.info("\nAutomation interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
