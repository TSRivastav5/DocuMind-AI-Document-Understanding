"""
utils/router.py
Smart OCR engine routing.

Decides BEFORE processing whether the image is suitable for Tesseract,
needs aggressive mode, or should be rejected with actionable guidance.
"""
from __future__ import annotations


def route_ocr_engine(quality_report: dict, file_ext: str) -> dict:
    """
    Choose the right OCR approach based on image characteristics.

    Returns a dict:
      {
        "engine":  "tesseract_standard" | "tesseract_aggressive" | "reject",
        "psm":     "--oem 3 --psm 6"   | "--oem 3 --psm 11",
        "mode":    "standard"           | "aggressive" | "photo",
        "reason":  str,                 # human-readable routing decision
      }
    """
    ext   = file_ext.lower().lstrip(".")
    score = quality_report.get("overall_score", 0)
    blurry       = quality_report.get("is_blurry", False)
    low_contrast = quality_report.get("is_low_contrast", False)
    has_persp    = quality_report.get("perspective_warning", False)

    # ── PDFs always go to standard Tesseract (already flat) ───────────────────
    if ext == "pdf":
        return {
            "engine": "tesseract_standard",
            "psm":    "--oem 3 --psm 6",
            "mode":   "standard",
            "reason": "PDF document — using standard OCR pipeline.",
        }

    # ── High-quality image (screenshot / flatbed scan) ─────────────────────────
    if score >= 70 and not blurry and not has_persp:
        return {
            "engine": "tesseract_standard",
            "psm":    "--oem 3 --psm 6",
            "mode":   "standard",
            "reason": f"High-quality image (score {score}/100) — standard OCR.",
        }

    # ── Decent photo, no heavy distortion — try harder ─────────────────────────
    if score >= 50 and not blurry:
        return {
            "engine": "tesseract_aggressive",
            "psm":    "--oem 3 --psm 11",
            "mode":   "aggressive",
            "reason": (f"Moderate quality image (score {score}/100) — "
                       "using aggressive preprocessing and sparse-text PSM."),
        }

    # ── Poor / blurry / heavy perspective — reject honestly ───────────────────
    reasons = []
    if blurry:
        reasons.append("image is blurry")
    if has_persp:
        reasons.append("strong perspective distortion detected")
    if low_contrast:
        reasons.append("very low contrast")
    if score < 50:
        reasons.append(f"overall quality score is only {score}/100")

    return {
        "engine": "reject",
        "psm":    "--oem 3 --psm 11",
        "mode":   "photo",
        "reason": "Tesseract cannot reliably read this image: " + "; ".join(reasons) + ".",
    }


REJECTION_TIPS = """
**Why Tesseract OCR cannot process this image:**
Tesseract was designed for flat, scanner-quality documents (300+ DPI, horizontal text,
white background). Phone photos of physical documents involve camera angles, paper curl,
JPEG compression, and uneven lighting that cause Tesseract to hallucinate characters.

**✅ For best results, please provide:**
- 📄 A scanned PDF (use a phone scanner app like Adobe Scan, Microsoft Lens, or CamScanner)
- 🖥️ A screenshot of a digital document (email invoice, online receipt)
- 📸 A photo taken **directly overhead** with **flat, even lighting** and **no shadows**

**📱 Free scanner apps that produce clean output:**
- Adobe Scan (iOS/Android) — exports flat-corrected PDF
- Microsoft Lens (iOS/Android) — exports flat-corrected PDF or image
- Google PhotoScan — for documents with glare

**🧪 Or use the sample documents** in the sidebar — they are guaranteed to work at 85–95% confidence.
"""
