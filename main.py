import io
import os
import traceback
import streamlit as st

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from utils.pdf_parser import extract_text_from_pdf
from utils.ocr_extractor import extract_text_from_images
from utils.output_formatter import combine_results

st.set_page_config(page_title="PDF Text Extraction App (Debug)", layout="wide")
st.title("PDF Text Extraction App — Native + OCR (Debug mode)")

st.markdown("Upload a PDF. This debug build will render page images and show what Tesseract sees.")

zoom = st.sidebar.slider("Render zoom (increase to improve OCR; larger = slower)", min_value=1, max_value=4, value=2)
save_debug = st.sidebar.checkbox("Save debug page images to server (debug_pages/)", value=True)
lang = st.sidebar.text_input("Tesseract language code (leave blank for 'eng')", value="")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

def _clear_debug_dir(path="debug_pages"):
    if os.path.exists(path):
        for f in os.listdir(path):
            try:
                os.remove(os.path.join(path, f))
            except Exception:
                pass
    else:
        os.makedirs(path, exist_ok=True)

if uploaded_file:
    try:
        file_bytes = uploaded_file.read()
        if not file_bytes:
            st.error("Uploaded file is empty. Try re-uploading.")
            st.stop()

        native_stream = io.BytesIO(file_bytes)

        with st.spinner("Extracting native text..."):
            native = extract_text_from_pdf(native_stream)

        debug_dir = "debug_pages"
        if save_debug:
            _clear_debug_dir(debug_dir)
        else:
            os.makedirs(debug_dir, exist_ok=True)

        with st.spinner("Running OCR (this may take a while)..."):
            ocr = extract_text_from_images(io.BytesIO(file_bytes), save_debug_pages=debug_dir)

        result = combine_results(native, ocr)

        st.success("Extraction complete ✅")

        st.subheader("Metadata / Status")
        cols = st.columns(2)
        with cols[0]:
            st.markdown("**Native extraction**")
            st.write({
                "page_count": native.get("page_count"),
                "metadata": native.get("metadata"),
                "error": native.get("error")
            })
        with cols[1]:
            st.markdown("**OCR extraction**")
            st.write({
                "image_count": ocr.get("image_count"),
                "pages_total": ocr.get("debug", {}).get("pages_total"),
                "error": ocr.get("error")
            })

        st.subheader("Native Text (preview)")
        st.text_area("Native preview", result.get("native_preview", "") or "(no native text)", height=200)

        st.subheader("OCR Text (preview)")
        st.text_area("OCR preview", result.get("ocr_preview", "") or "(no OCR text)", height=200)

        st.subheader("Per-page OCR results (detailed)")
        for p in ocr.get("pages", []):
            st.markdown(f"### Page {p.get('page')}")
            for img in p.get("images", []):
                method = img.get("method", "embedded")
                st.markdown(f"**Image {img.get('index')} — method:** {method}")
                if img.get("error"):
                    st.error(f"Image error: {img.get('error')}")
                st.text_area(f"OCR text (page {p.get('page')} img {img.get('index')})", img.get("ocr", "") or "(empty)", height=120)

        st.subheader("Rendered / extracted images (what Tesseract saw)")
        debug_files = sorted([f for f in os.listdir(debug_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        if debug_files:
            for fname in debug_files:
                path = os.path.join(debug_dir, fname)
                st.markdown(f"**{fname}**")
                st.image(path, use_column_width=True)
        else:
            st.info("No debug images saved. Make sure 'Save debug page images' is checked in the sidebar.")

        st.download_button("Download TXT", result["txt"].encode("utf-8"), file_name="extracted.txt", mime="text/plain")
        st.download_button("Download JSON", result["json"].encode("utf-8"), file_name="extracted.json", mime="application/json")
        st.download_button("Download MD", result["md"].encode("utf-8"), file_name="extracted.md", mime="text/markdown")

    except Exception as e:
        st.error("An unexpected error occurred. See details below.")
        st.code(traceback.format_exc(), language="python")
