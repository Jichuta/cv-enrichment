"""Health check endpoint — GET /api/v1/health"""

import logging

from fastapi import APIRouter

from app.core.config import settings
from app.services.databricks_jobs import databricks_jobs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    summary="Service health check",
    response_model=dict,
    responses={
        200: {"description": "Service is healthy or degraded (check body for details)"}
    },
)
async def health_check() -> dict:
    """
    Returns service health and the connectivity status of external dependencies.

    This endpoint is intentionally **unauthenticated** so load balancers and
    monitoring tools can probe it without credentials.
    """
    health: dict = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "dependencies": {},
    }

    # Probe Databricks (non-fatal — service still works if degraded)
    databricks_ok = await databricks_jobs.check_connectivity(
        settings.DATABRICKS_ENRICHMENT_JOB_ID
    )
    health["dependencies"]["databricks"] = "healthy" if databricks_ok else "unreachable"

    if not databricks_ok:
        health["status"] = "degraded"
        logger.warning("Health check: Databricks unreachable")

    return health
