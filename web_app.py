"""
DocuMind Web — Flask server serving the new Editorial-SaaS UI.
The Streamlit app.py is completely untouched; this is a parallel entry-point.
"""
import io, json, os, time, base64, traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from PIL import Image

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    import fitz
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

# ── util imports (same as Streamlit app) ──────────────────────────────────────
from utils.ocr import extract_text, PSM_OPTIONS, DEFAULT_PSM_LABEL, PHOTO_PSM_LABEL
from utils.preprocess import clean_text
from utils.extract import (extract_entities, get_pos_tags,
                            compute_extraction_metrics, build_accuracy_table)
from utils.image_preprocess import assess_image_quality, auto_crop_document
from utils.router import route_ocr_engine

SAMPLE_DIR = Path(__file__).parent / "sample_docs"
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))


# ── helpers ────────────────────────────────────────────────────────────────────
CONF_SCORE = {"high": 1.0, "medium": 0.6, "low": 0.3}


def _process_image(pil_img: Image.Image, mode: str = "standard",
                   psm_config: str = "--oem 3 --psm 6") -> dict:
    timings = {}
    t0 = time.perf_counter()
    ocr_result = extract_text(pil_img, preprocess=True,
                               preprocess_mode=mode, psm_config=psm_config)
    timings["preprocess_ms"] = ocr_result.get("preprocess_ms", 0)
    timings["ocr_ms"] = round((time.perf_counter() - t0) * 1000 - timings["preprocess_ms"], 1)
    raw_text  = ocr_result["text"]
    ocr_conf  = ocr_result["confidence"]
    word_data = ocr_result.get("word_data", {})

    t1 = time.perf_counter()
    pre_result = clean_text(raw_text)
    timings["clean_ms"]   = round((time.perf_counter() - t1) * 1000, 1)
    timings["nlp_pre_ms"] = pre_result["duration_ms"]
    cleaned = pre_result["cleaned"]

    t2 = time.perf_counter()
    ext_result = extract_entities(cleaned)
    timings["extraction_ms"] = round((time.perf_counter() - t2) * 1000, 1)

    pos_tags = get_pos_tags(cleaned)
    entities = ext_result["entities"]

    return {
        "raw_text":       raw_text,
        "cleaned_text":   cleaned,
        "sentences":      pre_result["sentences"],
        "tokens":         pre_result["tokens"],
        "entities":       entities,
        "doc_type":       ext_result.get("doc_type", "general"),
        "model_used":     ext_result.get("model_used", "N/A"),
        "spacy_failed":   ext_result.get("spacy_failed", False),
        "ocr_confidence": ocr_conf,
        "timings":        timings,
        "pos_tags":       pos_tags,
        "config_used":    ocr_result.get("config_used", "N/A"),
    }


# ── routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        f = request.files.get("file")
        if not f:
            return jsonify({"error": "No file uploaded"}), 400

        filename = f.filename.lower()
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if f.content_length and f.content_length > 10 * 1024 * 1024:
            return jsonify({"error": "File exceeds 10 MB limit"}), 400

        raw_bytes = f.read()
        if len(raw_bytes) > 10 * 1024 * 1024:
            return jsonify({"error": "File exceeds 10 MB limit"}), 400

        # ── PDF branch ────────────────────────────────────────────────────────
        if ext == "pdf":
            if not _HAS_FITZ:
                return jsonify({"error": "PDF support requires PyMuPDF"}), 400
            from utils.pdf_handler import (open_pdf, is_scanned_page,
                                           page_to_pil, extract_page_text, get_pdf_info)
            doc   = open_pdf(raw_bytes)
            info  = get_pdf_info(doc)
            page  = doc[0]
            if not is_scanned_page(page):
                raw = extract_page_text(page)
                pre = clean_text(raw)
                ext_r = extract_entities(pre["cleaned"])
                result = {
                    "raw_text":       raw,
                    "cleaned_text":   pre["cleaned"],
                    "sentences":      pre["sentences"],
                    "tokens":         pre["tokens"],
                    "entities":       ext_r["entities"],
                    "doc_type":       ext_r.get("doc_type", "general"),
                    "model_used":     ext_r.get("model_used", "N/A"),
                    "spacy_failed":   ext_r.get("spacy_failed", False),
                    "ocr_confidence": 100.0,
                    "timings": {"preprocess_ms": 0, "ocr_ms": 0,
                                "clean_ms": pre["duration_ms"], "nlp_pre_ms": 0,
                                "extraction_ms": ext_r.get("duration_ms", 0)},
                    "pos_tags": get_pos_tags(pre["cleaned"]),
                    "config_used": "N/A (direct PDF text)",
                    "pdf_info": info,
                }
            else:
                pil_img = page_to_pil(page)
                quality  = assess_image_quality(pil_img)
                routing  = route_ocr_engine(quality, "pdf")
                if routing["engine"] == "reject":
                    return jsonify({"error": "Image quality too low for OCR", "quality": quality}), 422
                cropped, _ = auto_crop_document(pil_img)
                result = _process_image(cropped, routing["mode"], routing["psm"])
                result["pdf_info"] = info
        else:
            # ── Image branch ─────────────────────────────────────────────────
            pil_img  = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            quality  = assess_image_quality(pil_img)
            file_ext = ext if ext else "png"
            routing  = route_ocr_engine(quality, file_ext)

            if routing["engine"] == "reject":
                return jsonify({
                    "error":   "Image quality too low for reliable OCR",
                    "quality": quality,
                    "tips":    "Try a higher-resolution or better-lit scan."
                }), 422

            cropped, crop_strategy = auto_crop_document(pil_img)
            result = _process_image(cropped, routing["mode"], routing["psm"])
            result["quality"]       = quality
            result["routing"]       = {"engine": routing["engine"], "reason": routing["reason"]}
            result["crop_strategy"] = crop_strategy

        # ── Serialise results ─────────────────────────────────────────────────
        entities = result["entities"]
        total_time = sum(result["timings"].values())
        avg_conf = round(
            (sum(CONF_SCORE.get(e["confidence"], 0) for e in entities) / len(entities) * 100)
            if entities else 0, 1
        )
        metrics = compute_extraction_metrics(entities)

        return jsonify({
            "success":        True,
            "raw_text":       result["raw_text"],
            "cleaned_text":   result["cleaned_text"],
            "entities":       entities,
            "doc_type":       result.get("doc_type", "general"),
            "model_used":     result.get("model_used", "N/A"),
            "spacy_failed":   result.get("spacy_failed", False),
            "ocr_confidence": round(result["ocr_confidence"], 1),
            "avg_confidence": avg_conf,
            "total_time_ms":  round(total_time, 1),
            "timings":        result["timings"],
            "entity_count":   len(entities),
            "sentence_count": len(result.get("sentences", [])),
            "token_count":    len(result.get("tokens", [])),
            "metrics":        metrics,
            "config_used":    result.get("config_used", "N/A"),
            "routing":        result.get("routing", {}),
            "filename":       filename,
        })

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/samples", methods=["GET"])
def list_samples():
    samples = []
    if SAMPLE_DIR.exists():
        for p in SAMPLE_DIR.iterdir():
            if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                samples.append({"name": p.stem, "filename": p.name})
    return jsonify(samples)


@app.route("/api/samples/<filename>", methods=["GET"])
def get_sample(filename):
    return send_from_directory(str(SAMPLE_DIR), filename)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
