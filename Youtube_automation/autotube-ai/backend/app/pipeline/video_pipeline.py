"""Video Pipeline Orchestrator — end-to-end video creation from topic to assembled video."""

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
    UPLOAD = 10
    TRACK = 11


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

            # Use provided topic or existing one
            if topic:
                video.topic = topic

            if not video.topic:
                return PipelineResult(video_id=video_id, success=False, final_step=0,
                                      error="No topic specified")

            # Load channel info
            channel = video.channel
            niche = channel.niche if channel else "general"
            channel_name = channel.name if channel else "AutoTube AI"
            caption_style = channel.caption_style if channel else "hormozi"
            voice_id = channel.voice_id if channel else None

            start_step = video.pipeline_step + 1 if video.pipeline_step > 0 else PipelineStep.SCRIPT
            total_cost = Decimal(str(video.api_cost or 0))

            logger.info(f"Pipeline started for video {video_id}: '{video.topic}' "
                        f"(starting at step {start_step})")

            try:
                # === STEP 3: SCRIPT GENERATION ===
                if start_step <= PipelineStep.SCRIPT:
                    await self._update_status(db, video, PipelineStep.SCRIPT)

                    script = self.script_gen.generate_script(
                        topic=video.topic,
                        niche=niche,
                    )
                    video.script_text = script.text
                    video.word_count = script.word_count
                    video.duration_seconds = script.estimated_duration_seconds
                    total_cost += Decimal(str(script.cost_usd))
                    video.api_cost = total_cost
                    await db.commit()

                    logger.info(f"Step 3 (Script): {script.word_count} words, "
                                f"~{script.estimated_duration_seconds}s")

                # === STEP 4: VOICEOVER ===
                if start_step <= PipelineStep.VOICE:
                    await self._update_status(db, video, PipelineStep.VOICE)

                    clean_script = self.script_gen.clean_script_for_tts(video.script_text)
                    vo_result = self.voiceover_gen.generate_voiceover(
                        script=clean_script,
                        voice_id=voice_id,
                    )
                    video.voiceover_path = vo_result.audio_path
                    video.duration_seconds = int(vo_result.duration_seconds)
                    total_cost += Decimal(str(vo_result.cost_usd))
                    video.api_cost = total_cost

                    # Normalize audio
                    self.voiceover_gen.normalize_audio(vo_result.audio_path)
                    await db.commit()

                    logger.info(f"Step 4 (Voice): {vo_result.duration_seconds:.1f}s, "
                                f"provider={vo_result.provider}")

                # === STEP 5: ASSET COLLECTION ===
                if start_step <= PipelineStep.ASSETS:
                    await self._update_status(db, video, PipelineStep.ASSETS)

                    collection = self.asset_collector.collect_assets_for_script(
                        video.script_text
                    )

                    # Save assets to DB
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

                    logger.info(f"Step 5 (Assets): {len(collection.assets)} assets collected")

                # === STEP 6: CAPTION GENERATION ===
                if start_step <= PipelineStep.CAPTIONS:
                    await self._update_status(db, video, PipelineStep.CAPTIONS)

                    caption_result = self.caption_gen.generate_captions(
                        audio_path=video.voiceover_path,
                    )
                    await db.commit()

                    logger.info(f"Step 6 (Captions): {len(caption_result.entries)} entries, "
                                f"provider={caption_result.provider}")

                # === STEP 7: THUMBNAIL ===
                if start_step <= PipelineStep.THUMBNAIL:
                    await self._update_status(db, video, PipelineStep.THUMBNAIL)

                    thumb_result = self.thumbnail_gen.generate_thumbnail(
                        title=video.topic,
                        style=channel.thumbnail_style if channel else "bold",
                    )
                    video.thumbnail_path = thumb_result.primary_path
                    await db.commit()

                    logger.info(f"Step 7 (Thumbnail): {len(thumb_result.paths)} variants")

                # === STEP 8: VIDEO ASSEMBLY ===
                if start_step <= PipelineStep.ASSEMBLE:
                    await self._update_status(db, video, PipelineStep.ASSEMBLE)

                    # Gather asset paths from DB
                    assets_result = await db.execute(
                        select(Asset).where(Asset.video_id == video.id)
                    )
                    db_assets = assets_result.scalars().all()
                    asset_paths = [a.local_path for a in db_assets if a.local_path]
                    asset_types = [a.type.value for a in db_assets if a.local_path]

                    # Get caption entries
                    caption_result_entries = []
                    if hasattr(caption_result, "entries"):
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

                # === STEPS 9-11: SEO, UPLOAD, TRACK (Phases 4-5) ===
                # These will be wired in when the YouTube services are built
                if start_step <= PipelineStep.SEO:
                    video.pipeline_step = PipelineStep.ASSEMBLE
                    video.status = VideoStatus.ASSEMBLING
                    # Mark as completed up through assembly for now
                    await db.commit()

                logger.info(f"Pipeline completed for video {video_id} through step "
                            f"{video.pipeline_step}")

                return PipelineResult(
                    video_id=video_id,
                    success=True,
                    final_step=video.pipeline_step,
                    video_path=video.final_video_path,
                    thumbnail_path=video.thumbnail_path,
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
