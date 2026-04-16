"""Request logging middleware.

For every HTTP request:
  - Injects a unique X-Request-ID header (UUID4)
  - Stores request_id in request.state so exception handlers can include it
  - Logs method, path, status, and latency
  - Returns X-Request-ID in the response headers for tracing
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Paths that are too noisy to log every hit
_SILENT_PATHS = {"/api/v1/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        silent = request.url.path in _SILENT_PATHS
        start = time.perf_counter()

        if not silent:
            logger.info(
                "→ %s %s  request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "✗ %s %s  request_id=%s  %.0fms — unhandled exception",
                request.method,
                request.url.path,
                request_id,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        status = response.status_code

        if not silent:
            log_fn = logger.info if status < 500 else logger.error
            log_fn(
                "← %s %s  status=%d  request_id=%s  %.0fms",
                request.method,
                request.url.path,
                status,
                request_id,
                elapsed_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response
