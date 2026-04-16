"""Text extraction endpoint.

Route:
  POST /api/v1/cv/extract-text  — Upload a PDF or DOCX CV and receive extracted plain text.
"""

import logging

from fastapi import APIRouter, File, UploadFile

from app.api.deps import ApiKey
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.schemas.extraction import TextExtractionResponse
from app.services.text_extraction import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    SUPPORTED_TYPES,
    extract_text,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/extract-text",
    response_model=TextExtractionResponse,
    status_code=200,
    summary="Extract text from a CV file",
    description=(
        "Upload a **PDF** or **DOCX** CV file and receive the full extracted plain text "
        "along with page count, word count, and character count.\n\n"
        "- **PDF**: extracted with `pdfplumber` — handles multi-column layouts and embedded fonts.\n"
        "- **DOCX**: extracted with `python-docx` — captures paragraphs and table cells.\n\n"
        "Maximum file size: **10 MB**. Scanned/image-only PDFs are not supported (no OCR)."
    ),
)
async def extract_cv_text(
    _: ApiKey,
    file: UploadFile = File(..., description="CV file to extract text from (.pdf or .docx)"),
) -> TextExtractionResponse:
    # Validate content type
    if file.content_type not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(
            content_type=file.content_type or "unknown",
            filename=file.filename or "",
        )

    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(max_mb=MAX_FILE_SIZE_MB)

    logger.info(
        "Text extraction request: file=%s type=%s size_kb=%d",
        file.filename,
        file.content_type,
        len(file_bytes) // 1024,
    )

    return extract_text(
        file_bytes=file_bytes,
        filename=file.filename or "unknown",
        content_type=file.content_type,
    )
