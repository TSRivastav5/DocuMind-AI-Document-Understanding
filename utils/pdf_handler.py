"""
utils/pdf_handler.py
PDF page extraction and routing logic using PyMuPDF (fitz).
- Selectable text PDFs → extract text directly, skip OCR.
- Scanned PDFs → render each page as PIL Image for preprocessing + OCR.
"""
import fitz  # PyMuPDF
from PIL import Image
import io


def open_pdf(pdf_bytes: bytes):
    """Open a PDF from bytes and return the fitz.Document object."""
    return fitz.open(stream=pdf_bytes, filetype="pdf")


def is_scanned_page(page: fitz.Page, min_chars: int = 20) -> bool:
    """Return True if the page contains too little selectable text (likely scanned)."""
    text = page.get_text().strip()
    return len(text) < min_chars


def page_to_pil(page: fitz.Page, dpi: int = 200) -> Image.Image:
    """Render a PDF page as a PIL Image at the given DPI."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("png")
    return Image.open(io.BytesIO(img_bytes))


def extract_page_text(page: fitz.Page) -> str:
    """Extract selectable text directly from a page."""
    return page.get_text()


def get_pdf_info(doc: fitz.Document) -> dict:
    """Return basic metadata about the PDF."""
    return {
        "page_count": doc.page_count,
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "format": doc.metadata.get("format", ""),
    }
