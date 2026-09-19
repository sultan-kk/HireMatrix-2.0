"""
extraction_engine.py
---------------------
Unified document extraction for HireMatrix. Every uploaded file — no
matter its format — ends up as the same shape: a list of line dicts
`{"text", "confidence", "bbox"}`, so parser.py never needs to know what
kind of file it came from.

Format-specific strategy (this is where the real accuracy gains are):

  PNG / JPG / JPEG
      Preprocessed (grayscale, denoise, adaptive threshold, upscale) then
      OCR'd with Tesseract at word level so we get a genuine per-word
      confidence score.

  PDF
      HYBRID extraction — most CVs submitted as PDF are "born digital"
      (exported from Word/Canva/a CV builder), which means the text is
      already selectable and 100% accurate; running OCR on those throws
      away accuracy for no reason. So for each page:
        1. Try to pull the real text layer directly (pdfplumber).
        2. Only if a page has no usable text layer (i.e. it's actually a
           SCANNED image saved as PDF) does it fall back to rendering
           that page to an image and running OCR on it.
      Native text lines get confidence=100 (they're exact, not a guess).

  DOCX
      Read directly via python-docx — paragraphs and table cells become
      lines with confidence=100. No OCR involved at all, so this is the
      most accurate path of the three formats.

Every extractor also returns a "preview", used by the Review tab's left
panel:
    - image/PDF-with-a-rendered-page -> a PIL Image
    - DOCX (no visual page to show)  -> None, so the UI shows the
      extracted text instead of a picture.
"""

import io
import logging
import os

import cv2
import numpy as np
import pytesseract
from PIL import Image

import config

logger = logging.getLogger(__name__)

if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


# ---------------------------------------------------------------------------
# Shared preprocessing + OCR (used by images, and by scanned PDF pages)
# ---------------------------------------------------------------------------
def preprocess_image(pil_image: Image.Image) -> Image.Image:
    """Grayscale -> denoise -> adaptive threshold -> upscale small scans."""
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    h, w = gray.shape
    if max(h, w) < 1500:
        scale = 1500 / max(h, w)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        blockSize=31, C=15,
    )
    return Image.fromarray(thresh)


import streamlit as st
from google import genai

# Streamlit secrets ya local .env se key uthane ka tareeqa
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

# Client initialize karein
client = genai.Client(api_key=api_key)
def ocr_image_to_lines(pil_image, lang: str = "eng") -> list:
    try:
        prompt = (
            "Extract all the text from this resume/CV image accurately. "
            "Maintain the logical reading order, handling multi-column layouts "
            "and sidebars correctly from top to bottom, left to right. "
            "Return the extracted text clearly."
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[pil_image, prompt]
        )
        
        extracted_text = response.text if response and hasattr(response, 'text') else ""
        raw_lines = extracted_text.split("\n")

        results = []
        for line in raw_lines:
            cleaned_line = line.strip()
            if cleaned_line:
                results.append({"text": cleaned_line, "confidence": 1.0})
        return results
      
        st.write("Extracted Lines Results:",results)

    except Exception as e:
        st.error(f"OCR Error: {e}")
        return []
    lines = {}
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        conf = float(data["conf"][i])
        if not word or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if key not in lines:
            lines[key] = {"words": [], "confs": [], "x": data["left"][i], "y": data["top"][i]}
        lines[key]["words"].append(word)
        lines[key]["confs"].append(conf)
        lines[key]["x"] = min(lines[key]["x"], data["left"][i])
        lines[key]["y"] = min(lines[key]["y"], data["top"][i])

    results = []
    for entry in lines.values():
        text = " ".join(entry["words"])
        avg_conf = sum(entry["confs"]) / len(entry["confs"])
        results.append({"text": text, "confidence": round(avg_conf, 1), "bbox": (entry["x"], entry["y"], 0, 0)})
    return results


# ---------------------------------------------------------------------------
# Format: PNG / JPG / JPEG
# ---------------------------------------------------------------------------
def _extract_image(file_bytes: bytes):
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    cleaned = preprocess_image(image)
    lines = ocr_image_to_lines(cleaned)
    notice = None
    return lines, image, notice


# ---------------------------------------------------------------------------
# Format: PDF — hybrid text-layer + OCR-fallback-per-page
# ---------------------------------------------------------------------------
def _extract_pdf(file_bytes: bytes):
    import pdfplumber

    all_lines = []
    preview_image = None
    used_ocr = False
    used_native = False

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                used_native = True
                for raw_line in text.splitlines():
                    raw_line = raw_line.strip()
                    if raw_line:
                        all_lines.append({"text": raw_line, "confidence": 100.0, "bbox": (0, 0, 0, 0)})
            else:
                # No selectable text on this page -> it's a scanned/image
                # page saved as PDF. Render it and OCR it like a photo.
                used_ocr = True
                page_image = _render_pdf_page_to_image(file_bytes, page_num)
                if page_image is not None:
                    cleaned = preprocess_image(page_image)
                    all_lines.extend(ocr_image_to_lines(cleaned))
                    if preview_image is None:
                        preview_image = page_image

            if preview_image is None:
                # Still grab a visual preview of the first page even when
                # its text came from the native layer, purely for the
                # side-by-side UI (not used for extraction).
                preview_image = _render_pdf_page_to_image(file_bytes, page_num)

    if used_ocr and used_native:
        notice = "mixed"
    elif used_ocr:
        notice = "ocr"
    else:
        notice = "native"

    return all_lines, preview_image, notice


def _render_pdf_page_to_image(file_bytes: bytes, page_index: int):
    """Renders a single PDF page to a PIL Image via pdf2image (needs poppler)."""
    try:
        from pdf2image import convert_from_bytes
        kwargs = {"dpi": 300, "first_page": page_index + 1, "last_page": page_index + 1}
        if config.POPPLER_PATH:
            kwargs["poppler_path"] = config.POPPLER_PATH
        pages = convert_from_bytes(file_bytes, **kwargs)
        return pages[0] if pages else None
    except Exception as exc:
        logger.warning("Could not render PDF page %s to an image: %s", page_index, exc)
        return None


# ---------------------------------------------------------------------------
# Format: DOCX — native text, no OCR at all
# ---------------------------------------------------------------------------
def _extract_docx(file_bytes: bytes):
    import docx

    document = docx.Document(io.BytesIO(file_bytes))
    all_lines = []

    for para in document.paragraphs:
        text = para.text.strip()
        if text:
            all_lines.append({"text": text, "confidence": 100.0, "bbox": (0, 0, 0, 0)})

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text.strip()
                if text:
                    all_lines.append({"text": text, "confidence": 100.0, "bbox": (0, 0, 0, 0)})

    return all_lines, None, "native"  # no page image available for DOCX


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def extract_lines_from_file(uploaded_file):
    """
    Dispatches by file extension. Returns:
        (lines, preview_image_or_None, extraction_notice)

    extraction_notice is one of:
        "native" - text came directly from the file (PDF text layer / DOCX)
        "ocr"    - text came from OCR (image, or a scanned PDF page)
        "mixed"  - a multi-page PDF used both native text AND OCR pages
        None     - not applicable
    """
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""

    if ext in ("png", "jpg", "jpeg"):
        return _extract_image(file_bytes)
    if ext == "pdf":
        return _extract_pdf(file_bytes)
    if ext == "docx":
        return _extract_docx(file_bytes)

    raise ValueError(f"Unsupported file type: .{ext}")
