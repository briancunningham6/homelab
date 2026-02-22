"""Document parsing tool for extracting text from uploaded files."""
from pathlib import Path
from typing import List
import uuid

from .base import BaseTool, ToolParameter, ToolResult


class DocumentParserTool(BaseTool):
    """Extract and parse text from mission files (PDFs, images, documents)."""

    @property
    def name(self) -> str:
        return "parse_document"

    @property
    def description(self) -> str:
        return "Extract text and structured information from uploaded mission files. Use this to read PDFs, extract text from images (OCR), or parse document content."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_id",
                type="string",
                description="UUID of the mission file to parse",
                required=True,
            ),
            ToolParameter(
                name="extraction_type",
                type="string",
                description="Type of extraction: 'text' (default), 'structured', or 'tables'",
                required=False,
                enum=["text", "structured", "tables"],
            ),
        ]

    async def execute(
        self, file_id: str, extraction_type: str = "text", **kwargs
    ) -> ToolResult:
        """Parse a mission file and extract content.

        Args:
            file_id: UUID of the file to parse
            extraction_type: Type of extraction to perform

        Returns:
            ToolResult with extracted content
        """
        try:
            # Import here to avoid circular dependency
            from app.models.mission_file import MissionFile
            from app.database import SessionLocal

            # Get file from database
            db = SessionLocal()
            try:
                file_obj = db.query(MissionFile).filter(
                    MissionFile.id == uuid.UUID(file_id)
                ).first()

                if not file_obj:
                    return ToolResult(
                        success=False,
                        error=f"File {file_id} not found",
                    )

                # Check if we already have extracted text
                if file_obj.extracted_text and extraction_type == "text":
                    return ToolResult(
                        success=True,
                        data={
                            "text": file_obj.extracted_text,
                            "filename": file_obj.original_name,
                            "cached": True,
                        },
                        metadata={
                            "file_id": str(file_obj.id),
                            "mime_type": file_obj.mime_type,
                        },
                    )

                # Extract text based on file type
                FILES_DIR = Path("/app/data/files")
                file_path = FILES_DIR / file_obj.storage_path

                if not file_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found at {file_obj.storage_path}",
                    )

                extracted_text = None
                mime_type = file_obj.mime_type or ""

                # PDF files
                if mime_type == "application/pdf" or file_obj.original_name.lower().endswith('.pdf'):
                    extracted_text = self._extract_from_pdf(file_path, extraction_type)

                # Images (for OCR)
                elif mime_type.startswith('image/'):
                    extracted_text = self._extract_from_image(file_path)

                # Word documents
                elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_obj.original_name.lower().endswith('.docx'):
                    extracted_text = self._extract_from_docx(file_path)

                # Plain text
                elif mime_type.startswith('text/') or file_obj.original_name.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        extracted_text = f.read()

                # CSV/Excel
                elif file_obj.original_name.lower().endswith(('.csv', '.xlsx', '.xls')):
                    extracted_text = self._extract_from_spreadsheet(file_path, extraction_type)

                else:
                    return ToolResult(
                        success=False,
                        error=f"Unsupported file type: {mime_type or 'unknown'}",
                    )

                if not extracted_text:
                    return ToolResult(
                        success=False,
                        error="No text could be extracted from the file",
                    )

                # Cache the extracted text
                file_obj.extracted_text = extracted_text
                db.commit()

                return ToolResult(
                    success=True,
                    data={
                        "text": extracted_text,
                        "filename": file_obj.original_name,
                        "cached": False,
                        "char_count": len(extracted_text),
                    },
                    metadata={
                        "file_id": str(file_obj.id),
                        "mime_type": file_obj.mime_type,
                        "extraction_type": extraction_type,
                    },
                )

            finally:
                db.close()

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Document parsing failed: {str(e)}",
            )

    def _extract_from_pdf(self, file_path: Path, extraction_type: str) -> str:
        """Extract text from PDF using PyPDF2."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        if extraction_type == "structured":
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                        else:
                            text_parts.append(page_text)
                except Exception as e:
                    text_parts.append(f"[Error extracting page {page_num}: {str(e)}]")

            return "\n\n".join(text_parts)

        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")

    def _extract_from_image(self, file_path: Path) -> str:
        """Extract text from image using OCR (pytesseract)."""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(str(file_path))
            text = pytesseract.image_to_string(image)
            return text

        except ImportError:
            raise Exception("OCR not available. Install pytesseract and Tesseract-OCR.")
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")

    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from Word document."""
        try:
            from docx import Document

            doc = Document(str(file_path))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)

        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")

    def _extract_from_spreadsheet(self, file_path: Path, extraction_type: str) -> str:
        """Extract data from CSV or Excel files."""
        try:
            import pandas as pd

            # Read the file
            if str(file_path).lower().endswith('.csv'):
                df = pd.read_csv(str(file_path))
            else:
                df = pd.read_excel(str(file_path))

            # Convert to text representation
            if extraction_type == "structured":
                # Include column headers and preserve structure
                return df.to_string(index=False)
            elif extraction_type == "tables":
                # Markdown table format
                return df.to_markdown(index=False)
            else:
                # Simple text extraction
                return df.to_csv(index=False)

        except Exception as e:
            raise Exception(f"Spreadsheet extraction failed: {str(e)}")
