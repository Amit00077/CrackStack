from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        if client_ip not in self._requests:
            self._requests[client_ip] = []
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]

        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": f"Rate limit of {self.max_requests} requests per {self.window_seconds}s exceeded",
                },
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


def setup_rate_limiting(app: FastAPI) -> None:
    from app.core.config import settings

    if not settings.RATE_LIMIT_ENABLED:
        return
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=InMemoryRateLimiter(),
    )
