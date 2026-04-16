"""Standard error response models."""

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Unified error envelope returned on all non-2xx responses."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None
    retry_after: int | None = None
