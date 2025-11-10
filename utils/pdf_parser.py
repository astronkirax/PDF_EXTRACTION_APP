import io
from typing import Dict, List, Union
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _read_bytes(file: Union[str, bytes, io.BytesIO]):
    if isinstance(file, bytes):
        return file
    if isinstance(file, str):
        with open(file, "rb") as f:
            return f.read()
    try:
        file.seek(0)
    except Exception:
        pass
    return file.read()

def extract_text_from_pdf(file) -> Dict:
    try:
        data = _read_bytes(file)
    except Exception as e:
        return {"source": "Native Text", "content": "", "pages": [], "page_count": 0, "metadata": {}, "error": f"read_error: {e}"}

    if not data:
        return {"source": "Native Text", "content": "", "pages": [], "page_count": 0, "metadata": {}, "error": "empty_input_stream"}

    pages_out: List[Dict] = []
    combined_parts: List[str] = []
    metadata = {}

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            try:
                metadata = pdf.metadata or {}
            except Exception:
                metadata = {}

            for i, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                pages_out.append({"page": i, "text": text})
                combined_parts.append(f"--- Page {i} ---\n{text}\n")
            page_count = len(pages_out)
            combined_text = "\n".join(combined_parts).strip()
            return {
                "source": "Native Text",
                "content": combined_text,
                "pages": pages_out,
                "page_count": page_count,
                "metadata": metadata,
                "error": None
            }
    except Exception as e:
        return {
            "source": "Native Text",
            "content": "",
            "pages": [],
            "page_count": 0,
            "metadata": {},
            "error": f"pdfplumber_open_error: {e}"
        }
