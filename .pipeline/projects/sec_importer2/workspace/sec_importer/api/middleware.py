"""API middleware — CORS, rate limiting, request logging."""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import APIConfig

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI, config: APIConfig) -> None:
    """Configure all middleware for the FastAPI application."""
    _add_cors(app, config)
    _add_request_logging(app)
    _add_rate_limiting(app, config)


def _add_cors(app: FastAPI, config: APIConfig) -> None:
    """Add CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=config.cache_ttl_seconds,
    )


def _add_request_logging(app: FastAPI) -> None:
    """Add request/response logging middleware."""
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        msg = f"{request.method} {request.url.path} {response.status_code} {duration:.3f}s"
        
        if response.status_code >= 400:
            logger.warning(msg)
        else:
            logger.debug(msg)

        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response


def _add_rate_limiting(app: FastAPI, config: APIConfig) -> None:
    """Add simple rate limiting middleware."""
    from collections import defaultdict

    _rate_limits: dict[str, list[float]] = defaultdict(list)
    rate_limit = config.rate_limit_per_minute

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # 1 minute window

        # Clean old entries
        _rate_limits[client_ip] = [
            t for t in _rate_limits[client_ip] if now - t < window
        ]

        if len(_rate_limits[client_ip]) >= rate_limit:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )

        _rate_limits[client_ip].append(now)
        return await call_next(request)
