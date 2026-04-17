"""CV enrichment business logic.

Provides three enrichment strategies:
  1. enrich_via_job()    — async job-trigger + poll + parse (Databricks pipeline)
  2. trigger_job_async() — fire-and-forget; returns run_id for polling
  3. enrich_via_llm()    — direct LLM call, no job required (faster, no Delta write)
"""

import json
import logging
from typing import Any

from app.core.config import settings
from app.core.exceptions import OutputParseError
from app.schemas.enrich import DirectEnrichRequest, EnrichCVRequest
from app.services.databricks_jobs import databricks_jobs
from app.services.databricks_llm import databricks_llm
from app.utils.json_parser import extract_json_from_logs

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Orchestrates all CV enrichment flows."""

    # ── Job-Based Enrichment ──────────────────────────────────────────────────

    async def trigger_job_async(
        self,
        request: EnrichCVRequest,
        job_id: int | None = None,
    ) -> int:
        """
        Trigger the Databricks enrichment job without waiting.

        Returns:
            run_id (int) — use this to poll status and fetch the result later.
        """
        effective_job_id = job_id or settings.DATABRICKS_ENRICHMENT_JOB_ID
        candidate_id = request.greenhouse_parse_data.candidate_id

        # Serialize the full payload as a single JSON string passed via --input_data
        input_data = request.model_dump(by_alias=True)
        python_params = ["--input_data", json.dumps(input_data)]

        logger.info(
            "Async trigger — job_id=%s candidate_id=%s",
            effective_job_id,
            candidate_id,
        )
        return await databricks_jobs.trigger_job(effective_job_id, python_params)

    async def enrich_via_job(
        self,
        request: EnrichCVRequest,
        job_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Trigger the Databricks enrichment job and wait for the result.

        Returns:
            Parsed JSON dict from the job's stdout logs.

        Raises:
            DatabricksJobFailedError, DatabricksTimeoutError, OutputParseError
        """
        effective_job_id = job_id or settings.DATABRICKS_ENRICHMENT_JOB_ID
        candidate_id = request.greenhouse_parse_data.candidate_id

        input_data = request.model_dump(by_alias=True)
        python_params = ["--input_data", json.dumps(input_data)]

        logger.info(
            "Sync enrichment — job_id=%s candidate_id=%s",
            effective_job_id,
            candidate_id,
        )
        return await databricks_jobs.trigger_and_wait(effective_job_id, python_params)

    # ── Status / Result Polling ───────────────────────────────────────────────

    async def get_job_status(self, run_id: int) -> dict[str, Any]:
        """Return the current status of an enrichment job run."""
        status = await databricks_jobs.get_run_status(run_id)
        lifecycle = status["lifecycle_state"]
        return {
            **status,
            "run_id": run_id,
            "is_complete": lifecycle in {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"},
            "is_success": status.get("result_state") == "SUCCESS",
        }

    async def get_job_result(self, run_id: int) -> dict[str, Any]:
        """
        Fetch and parse the enriched CV JSON from a completed job run.

        Raises:
            OutputParseError: If the job produced no parseable JSON.
        """
        output = await databricks_jobs.get_run_output(run_id)
        logs: str = output.get("logs", "")

        if not logs:
            raise OutputParseError(
                f"Run {run_id} produced no output logs",
                details={"run_id": run_id},
            )
        try:
            return extract_json_from_logs(logs)
        except ValueError as exc:
            raise OutputParseError(str(exc), details={"run_id": run_id}) from exc

    # ── Direct LLM Enrichment ─────────────────────────────────────────────────

    async def enrich_via_llm(self, request: DirectEnrichRequest) -> dict[str, Any]:
        """
        Enrich a CV by calling Databricks Model Serving directly.

        Faster than job-based enrichment; does NOT write to Delta tables.
        """
        prompt = databricks_llm.build_enrichment_prompt(
            cv_text=request.cv_text,
            job_title=request.job_title,
            job_requirements=request.job_requirements,
            candidate_name=request.candidate_name,
        )
        logger.info("Direct LLM enrichment — job=%s", request.job_title)
        return await databricks_llm.complete_json(prompt)


# Module-level singleton
enrichment_service = EnrichmentService()
