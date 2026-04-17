"""API v1 router — aggregates all v1 endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.enrich import router as enrich_router
from app.api.v1.endpoints.extraction import router as extraction_router
from app.api.v1.endpoints.health import router as health_router

router = APIRouter()

router.include_router(health_router,   prefix="/health", tags=["Health"])
router.include_router(enrich_router,   prefix="/cv",     tags=["CV Enrichment"])
router.include_router(extraction_router, prefix="/cv",   tags=["CV Extraction"])
router.include_router(document_router, prefix="/cv",     tags=["CV Document Generation"])
