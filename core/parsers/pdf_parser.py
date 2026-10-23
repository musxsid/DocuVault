"""
DocuVaultAI — PDF Parser (Unit 4: PyMuPDF with Fallback Handling)
Extracts page-by-page text from PDF documents using PyMuPDF (fitz),
with structured page metadata for exact citation generation.
"""

from pathlib import Path
from typing import Any, Dict, List

from core.exceptions import ParsingError

# Try importing pymupdf (modern) or fitz with graceful fallback
try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False


class PDFDocumentParser:
    """Parses PDF documents page by page with text extraction and citation metadata."""

    @classmethod
    def parse_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Extracts text from PDF file page by page.
        Returns a dictionary with page count, page-by-page chunks, and full text.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"PDF file not found: {filepath}")

        pages_data: List[Dict[str, Any]] = []
        full_text_list: List[str] = []

        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(filepath)
                total_pages = len(doc)
                for page_idx in range(total_pages):
                    page = doc[page_idx]
                    page_text = page.get_text("text") or ""
                    cleaned_text = page_text.strip()
                    pages_data.append({
                        "page_number": page_idx + 1,
                        "text": cleaned_text,
                        "char_count": len(cleaned_text),
                    })
                    if cleaned_text:
                        full_text_list.append(f"--- Page {page_idx + 1} ---\n{cleaned_text}")
                doc.close()
            except Exception as e:
                raise ParsingError(
                    parser_name="PyMuPDFParser",
                    filepath=filepath,
                    reason=f"Failed to read PDF document: {str(e)}",
                )
        else:
            # Fallback text extractor: attempt simple stream / ASCII extraction
            try:
                with open(filepath, "rb") as f:
                    raw_bytes = f.read()
                # Simple heuristic string extraction from PDF stream
                ascii_text = "".join(
                    chr(b) if 32 <= b <= 126 or b in (10, 13, 9) else " "
                    for b in raw_bytes
                )
                pages_data.append({
                    "page_number": 1,
                    "text": ascii_text.strip(),
                    "char_count": len(ascii_text),
                })
                full_text_list.append(ascii_text.strip())
            except Exception as e:
                raise ParsingError(
                    parser_name="FallbackPDFParser",
                    filepath=filepath,
                    reason=f"Fallback PDF extractor failed: {str(e)}",
                )

        combined_text = "\n\n".join(full_text_list)
        return {
            "filepath": filepath,
            "filename": Path(filepath).name,
            "total_pages": len(pages_data),
            "pages": pages_data,
            "raw_text": combined_text,
        }

    @classmethod
    def extract_text(cls, filepath: str) -> str:
        """Convenience method returning plain text extracted from PDF."""
        data = cls.parse_file(filepath)
        return data.get("raw_text", "")
