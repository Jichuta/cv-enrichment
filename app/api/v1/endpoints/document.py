"""CV document generation endpoint.

Route:
  POST /api/v1/cv/generate-document  — Receive enriched CV JSON, return a formatted file.
"""

import logging

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import ApiKey
from app.schemas.document import GenerateCVRequest
from app.services.document_generation import generate_docx, generate_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PDF_MIME   = "application/pdf"


@router.post(
    "/generate-document",
    status_code=200,
    summary="Generate a formatted CV document",
    description=(
        "Receives enriched CV data as JSON and returns a formatted document file.\n\n"
        "- **format=docx** *(default)*: returns a styled `.docx` file via `python-docx`.\n"
        "- **format=pdf**: returns a PDF via WeasyPrint (requires system dependencies — "
        "works in Docker, requires GTK+ runtime on Windows).\n\n"
        "Use the **template** parameter to select a branded layout. "
        "Available templates map to subfolders inside `templates/`."
    ),
    responses={
        200: {
            "content": {
                _DOCX_MIME: {"schema": {"type": "string", "format": "binary"}},
                _PDF_MIME:  {"schema": {"type": "string", "format": "binary"}},
            },
            "description": "Formatted CV file",
        }
    },
)
async def generate_cv_document(
    payload: GenerateCVRequest,
    _: ApiKey,
    template: str = Query(default="assuresoft", description="Template name (subfolder under templates/). Options: assuresoft, assuresoft-internal"),
    format: str   = Query(default="docx", description="Output format: 'docx' or 'pdf'"),
) -> Response:
    safe_name = payload.candidate_name.lower().replace(" ", "_")
    fmt = format.lower()

    if fmt == "pdf":
        content   = generate_pdf(payload, template)
        mime      = _PDF_MIME
        filename  = f"{safe_name}_cv.pdf"
    else:
        content   = generate_docx(payload, template)
        mime      = _DOCX_MIME
        filename  = f"{safe_name}_cv.docx"

    logger.info(
        "Document generated: candidate=%s template=%s format=%s size_kb=%d",
        payload.candidate_name,
        template,
        fmt,
        len(content) // 1024,
    )

    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
