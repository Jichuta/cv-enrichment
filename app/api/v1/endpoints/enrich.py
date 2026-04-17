"""CV enrichment endpoints.

Routes:
  POST /api/v1/cv/enrich           — Trigger job (async, returns run_id immediately)
  POST /api/v1/cv/enrich/sync      — Trigger job and wait for result (sync)
  POST /api/v1/cv/enrich/direct    — Call Databricks LLM directly (no job)
  GET  /api/v1/cv/runs/{run_id}/status  — Poll job status
  GET  /api/v1/cv/runs/{run_id}/result  — Fetch completed job result
"""

import logging
import time

from fastapi import APIRouter

from app.api.deps import ApiKey
from app.schemas.enrich import (
    DirectEnrichRequest,
    EnrichCVAsyncResponse,
    EnrichCVRequest,
    EnrichCVSyncResponse,
    JobResultResponse,
    JobStatusResponse,
)
from app.services.enrichment import enrichment_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/enrich",
    response_model=EnrichCVAsyncResponse,
    status_code=202,
    summary="Trigger CV enrichment (async)",
    description=(
        "Triggers a Databricks job to enrich a candidate CV. "
        "Returns immediately with a `run_id`. "
        "Poll **GET /cv/runs/{run_id}/status** to check completion, "
        "then **GET /cv/runs/{run_id}/result** to fetch the enriched data."
    ),
)
async def enrich_cv_async(
    payload: EnrichCVRequest,
    _: ApiKey,
) -> EnrichCVAsyncResponse:
    run_id = await enrichment_service.trigger_job_async(payload)
    return EnrichCVAsyncResponse(run_id=run_id)


@router.post(
    "/enrich/sync",
    response_model=EnrichCVSyncResponse,
    status_code=200,
    summary="Trigger CV enrichment (synchronous)",
    description=(
        "Triggers a Databricks job and **waits** for completion before responding. "
        "Returns the full enriched CV JSON. "
        "May take up to 5 minutes — use the async endpoint for non-blocking workflows."
    ),
)
async def enrich_cv_sync(
    payload: EnrichCVRequest,
    _: ApiKey,
) -> EnrichCVSyncResponse:
    start = time.perf_counter()
    data = await enrichment_service.enrich_via_job(payload)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "Sync enrichment complete — candidate=%s elapsed=%dms",
        payload.greenhouse_parse_data.candidate_id,
        elapsed_ms,
    )
    return EnrichCVSyncResponse(run_id=0, data=data, processing_time_ms=elapsed_ms)


@router.post(
    "/enrich/direct",
    response_model=dict,
    status_code=200,
    summary="Enrich CV via direct LLM call",
    description=(
        "Calls Databricks Model Serving directly — **no Databricks job required**. "
        "Faster for single-request enrichment. "
        "Does NOT write results to Delta tables."
    ),
)
async def enrich_cv_direct(
    payload: DirectEnrichRequest,
    _: ApiKey,
) -> dict:
    start = time.perf_counter()
    result = await enrichment_service.enrich_via_llm(payload)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "Direct enrichment complete — job_title=%s elapsed=%dms",
        payload.job_title,
        elapsed_ms,
    )
    return result


@router.get(
    "/runs/{run_id}/status",
    response_model=JobStatusResponse,
    summary="Get enrichment job status",
    description="Returns the current lifecycle and result state of a Databricks job run.",
)
async def get_run_status(
    run_id: int,
    _: ApiKey,
) -> JobStatusResponse:
    status = await enrichment_service.get_job_status(run_id)
    return JobStatusResponse(
        run_id=run_id,
        lifecycle_state=status["lifecycle_state"],
        result_state=status.get("result_state"),
        state_message=status.get("state_message", ""),
        is_complete=status["is_complete"],
        is_success=status["is_success"],
    )


@router.get(
    "/runs/{run_id}/result",
    response_model=JobResultResponse,
    summary="Get enrichment job result",
    description=(
        "Fetches and parses the enriched CV JSON from a **completed** job run. "
        "Returns 502 if the job has not yet completed or produced no output."
    ),
)
async def get_run_result(
    run_id: int,
    _: ApiKey,
) -> JobResultResponse:
    data = await enrichment_service.get_job_result(run_id)
    return JobResultResponse(run_id=run_id, data=data)
