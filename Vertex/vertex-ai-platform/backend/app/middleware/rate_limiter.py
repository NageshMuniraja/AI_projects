"""Rate limiting middleware using in-memory or Redis backend."""

import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

settings = get_settings()


class RateLimiter:
    """Simple in-memory rate limiter. Use Redis in production."""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        # Clean old entries
        self.requests[key] = [t for t in self.requests[key] if t > now - window]
        if len(self.requests[key]) >= limit:
            return False
        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Determine limit based on path
        if "/ai/" in request.url.path or "/chat/" in request.url.path:
            limit = settings.AI_RATE_LIMIT_PER_MINUTE
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE

        if not rate_limiter.is_allowed(client_ip, limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        return await call_next(request)
