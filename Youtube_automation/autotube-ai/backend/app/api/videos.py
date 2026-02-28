from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoCreate, VideoListResponse, VideoResponse

router = APIRouter()


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    channel_id: int | None = None,
    status: VideoStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Video)
    count_query = select(func.count(Video.id))

    if channel_id:
        query = query.where(Video.channel_id == channel_id)
        count_query = count_query.where(Video.channel_id == channel_id)
    if status:
        query = query.where(Video.status == status)
        count_query = count_query.where(Video.status == status)

    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    total_result = await db.execute(count_query)
    return VideoListResponse(
        videos=result.scalars().all(),
        total=total_result.scalar_one(),
    )


@router.post("/", response_model=VideoResponse, status_code=201)
async def create_video(data: VideoCreate, db: AsyncSession = Depends(get_db)):
    video = Video(**data.model_dump())
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return video


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.delete(video)
