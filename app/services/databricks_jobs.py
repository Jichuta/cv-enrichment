"""Databricks Jobs REST API 2.0 client.

Handles:
  - Triggering a job run (with optional python_params)
  - Polling until the run reaches a terminal state
  - Fetching and parsing the run output (logs)

All methods are async; use httpx.AsyncClient internally.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    DatabricksError,
    DatabricksJobFailedError,
    DatabricksTimeoutError,
    OutputParseError,
)
from app.utils.json_parser import extract_json_from_logs

logger = logging.getLogger(__name__)

_TERMINAL_STATES = frozenset({"TERMINATED", "SKIPPED", "INTERNAL_ERROR"})


class DatabricksJobsClient:
    """Async wrapper around the Databricks Jobs REST API 2.0."""

    def __init__(self) -> None:
        self._base_url = settings.DATABRICKS_HOST
        self._default_headers = {
            "Authorization": settings.databricks_auth_header,
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._default_headers,
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    async def trigger_job(
        self,
        job_id: int,
        python_params: list[str] | None = None,
    ) -> int:
        """Trigger a Databricks job run and return the run_id."""
        payload: dict[str, Any] = {"job_id": job_id}
        if python_params:
            payload["python_params"] = python_params

        async with self._client() as client:
            try:
                response = await client.post("/api/2.0/jobs/run-now", json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise DatabricksError(
                    f"Failed to trigger job {job_id} (HTTP {exc.response.status_code})",
                    details={"body": exc.response.text[:500]},
                ) from exc
            except httpx.RequestError as exc:
                raise DatabricksError(
                    f"Network error triggering job {job_id}: {exc}"
                ) from exc

        run_id: int = response.json()["run_id"]
        logger.info("Triggered job_id=%s → run_id=%s", job_id, run_id)
        return run_id

    async def get_run_status(self, run_id: int) -> dict[str, Any]:
        """Return the current lifecycle and result state of a run."""
        async with self._client() as client:
            try:
                response = await client.get(
                    "/api/2.0/jobs/runs/get",
                    params={"run_id": run_id},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise DatabricksError(
                    f"Failed to get status for run {run_id} (HTTP {exc.response.status_code})",
                    details={"body": exc.response.text[:500]},
                ) from exc
            except httpx.RequestError as exc:
                raise DatabricksError(
                    f"Network error fetching run {run_id}: {exc}"
                ) from exc

        state = response.json().get("state", {})
        return {
            "lifecycle_state": state.get("life_cycle_state", "UNKNOWN"),
            "result_state": state.get("result_state"),
            "state_message": state.get("state_message", ""),
        }

    async def get_run_output(self, run_id: int) -> dict[str, Any]:
        """Return the raw output payload for a completed run."""
        async with self._client() as client:
            try:
                response = await client.get(
                    "/api/2.0/jobs/runs/get-output",
                    params={"run_id": run_id},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise DatabricksError(
                    f"Failed to get output for run {run_id} (HTTP {exc.response.status_code})",
                    details={"body": exc.response.text[:500]},
                ) from exc
            except httpx.RequestError as exc:
                raise DatabricksError(
                    f"Network error fetching output for run {run_id}: {exc}"
                ) from exc

        return response.json()

    async def wait_for_completion(
        self,
        run_id: int,
        poll_interval: int | None = None,
        timeout_secs: int | None = None,
    ) -> dict[str, Any]:
        """
        Poll run_id until it reaches a terminal state.

        Returns the final status dict.
        Raises DatabricksTimeoutError if the job doesn't finish in time.
        """
        poll_interval = poll_interval or settings.DATABRICKS_JOB_POLL_INTERVAL_SECS
        timeout_secs = timeout_secs or settings.DATABRICKS_JOB_TIMEOUT_SECS
        deadline = time.monotonic() + timeout_secs

        while True:
            status = await self.get_run_status(run_id)
            lifecycle = status["lifecycle_state"]

            logger.debug(
                "run_id=%s | lifecycle=%s | result=%s",
                run_id,
                lifecycle,
                status.get("result_state", "—"),
            )

            if lifecycle in _TERMINAL_STATES:
                return status

            if time.monotonic() >= deadline:
                raise DatabricksTimeoutError(run_id, timeout_secs)

            await asyncio.sleep(poll_interval)

    async def trigger_and_wait(
        self,
        job_id: int,
        python_params: list[str] | None = None,
        poll_interval: int | None = None,
        timeout_secs: int | None = None,
    ) -> dict[str, Any]:
        """
        Trigger a job, wait for it to complete, and return the parsed JSON output.

        Raises:
            DatabricksJobFailedError: If the job terminates with a non-SUCCESS state.
            DatabricksTimeoutError:   If the job doesn't finish within timeout_secs.
            OutputParseError:         If the logs contain no parseable JSON.
        """
        run_id = await self.trigger_job(job_id, python_params)
        final_status = await self.wait_for_completion(
            run_id, poll_interval, timeout_secs
        )

        result_state = final_status.get("result_state")
        if result_state != "SUCCESS":
            raise DatabricksJobFailedError(
                run_id, final_status.get("state_message", "")
            )

        output = await self.get_run_output(run_id)
        logs: str = output.get("logs", "")

        if not logs:
            raise OutputParseError(
                f"Job run {run_id} completed but produced no output",
                details={"run_id": run_id},
            )

        try:
            return extract_json_from_logs(logs)
        except ValueError as exc:
            raise OutputParseError(str(exc), details={"run_id": run_id}) from exc

    async def check_connectivity(self, job_id: int) -> bool:
        """Return True if the Databricks host is reachable and the job exists."""
        async with self._client() as client:
            try:
                response = await client.get(
                    "/api/2.0/jobs/get",
                    params={"job_id": job_id},
                    timeout=5.0,
                )
                return response.status_code == 200
            except Exception:
                return False


# Module-level singleton — import this instead of instantiating directly
databricks_jobs = DatabricksJobsClient()
