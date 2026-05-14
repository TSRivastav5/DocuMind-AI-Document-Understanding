"""
utils/ocr.py  — V3
OCR extraction using pytesseract.
• NO char_whitelist (avoids character hallucination on blurry images)
• DPI hint for upscaled images
• PSM 11 auto-selected for photo mode
"""
import time
import pytesseract
from PIL import Image, ImageDraw

# PSM config map — no whitelist, clean configs only
PSM_OPTIONS = {
    "PSM 6 — Uniform text block (invoices/forms)": "--oem 3 --psm 6",
    "PSM 11 — Sparse text (receipts/photos)":       "--oem 3 --psm 11",
    "PSM 4 — Single column (reports/letters)":      "--oem 3 --psm 4",
    "PSM 3 — Fully automatic (default)":            "--oem 3 --psm 3",
}
DEFAULT_PSM_LABEL = "PSM 6 — Uniform text block (invoices/forms)"

# Separate default for photo mode
PHOTO_PSM_LABEL = "PSM 11 — Sparse text (receipts/photos)"


def _build_config(psm_flags: str, dpi: int = 150) -> str:
    """Build Tesseract config string — no whitelist, with DPI hint."""
    return f"{psm_flags} --dpi {dpi}"


def extract_text(
    image: Image.Image,
    preprocess: bool = True,
    photo_mode: bool = True,        # kept for compat
    preprocess_mode: str = "standard",
    psm_config: str = "--oem 3 --psm 6",
    dpi: int = 150,
) -> dict:
    """
    Extract text from a PIL Image using pytesseract.

    Args:
        image:            PIL Image.
        preprocess:       Run OpenCV preprocessing pipeline first.
        photo_mode:       Legacy compat flag.
        preprocess_mode:  'standard' | 'aggressive' | 'photo'
        psm_config:       Tesseract PSM flags (e.g. '--oem 3 --psm 11')
        dpi:              DPI hint for Tesseract (150 for upscaled photos, 300 for scans)

    Returns:
        dict: text, confidence, duration_ms, preprocess_ms, word_data, config_used
    """
    t0 = time.time()
    preprocess_ms = 0.0

    if preprocess:
        from utils.image_preprocess import preprocess_for_ocr
        tp = time.time()
        image = preprocess_for_ocr(image, mode=preprocess_mode)
        preprocess_ms = round((time.time() - tp) * 1000, 1)

    # Auto-bump DPI hint if image is large (was upscaled)
    w, h = image.size
    effective_dpi = 300 if max(w, h) >= 2000 else dpi

    config = _build_config(psm_config, dpi=effective_dpi)

    try:
        data = pytesseract.image_to_data(
            image, config=config, output_type=pytesseract.Output.DICT
        )
        raw_text = pytesseract.image_to_string(image, config=config)

        confs = [int(c) for c in data["conf"] if int(c) > 0]
        avg_conf = round(sum(confs) / len(confs), 1) if confs else 0.0
    except Exception:
        raw_text = ""
        data = {}
        avg_conf = 0.0

    duration_ms = round((time.time() - t0) * 1000, 1)

    return {
        "text":          raw_text,
        "confidence":    avg_conf,
        "duration_ms":   duration_ms,
        "preprocess_ms": preprocess_ms,
        "word_data":     data,
        "config_used":   config,
    }


def draw_confidence_heatmap(pil_image: Image.Image, ocr_data: dict) -> Image.Image:
    """
    Draw per-word bounding boxes coloured by OCR confidence:
      green (≥80) → yellow (≥50) → red (<50).
    """
    if not ocr_data or not ocr_data.get("text"):
        return pil_image

    img = pil_image.copy().convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    for i in range(len(ocr_data["text"])):
        word = str(ocr_data["text"][i]).strip()
        conf = int(ocr_data["conf"][i])
        if not word or conf < 0:
            continue
        x = ocr_data["left"][i]
        y = ocr_data["top"][i]
        w = ocr_data["width"][i]
        h = ocr_data["height"][i]
        color = (0, 200, 0, 90) if conf >= 80 else (255, 200, 0, 90) if conf >= 50 else (255, 40, 40, 110)
        draw.rectangle([x, y, x + w, y + h], fill=color)

    from PIL import Image as _PIL
    merged = _PIL.alpha_composite(img, overlay)
    return merged.convert("RGB")
