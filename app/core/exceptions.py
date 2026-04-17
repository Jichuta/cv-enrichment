"""Custom exception hierarchy for the CV Enrichment API.

All application errors subclass AppException so the global handler in
main.py can catch and format them consistently.
"""

from typing import Any


class AppException(Exception):
    """Base exception — carries HTTP status, error code, and optional details."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


# ── 4xx Client Errors ─────────────────────────────────────────────────────────


class ValidationError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="validation_error",
            details=details,
        )


class UnauthorizedError(AppException):
    def __init__(
        self, message: str = "Missing or invalid authentication token"
    ) -> None:
        super().__init__(message=message, status_code=401, error_code="unauthorized")


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403, error_code="forbidden")


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str | None = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(message=message, status_code=404, error_code="not_found")


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409, error_code="conflict")


class RateLimitError(AppException):
    def __init__(self, message: str = "Too many requests — please slow down") -> None:
        super().__init__(message=message, status_code=429, error_code="rate_limited")


# ── 5xx Server / Gateway Errors ───────────────────────────────────────────────


class DatabricksError(AppException):
    """Generic error from the Databricks API."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="databricks_error",
            details=details,
        )


class DatabricksJobFailedError(AppException):
    """A Databricks job run terminated with a non-SUCCESS result."""

    def __init__(self, run_id: int, state_message: str = "") -> None:
        msg = f"Databricks job run {run_id} failed"
        if state_message:
            msg += f": {state_message}"
        super().__init__(
            message=msg,
            status_code=502,
            error_code="job_failed",
            details={"run_id": run_id, "state_message": state_message},
        )


class DatabricksTimeoutError(AppException):
    """Job did not complete within the configured timeout."""

    def __init__(self, run_id: int, timeout_secs: int) -> None:
        super().__init__(
            message=f"Job run {run_id} did not complete within {timeout_secs}s",
            status_code=504,
            error_code="gateway_timeout",
            details={"run_id": run_id, "timeout_secs": timeout_secs},
        )


class LLMError(AppException):
    """Error calling the LLM endpoint directly."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="llm_error",
            details=details,
        )


class UnsupportedFileTypeError(AppException):
    """File type is not supported for text extraction."""

    def __init__(self, content_type: str, filename: str = "") -> None:
        super().__init__(
            message=f"Unsupported file type: '{content_type}'. Only PDF and DOCX are accepted.",
            status_code=415,
            error_code="unsupported_file_type",
            details={"content_type": content_type, "filename": filename},
        )


class FileTooLargeError(AppException):
    """Uploaded file exceeds the allowed size limit."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(
            message=f"File exceeds the maximum allowed size of {max_mb} MB.",
            status_code=413,
            error_code="file_too_large",
            details={"max_size_mb": max_mb},
        )


class ExtractionError(AppException):
    """Text could not be extracted from the uploaded file."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="extraction_error",
            details=details,
        )


class OutputParseError(AppException):
    """Could not extract valid JSON from job/LLM output."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="output_parse_error",
            details=details,
        )
