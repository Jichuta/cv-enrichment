"""Pydantic models for the text extraction endpoint."""

from pydantic import BaseModel, Field


class TextExtractionResponse(BaseModel):
    """Response returned after extracting text from a CV file."""

    filename: str = Field(description="Original uploaded filename")
    file_type: str = Field(description="Detected file type: 'pdf' or 'docx'")
    raw_text: str = Field(description="Full extracted plain text from the document")
    page_count: int = Field(description="Number of pages in the document")
    word_count: int = Field(description="Number of words in the extracted text")
    char_count: int = Field(description="Number of characters in the extracted text")
