from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate

router = APIRouter()


@router.get("/", response_model=list[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=ChannelResponse, status_code=201)
async def create_channel(data: ChannelCreate, db: AsyncSession = Depends(get_db)):
    channel = Channel(**data.model_dump())
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return channel


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int, data: ChannelUpdate, db: AsyncSession = Depends(get_db)
):
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)

    await db.flush()
    await db.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(channel)
