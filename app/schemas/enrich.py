"""Pydantic models for CV enrichment requests and responses.

Naming follows the camelCase convention used by the Greenhouse/Databricks
integration (alias) while keeping Python-idiomatic snake_case internally.
Set `model_config = {"populate_by_name": True}` so callers may use either.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Shared config ─────────────────────────────────────────────────────────────

_CAMEL_CONFIG = ConfigDict(populate_by_name=True)


# ── Sub-models ────────────────────────────────────────────────────────────────

class JobDescription(BaseModel):
    model_config = _CAMEL_CONFIG

    id: str = Field(default="", description="Job description identifier")
    title: str = Field(..., description="Job title, e.g. 'Senior Python Developer'")
    requirements: list[str] = Field(default=[], description="Required skills/qualifications")
    responsibilities: list[str] = Field(default=[], description="Key responsibilities")
    nice_to_have: list[str] = Field(
        default=[], alias="niceToHave", description="Optional/preferred skills"
    )


class GreenhouseCandidate(BaseModel):
    model_config = _CAMEL_CONFIG

    candidate_id: str = Field(alias="candidateId", description="Greenhouse candidate ID")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str = ""
    phone: str = ""
    current_title: str = Field(default="", alias="currentTitle")
    current_company: str = Field(default="", alias="currentCompany")
    education: list[dict[str, Any]] = []
    employment_history: list[dict[str, Any]] = Field(
        default=[], alias="employmentHistory"
    )


class CvExtracted(BaseModel):
    model_config = _CAMEL_CONFIG

    raw_text: str = Field(default="", alias="rawText", description="Full extracted CV text")
    structured: dict[str, Any] = Field(
        default={}, description="Pre-structured fields (skills, certifications, etc.)"
    )


# ── Request Models ────────────────────────────────────────────────────────────

class EnrichCVRequest(BaseModel):
    """
    Full enrichment request — mirrors the Greenhouse/Databricks pipeline format.
    Accepted by POST /api/v1/cv/enrich and POST /api/v1/cv/enrich/sync.
    """

    model_config = _CAMEL_CONFIG

    job_description: JobDescription = Field(alias="jobDescription")
    greenhouse_parse_data: GreenhouseCandidate = Field(alias="greenhouseParseData")
    json_cv_text_extracted: CvExtracted = Field(alias="jsonCvTextExtracted")
    document_type: int = Field(
        default=1,
        alias="documentType",
        description="1 = PDF, 2 = DOCX, 3 = DOC",
    )


class DirectEnrichRequest(BaseModel):
    """
    Lightweight request for POST /api/v1/cv/enrich/direct.
    Calls Databricks Model Serving directly — no job required.
    """

    cv_text: str = Field(..., min_length=20, description="Raw CV text (plain text)")
    job_title: str = Field(..., min_length=2, description="Target job title")
    job_requirements: list[str] = Field(
        default=[], description="Required skills for the position"
    )
    candidate_name: str = Field(default="", description="Candidate full name (optional)")


# ── Response Models ───────────────────────────────────────────────────────────

class EnrichCVAsyncResponse(BaseModel):
    """Returned immediately after triggering an async enrichment job."""

    run_id: int
    status: str = "started"
    message: str = "CV enrichment job triggered. Poll /cv/runs/{run_id}/status to track progress."


class EnrichCVSyncResponse(BaseModel):
    """Returned once a synchronous enrichment job completes."""

    run_id: int
    status: str = "completed"
    data: dict[str, Any]
    processing_time_ms: int | None = None


class JobStatusResponse(BaseModel):
    """Current state of a Databricks job run."""

    run_id: int
    lifecycle_state: str = Field(
        description="PENDING | RUNNING | TERMINATING | TERMINATED | SKIPPED | INTERNAL_ERROR"
    )
    result_state: str | None = Field(
        default=None, description="SUCCESS | FAILED | TIMEDOUT | CANCELED (only when terminated)"
    )
    state_message: str = ""
    is_complete: bool = False
    is_success: bool = False


class JobResultResponse(BaseModel):
    """Enriched CV data returned from a completed job run."""

    run_id: int
    status: str = "completed"
    data: dict[str, Any]
