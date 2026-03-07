"""Video Pipeline Orchestrator — end-to-end video creation from topic to uploaded video.

Optimized for:
- Zero TTS cost (Edge-TTS by default)
- 5-7 min videos (retention sweet spot + monetizable)
- Auto YouTube Shorts generation
- Public upload by default
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.asset import Asset, AssetType
from app.models.video import Video, VideoStatus
from app.services.asset_collector import AssetCollector
from app.services.caption_generator import CaptionGenerator
from app.services.script_generator import ScriptGenerator
from app.services.seo_optimizer import SEOOptimizer
from app.services.shorts_generator import ShortsGenerator
from app.services.thumbnail_generator import ThumbnailGenerator
from app.services.video_assembler import AssembledVideo, VideoAssembler, VideoComponents
from app.services.voiceover_generator import VoiceoverGenerator


class PipelineStep(IntEnum):
    RESEARCH = 1
    SELECT = 2
    SCRIPT = 3
    VOICE = 4
    ASSETS = 5
    CAPTIONS = 6
    THUMBNAIL = 7
    ASSEMBLE = 8
    SEO = 9
    SHORTS = 10
    UPLOAD = 11
    TRACK = 12


STEP_TO_STATUS = {
    PipelineStep.RESEARCH: VideoStatus.RESEARCHING,
    PipelineStep.SELECT: VideoStatus.RESEARCHING,
    PipelineStep.SCRIPT: VideoStatus.SCRIPTING,
    PipelineStep.VOICE: VideoStatus.VOICEOVER,
    PipelineStep.ASSETS: VideoStatus.COLLECTING_ASSETS,
    PipelineStep.CAPTIONS: VideoStatus.GENERATING_CAPTIONS,
    PipelineStep.THUMBNAIL: VideoStatus.GENERATING_THUMBNAIL,
    PipelineStep.ASSEMBLE: VideoStatus.ASSEMBLING,
    PipelineStep.SEO: VideoStatus.OPTIMIZING_SEO,
    PipelineStep.SHORTS: VideoStatus.ASSEMBLING,
    PipelineStep.UPLOAD: VideoStatus.UPLOADING,
    PipelineStep.TRACK: VideoStatus.PUBLISHED,
}


@dataclass
class PipelineResult:
    video_id: int
    success: bool
    final_step: int
    error: str | None = None
    video_path: str | None = None
    thumbnail_path: str | None = None
    shorts_path: str | None = None
    youtube_video_id: str | None = None
    youtube_shorts_id: str | None = None


class VideoPipeline:
    """Orchestrates the full video creation pipeline with resumability."""

    MAX_RETRIES_PER_STEP = 3

    def __init__(self):
        self.script_gen = ScriptGenerator()
        self.voiceover_gen = VoiceoverGenerator()
        self.asset_collector = AssetCollector()
        self.caption_gen = CaptionGenerator()
        self.thumbnail_gen = ThumbnailGenerator()
        self.video_assembler = VideoAssembler()
        self.shorts_gen = ShortsGenerator()
        self.seo_optimizer = None
        try:
            self.seo_optimizer = SEOOptimizer()
        except ValueError:
            logger.warning("SEO optimizer not available (missing API key)")

    async def run_full_pipeline(
        self,
        video_id: int,
        topic: str | None = None,
    ) -> PipelineResult:
        """Run the complete pipeline for a video record."""
        async with async_session_factory() as db:
            video = await db.get(Video, video_id)
            if not video:
                return PipelineResult(video_id=video_id, success=False, final_step=0,
                                      error="Video not found")

            if topic:
                video.topic = topic

            if not video.topic:
                return PipelineResult(video_id=video_id, success=False, final_step=0,
                                      error="No topic specified")

            # Load channel info (explicit query — async can't lazy-load)
            from app.models.channel import Channel
            channel = await db.get(Channel, video.channel_id)
            niche = channel.niche if channel else "general"
            channel_name = channel.name if channel else "AutoTube AI"
            caption_style = channel.caption_style if channel else "hormozi"
            voice_id = channel.voice_id if channel else None

            start_step = video.pipeline_step + 1 if video.pipeline_step > 0 else PipelineStep.SCRIPT
            total_cost = Decimal(str(video.api_cost or 0))

            # Variables that persist across steps
            caption_result = None
            shorts_path = None
            shorts_video_id = None

            logger.info(f"Pipeline started for video {video_id}: '{video.topic}' "
                        f"(starting at step {start_step})")

            try:
                # === STEP 3: SCRIPT GENERATION (5-7 min sweet spot) ===
                if start_step <= PipelineStep.SCRIPT:
                    await self._update_status(db, video, PipelineStep.SCRIPT)

                    script = self.script_gen.generate_script(
                        topic=video.topic,
                        niche=niche,
                        duration_minutes=6,
                    )
                    video.script_text = script.text
                    video.word_count = script.word_count
                    video.duration_seconds = script.estimated_duration_seconds
                    total_cost += Decimal(str(script.cost_usd))
                    video.api_cost = total_cost
                    await db.commit()

                    logger.info(f"Step 3 (Script): {script.word_count} words, "
                                f"~{script.estimated_duration_seconds}s, ${script.cost_usd:.4f}")

                # === STEP 4: VOICEOVER (OpenAI TTS primary, Edge-TTS fallback) ===
                if start_step <= PipelineStep.VOICE:
                    await self._update_status(db, video, PipelineStep.VOICE)

                    clean_script = self.script_gen.clean_script_for_tts(video.script_text)
                    vo_result = self.voiceover_gen.generate_voiceover(
                        script=clean_script,
                        voice_id=voice_id,
                        provider="openai",
                        speed=1.05,
                    )
                    video.voiceover_path = vo_result.audio_path
                    video.duration_seconds = int(vo_result.duration_seconds)
                    total_cost += Decimal(str(vo_result.cost_usd))
                    video.api_cost = total_cost

                    self.voiceover_gen.normalize_audio(vo_result.audio_path)
                    await db.commit()

                    logger.info(f"Step 4 (Voice): {vo_result.duration_seconds:.1f}s, "
                                f"provider={vo_result.provider}, cost=${vo_result.cost_usd:.4f}")

                # === STEP 5: ASSET COLLECTION ===
                if start_step <= PipelineStep.ASSETS:
                    await self._update_status(db, video, PipelineStep.ASSETS)

                    collection = self.asset_collector.collect_assets_for_script(
                        video.script_text
                    )

                    for asset in collection.assets:
                        db_asset = Asset(
                            video_id=video.id,
                            type=AssetType(asset.type) if asset.type in AssetType.__members__.values() else AssetType.STOCK_VIDEO,
                            source=asset.source,
                            source_url=asset.source_url,
                            local_path=asset.local_path,
                            license_type="free" if asset.source in ("pexels", "pixabay") else "generated",
                            attribution=asset.attribution,
                        )
                        db.add(db_asset)

                    total_cost += Decimal(str(collection.total_cost_usd))
                    video.api_cost = total_cost
                    await db.commit()

                    logger.info(f"Step 5 (Assets): {len(collection.assets)} assets")

                # === STEP 6: CAPTION GENERATION ===
                if start_step <= PipelineStep.CAPTIONS:
                    await self._update_status(db, video, PipelineStep.CAPTIONS)

                    caption_result = self.caption_gen.generate_captions(
                        audio_path=video.voiceover_path,
                    )
                    await db.commit()

                    logger.info(f"Step 6 (Captions): {len(caption_result.entries)} entries")

                # === STEP 7: THUMBNAIL ===
                if start_step <= PipelineStep.THUMBNAIL:
                    await self._update_status(db, video, PipelineStep.THUMBNAIL)

                    thumb_result = self.thumbnail_gen.generate_thumbnail(
                        title=video.topic,
                        style=channel.thumbnail_style if channel else "bold",
                        niche=niche,
                    )
                    video.thumbnail_path = thumb_result.primary_path
                    await db.commit()

                    logger.info(f"Step 7 (Thumbnail): {len(thumb_result.paths)} variants")

                # === STEP 8: VIDEO ASSEMBLY ===
                if start_step <= PipelineStep.ASSEMBLE:
                    await self._update_status(db, video, PipelineStep.ASSEMBLE)

                    assets_result = await db.execute(
                        select(Asset).where(Asset.video_id == video.id)
                    )
                    db_assets = assets_result.scalars().all()
                    asset_paths = [a.local_path for a in db_assets if a.local_path]
                    asset_types = [a.type.value for a in db_assets if a.local_path]

                    caption_result_entries = []
                    if caption_result and hasattr(caption_result, "entries"):
                        caption_result_entries = caption_result.entries

                    components = VideoComponents(
                        voiceover_path=video.voiceover_path,
                        asset_paths=asset_paths,
                        asset_types=asset_types,
                        subtitle_entries=caption_result_entries,
                        channel_name=channel_name,
                        caption_style=caption_style,
                    )

                    assembled = self.video_assembler.assemble_video(components)
                    video.final_video_path = assembled.video_path
                    video.duration_seconds = int(assembled.duration_seconds)
                    await db.commit()

                    logger.info(f"Step 8 (Assemble): {assembled.duration_seconds:.1f}s video")

                # === STEP 9: SEO OPTIMIZATION ===
                if start_step <= PipelineStep.SEO:
                    await self._update_status(db, video, PipelineStep.SEO)

                    if self.seo_optimizer:
                        duration_min = (video.duration_seconds or 360) // 60
                        metadata = self.seo_optimizer.optimize_metadata(
                            topic=video.topic,
                            script=video.script_text or "",
                            niche=niche,
                            duration_minutes=duration_min,
                        )
                        video.title = metadata.selected_title
                        video.description = metadata.description
                        video.tags = metadata.tags
                        total_cost += Decimal(str(metadata.cost_usd))
                        video.api_cost = total_cost
                        await db.commit()

                        logger.info(f"Step 9 (SEO): '{metadata.selected_title}', "
                                    f"{len(metadata.tags)} tags")
                    else:
                        video.title = video.topic[:100]
                        await db.commit()
                        logger.info("Step 9 (SEO): skipped (no API key)")

                # === STEP 10: YOUTUBE SHORTS ===
                if start_step <= PipelineStep.SHORTS:
                    await self._update_status(db, video, PipelineStep.SHORTS)

                    if video.final_video_path and video.script_text:
                        try:
                            short_result = self.shorts_gen.generate_short(
                                video_path=video.final_video_path,
                                script_text=video.script_text,
                                voiceover_path=video.voiceover_path,
                                video_duration=video.duration_seconds or 360,
                                caption_entries=caption_result.entries if caption_result and hasattr(caption_result, "entries") else None,
                            )
                            if short_result:
                                shorts_path = short_result.video_path
                                total_cost += Decimal(str(short_result.cost_usd))
                                video.api_cost = total_cost
                                await db.commit()
                                logger.info(f"Step 10 (Short): {short_result.duration_seconds:.1f}s, "
                                            f"hook='{short_result.hook_text}'")
                            else:
                                logger.warning("Step 10 (Short): generation returned None")
                        except Exception as short_err:
                            logger.warning(f"Step 10 (Short) failed: {short_err}")
                    else:
                        logger.warning("Step 10 (Short): no video/script available")

                # === STEP 11: YOUTUBE UPLOAD (PUBLIC) ===
                if start_step <= PipelineStep.UPLOAD:
                    await self._update_status(db, video, PipelineStep.UPLOAD)

                    if channel and channel.oauth_credentials_encrypted and video.final_video_path:
                        try:
                            from app.services.youtube_uploader import YouTubeUploader
                            uploader = YouTubeUploader(channel.oauth_credentials_encrypted)

                            # Upload main video as PUBLIC
                            upload_result = uploader.upload_video(
                                video_path=video.final_video_path,
                                title=video.title or video.topic[:100],
                                description=video.description or "",
                                tags=video.tags or [],
                                category_id="28" if niche == "technology" else "22",
                                privacy_status="public",
                                thumbnail_path=video.thumbnail_path,
                            )

                            video.youtube_video_id = upload_result.video_id
                            video.api_cost = total_cost
                            await db.commit()

                            logger.info(f"Step 11 (Upload): youtube.com/watch?v={upload_result.video_id} [PUBLIC]")

                            # Upload Short
                            if shorts_path:
                                try:
                                    short_title = f"{(video.title or video.topic)[:55]} #shorts"
                                    short_desc = (
                                        f"{(video.description or '')[:200]}\n\n"
                                        f"Full video: https://youtube.com/watch?v={upload_result.video_id}\n"
                                        f"#shorts #{niche.replace(' ', '')}"
                                    )
                                    short_tags = (video.tags or [])[:8] + ["shorts", "short", niche]
                                    short_upload = uploader.upload_video(
                                        video_path=shorts_path,
                                        title=short_title[:100],
                                        description=short_desc[:5000],
                                        tags=short_tags,
                                        category_id="28" if niche == "technology" else "22",
                                        privacy_status="public",
                                    )
                                    shorts_video_id = short_upload.video_id
                                    logger.info(f"Step 11 (Short Upload): youtube.com/shorts/{short_upload.video_id}")
                                except Exception as se:
                                    logger.warning(f"Short upload failed: {se}")

                        except Exception as upload_err:
                            logger.warning(f"Step 11 (Upload) failed: {upload_err}")
                    else:
                        reason = "no OAuth" if not (channel and channel.oauth_credentials_encrypted) else "no video"
                        logger.info(f"Step 11 (Upload): skipped ({reason})")

                # === STEP 12: TRACK ===
                if start_step <= PipelineStep.TRACK:
                    video.pipeline_step = PipelineStep.TRACK
                    if video.youtube_video_id:
                        video.status = VideoStatus.PUBLISHED
                    else:
                        video.status = VideoStatus.ASSEMBLING
                    await db.commit()
                    logger.info("Step 12 (Track): pipeline complete")

                total_float = float(total_cost)
                logger.info(f"Pipeline completed for video {video_id} — total cost: ${total_float:.4f}")

                return PipelineResult(
                    video_id=video_id,
                    success=True,
                    final_step=video.pipeline_step,
                    video_path=video.final_video_path,
                    thumbnail_path=video.thumbnail_path,
                    shorts_path=shorts_path,
                    youtube_video_id=video.youtube_video_id,
                    youtube_shorts_id=shorts_video_id,
                )

            except Exception as e:
                logger.error(f"Pipeline failed at step {video.pipeline_step}: {e}")
                video.status = VideoStatus.FAILED
                video.error_message = str(e)[:1000]
                video.api_cost = total_cost
                await db.commit()

                return PipelineResult(
                    video_id=video_id,
                    success=False,
                    final_step=video.pipeline_step,
                    error=str(e),
                )

    async def _update_status(
        self, db: AsyncSession, video: Video, step: PipelineStep
    ) -> None:
        """Update video status and pipeline step in the database."""
        video.pipeline_step = step
        video.status = STEP_TO_STATUS[step]
        video.error_message = None
        await db.commit()
