import json
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def combine_results(native, ocr):
    native_source = native.get("source", "Native Text")
    native_content = native.get("content", "").strip()

    ocr_source = ocr.get("source", "OCR Text from Images")
    ocr_content = ocr.get("content", "").strip()

    combined = (
        f"## {native_source}\n"
        f"{native_content or '(No native text found)'}\n\n"
        f"## {ocr_source}\n"
        f"{ocr_content or '(No OCR text found)'}"
    )

    preview_native = (native_content[:500] + "...") if len(native_content) > 500 else native_content
    preview_ocr = (ocr_content[:500] + "...") if len(ocr_content) > 500 else ocr_content

    combined_json = json.dumps(
        {"native": native, "ocr": ocr},
        indent=2,
        ensure_ascii=False
    )

    return {
        "txt": combined,
        "json": combined_json,
        "md": combined,
        "native_preview": preview_native,
        "ocr_preview": preview_ocr,
    }
