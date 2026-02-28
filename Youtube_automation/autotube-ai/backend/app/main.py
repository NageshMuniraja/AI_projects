from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.router import api_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AutoTube AI...")
    settings.ensure_media_dirs()
    yield
    logger.info("Shutting down AutoTube AI...")


app = FastAPI(
    title="AutoTube AI",
    description="Automated Faceless YouTube Channel Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autotube-ai"}
