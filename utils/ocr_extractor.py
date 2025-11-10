# utils/ocr_extractor.py
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

import io
from typing import Dict, List, Union
from PIL import Image, ImageOps, UnidentifiedImageError
import pytesseract
import fitz  # PyMuPDF
import os

def _preprocess_image(pil_img: Image.Image) -> Image.Image:
    """Convert to grayscale, autocontrast, resize very large images for speed."""
    img = pil_img.convert("L")
    img = ImageOps.autocontrast(img)
    max_dim = max(img.size)
    if max_dim > 2000:
        scale = 2000 / max_dim
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img

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

def extract_text_from_images(file, save_debug_pages: str = None) -> Dict:
    """
    Extract text via OCR from a PDF.
    Steps:
      1. Try to extract embedded image objects and OCR them.
      2. If no embedded images or you still want OCR of whole pages, render each page to an image (pixmap) and OCR that.

    Args:
      file: bytes / path / file-like
      save_debug_pages: optional folder path to save rendered page images for debugging (helps see what OCR sees)

    Returns:
      dict with keys:
        - pages: list of pages with 'images' list (index, ocr, method)
        - image_count: total images OCRed
        - content: combined OCR text
        - source: "OCR Text from Images"
        - debug: optional info
    """
    try:
        data = _read_bytes(file)
    except Exception as e:
        return {"pages": [], "image_count": 0, "content": "", "error": f"read_error: {e}"}

    if not data:
        return {"pages": [], "image_count": 0, "content": "", "error": "empty_input_stream"}

    try:
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        return {"pages": [], "image_count": 0, "content": "", "error": f"fitz_open_error: {e}"}

    pages_out: List[Dict] = []
    ocr_texts: List[str] = []
    total_images = 0

    # optional debug dir
    if save_debug_pages:
        os.makedirs(save_debug_pages, exist_ok=True)

    for pno in range(len(pdf)):
        page = pdf.load_page(pno)
        page_images = []
        # 1) Try embedded images (XObjects)
        try:
            images = page.get_images(full=True)
        except Exception:
            images = []

        if images:
            for img_index, img in enumerate(images, start=1):
                try:
                    xref = img[0]
                    base_image = pdf.extract_image(xref)
                    image_bytes = base_image.get("image")
                    if not image_bytes:
                        raise ValueError("no_image_bytes")
                    pil_img = Image.open(io.BytesIO(image_bytes))
                except (KeyError, ValueError, UnidentifiedImageError, Exception) as e:
                    page_images.append({"index": img_index, "ocr": "", "method": "embedded", "error": str(e)})
                    continue

                try:
                    pil_img = _preprocess_image(pil_img)
                    ocr_result = pytesseract.image_to_string(pil_img)
                except Exception:
                    ocr_result = ""

                page_images.append({"index": img_index, "ocr": ocr_result, "method": "embedded"})
                ocr_texts.append(f"--- OCR Page {pno+1}, Image {img_index} (embedded) ---\n{ocr_result}\n")
                total_images += 1
        else:
            # 2) Fall back: render full page to an image and OCR that
            try:
                # render at 150-200 dpi-ish (scale factor)
                zoom = 2  # 2 means ~150-200 dpi depending on source
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_bytes))
                if save_debug_pages:
                    fname = os.path.join(save_debug_pages, f"page_{pno+1}.png")
                    pil_img.save(fname)
                pil_img = _preprocess_image(pil_img)
                ocr_result = pytesseract.image_to_string(pil_img)
            except Exception as e:
                pil_img = None
                ocr_result = ""
            page_images.append({"index": 1, "ocr": ocr_result, "method": "rendered_page"})
            ocr_texts.append(f"--- OCR Page {pno+1}, Rendered Page ---\n{ocr_result}\n")
            total_images += 1

        pages_out.append({"page": pno + 1, "images": page_images})

    combined = "\n".join(ocr_texts).strip()
    return {
        "pages": pages_out,
        "image_count": total_images,
        "content": combined,
        "source": "OCR Text from Images",
        "debug": {"pages_total": len(pdf)}
    }
