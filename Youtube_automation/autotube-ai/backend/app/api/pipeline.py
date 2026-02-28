from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.video import PipelineStatusResponse, PipelineTriggerRequest, VideoResponse

router = APIRouter()

PIPELINE_STEPS = [
    {"step": 1, "name": "Research", "status_field": VideoStatus.RESEARCHING},
    {"step": 2, "name": "Script Generation", "status_field": VideoStatus.SCRIPTING},
    {"step": 3, "name": "Voiceover", "status_field": VideoStatus.VOICEOVER},
    {"step": 4, "name": "Asset Collection", "status_field": VideoStatus.COLLECTING_ASSETS},
    {"step": 5, "name": "Caption Generation", "status_field": VideoStatus.GENERATING_CAPTIONS},
    {"step": 6, "name": "Thumbnail", "status_field": VideoStatus.GENERATING_THUMBNAIL},
    {"step": 7, "name": "Video Assembly", "status_field": VideoStatus.ASSEMBLING},
    {"step": 8, "name": "SEO Optimization", "status_field": VideoStatus.OPTIMIZING_SEO},
    {"step": 9, "name": "Upload", "status_field": VideoStatus.UPLOADING},
    {"step": 10, "name": "Published", "status_field": VideoStatus.PUBLISHED},
]


@router.post("/trigger", response_model=VideoResponse, status_code=202)
async def trigger_pipeline(
    request: PipelineTriggerRequest, db: AsyncSession = Depends(get_db)
):
    """Trigger a new video pipeline run. Celery task will be dispatched in Phase 3."""
    video = Video(
        channel_id=request.channel_id,
        topic=request.topic,
        status=VideoStatus.QUEUED,
        pipeline_step=0,
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)

    # Dispatch Celery task
    from app.workers.video_tasks import run_pipeline_task
    run_pipeline_task.delay(video.id, request.topic)

    return video


@router.get("/status/{video_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    steps = []
    for step_def in PIPELINE_STEPS:
        if video.pipeline_step > step_def["step"]:
            state = "completed"
        elif video.pipeline_step == step_def["step"]:
            state = "in_progress" if video.status != VideoStatus.FAILED else "failed"
        else:
            state = "pending"
        steps.append({"step": step_def["step"], "name": step_def["name"], "state": state})

    return PipelineStatusResponse(
        video_id=video.id,
        status=video.status,
        pipeline_step=video.pipeline_step,
        error_message=video.error_message,
        steps=steps,
    )


@router.post("/resume/{video_id}", response_model=VideoResponse, status_code=202)
async def resume_pipeline(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != VideoStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed pipelines can be resumed")

    video.status = VideoStatus.QUEUED
    video.error_message = None
    await db.flush()
    await db.refresh(video)

    # Dispatch Celery resume task
    from app.workers.video_tasks import resume_pipeline_task
    resume_pipeline_task.delay(video.id)

    return video
