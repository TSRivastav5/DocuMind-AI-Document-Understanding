"""
utils/image_preprocess.py  — V4
Adds public correct_perspective() with detection feedback,
updates photo pipeline to use it + improved adaptive threshold params,
and adds perspective_warning to quality assessment.

V4 changes:
  • correct_perspective()  — public function, returns (Image, bool)
  • assess_image_quality() — adds perspective_warning via Hough lines
  • _mode_photo()          — calls correct_perspective first, blockSize=31, C=12
  • upscale_for_ocr()      — unchanged but called before denoising
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


# ── Corner ordering (shared by public + private functions) ─────────────────────

def order_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]    # TL — smallest sum
    rect[2] = pts[np.argmax(s)]    # BR — largest sum
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # TR — smallest diff
    rect[3] = pts[np.argmax(diff)] # BL — largest diff
    return rect


# ── Public: Smart Auto-Crop (3-strategy cascade) ──────────────────────────────

def auto_crop_document(pil_image: Image.Image) -> tuple:
    """
    Automatically isolate the document from its background using 3 strategies
    tried in cascade order:

    Strategy 1 — Contour + perspective warp:
        Best when the paper edge is visible and contrasts with the background.
        Returns a flat, de-skewed version of the document.

    Strategy 2 — White/light-region color segmentation:
        Best for white paper on a darker or coloured background (countertop, desk).
        Finds the largest bright connected region and crops to its bounding box.

    Strategy 3 — Edge-based bounding box:
        Falls back to the bounding box of the strongest edge cluster.

    Returns:
        (cropped_pil_image, strategy_used: str | None)
        strategy_used is None if no cropping was done.
    """
    if not _HAS_CV2:
        return pil_image, None

    img_rgb = np.array(pil_image.convert("RGB"))
    h, w    = img_rgb.shape[:2]

    # ── Strategy 1: Contour + perspective warp ─────────────────────────────────
    try:
        gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 40, 120)
        kernel  = np.ones((7, 7), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=3)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours     = sorted(contours, key=cv2.contourArea, reverse=True)

        for c in contours[:8]:
            area  = cv2.contourArea(c)
            peri  = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and area > h * w * 0.10:
                pts  = approx.reshape(4, 2).astype(np.float32)
                rect = order_corners(pts)
                tl, tr, br, bl = rect
                out_w = max(int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))), 800)
                out_h = max(int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))), 600)
                dst   = np.array(
                    [[0, 0], [out_w-1, 0], [out_w-1, out_h-1], [0, out_h-1]],
                    dtype=np.float32,
                )
                M      = cv2.getPerspectiveTransform(rect, dst)
                warped = cv2.warpPerspective(img_rgb, M, (out_w, out_h))
                return Image.fromarray(warped), "perspective warp"
    except Exception:
        pass

    # ── Strategy 2: White/light region color segmentation ──────────────────────
    # Works for white paper against countertops, desks, dark backgrounds.
    try:
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Adaptive brightness threshold — documents are bright relative to background
        mean_brightness = float(gray.mean())
        thresh_value    = max(160, int(mean_brightness * 1.15))
        thresh_value    = min(thresh_value, 230)   # don't go too high

        _, white_mask = cv2.threshold(gray, thresh_value, 255, cv2.THRESH_BINARY)

        # Close holes inside the document area
        close_kernel  = np.ones((30, 30), np.uint8)
        white_mask    = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, close_kernel)

        # Remove tiny noise specks
        open_kernel   = np.ones((15, 15), np.uint8)
        white_mask    = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, open_kernel)

        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > h * w * 0.12:   # must cover ≥12% of image
                x, y, bw, bh = cv2.boundingRect(largest)
                # Generous 1% padding so we don't clip text at edges
                pad_x = max(8, int(w * 0.01))
                pad_y = max(8, int(h * 0.01))
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(w, x + bw + pad_x)
                y2 = min(h, y + bh + pad_y)

                # Only crop if it's meaningfully smaller than the original
                if (x2 - x1) < w * 0.92 or (y2 - y1) < h * 0.92:
                    cropped = pil_image.crop((x1, y1, x2, y2))
                    return cropped, "light-region detection"
    except Exception:
        pass

    # ── Strategy 3: Edge bounding-box crop ─────────────────────────────────────
    try:
        gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 50, 150)
        kernel  = np.ones((10, 10), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > h * w * 0.10:
                x, y, bw, bh = cv2.boundingRect(largest)
                pad = 20
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(w, x + bw + pad)
                y2 = min(h, y + bh + pad)
                if (x2 - x1) < w * 0.92 or (y2 - y1) < h * 0.92:
                    return pil_image.crop((x1, y1, x2, y2)), "edge bounding box"
    except Exception:
        pass

    return pil_image, None


# ── Legacy: Perspective-only wrapper (used internally) ─────────────────────────

def correct_perspective(pil_image: Image.Image) -> tuple:
    """Legacy wrapper — tries only Strategy 1 (perspective warp). Returns (Image, bool)."""
    result, strategy = auto_crop_document(pil_image)
    return result, strategy == "perspective warp"


# ── Image Quality Assessment ───────────────────────────────────────────────────

def assess_image_quality(pil_image: Image.Image) -> dict:
    """
    Score image quality before OCR.
    V4: adds perspective_warning via Hough line analysis.
    """
    if not _HAS_CV2:
        return {
            "overall_score": 50, "resolution_score": 50,
            "blur_score": 50, "contrast_score": 50,
            "is_blurry": False, "is_low_contrast": False,
            "resolution_px": f"{pil_image.width}x{pil_image.height}",
            "laplacian_variance": 0.0,
            "verdict": "unknown",
            "message": "OpenCV unavailable — quality check skipped.",
            "perspective_warning": False,
            "perspective_note": None,
        }

    img  = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    total_px = h * w

    # 1. Resolution
    resolution_score = min(100, int(total_px / (1920 * 1080) * 100))

    # 2. Blur (Laplacian variance)
    lap_var    = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_score = min(100, int(lap_var / 5))
    is_blurry  = lap_var < 100

    # 3. Contrast
    contrast         = float(gray.std())
    contrast_score   = min(100, int(contrast * 2))
    is_low_contrast  = contrast < 30

    # 4. Weighted overall
    overall = int(0.3 * resolution_score + 0.5 * blur_score + 0.2 * contrast_score)

    if overall >= 60:
        verdict, message = "good", None
    elif overall >= 35:
        verdict = "marginal"
        message = "Image quality is marginal. Results may be inaccurate. Try a clearer photo or scan."
    else:
        verdict = "poor"
        message = "Image quality is too low for reliable OCR. Please upload a clearer image."

    # 5. Perspective distortion check (V4)
    perspective_warning = False
    perspective_note    = None
    try:
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 50, 150)
        lines   = cv2.HoughLinesP(edges, 1, np.pi / 180,
                                  threshold=100, minLineLength=100, maxLineGap=10)
        if lines is not None:
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 != x1:
                    angles.append(abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))))
            non_straight = sum(
                1 for a in angles
                if not (a < 5 or abs(a - 90) < 5 or a > 175)
            )
            if angles and non_straight > len(angles) * 0.30:
                perspective_warning = True
                perspective_note = ("Document appears to have perspective distortion — "
                                    "auto-correction will be applied in Photo mode.")
    except Exception:
        pass

    return {
        "overall_score":      overall,
        "resolution_score":   resolution_score,
        "blur_score":         blur_score,
        "contrast_score":     contrast_score,
        "is_blurry":          is_blurry,
        "is_low_contrast":    is_low_contrast,
        "resolution_px":      f"{w}x{h}",
        "laplacian_variance": round(lap_var, 1),
        "verdict":            verdict,
        "message":            message,
        "perspective_warning": perspective_warning,
        "perspective_note":    perspective_note,
    }


# ── Upscaling helper ───────────────────────────────────────────────────────────

def upscale_for_ocr(gray: np.ndarray, target_min: int = 2000) -> np.ndarray:
    """Upscale so shorter dimension ≥ target_min. Uses INTER_CUBIC."""
    h, w    = gray.shape
    shorter = min(h, w)
    if shorter >= target_min:
        return gray
    scale = target_min / shorter
    return cv2.resize(gray, (int(w * scale), int(h * scale)),
                      interpolation=cv2.INTER_CUBIC)


# ── Public API ─────────────────────────────────────────────────────────────────

def preprocess_for_ocr(pil_image: Image.Image, mode: str = "standard") -> Image.Image:
    """
    Preprocess a PIL Image for OCR.
    mode: 'standard' | 'aggressive' | 'photo'
    Returns preprocessed Image (single value — callers that need perspective
    correction status should call correct_perspective() beforehand).
    """
    if _HAS_CV2:
        return _preprocess_cv2(pil_image, mode=mode)
    return _preprocess_pil(pil_image)


def preprocess_image(pil_image: Image.Image, photo_mode: bool = True) -> Image.Image:
    """Legacy compat alias."""
    return preprocess_for_ocr(pil_image, mode="photo" if photo_mode else "standard")


# ── OpenCV pipelines ───────────────────────────────────────────────────────────

def _preprocess_cv2(pil_image: Image.Image, mode: str) -> Image.Image:
    img_rgb = np.array(pil_image.convert("RGB"))
    gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    if mode == "standard":
        return _mode_standard(gray)
    if mode == "aggressive":
        return _mode_aggressive(gray)
    if mode == "photo":
        return _mode_photo(pil_image)   # photo mode takes PIL (runs correction)
    return Image.fromarray(gray)


def _mode_standard(gray: np.ndarray) -> Image.Image:
    """Clean flatbed scans — Otsu binarisation."""
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)


def _mode_aggressive(gray: np.ndarray) -> Image.Image:
    """Noisy / faded docs — adaptive threshold + morphological cleanup."""
    denoised = cv2.fastNlMeansDenoising(gray, h=20)
    blurred  = cv2.GaussianBlur(denoised, (3, 3), 0)
    binary   = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )
    kernel  = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return Image.fromarray(cleaned)


def _mode_photo(pil_image: Image.Image) -> Image.Image:
    """
    WhatsApp / camera photos — V4 pipeline:
    1. Perspective correction (correct_perspective)
    2. Upscale to ≥2000px shorter side
    3. CLAHE contrast enhancement
    4. Denoise
    5. Adaptive threshold (blockSize=31, C=12) for uneven lighting
    6. Light morphological cleanup
    7. Deskew
    """
    # Step 1 — Perspective correction (V4: using the new public function)
    corrected, _ = correct_perspective(pil_image)
    img_rgb = np.array(corrected.convert("RGB"))
    gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Step 2 — Upscale BEFORE denoising
    gray = upscale_for_ocr(gray, target_min=2000)

    # Step 3 — CLAHE for uneven / gradient lighting
    clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Step 4 — Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, h=15)

    # Step 5 — Adaptive threshold (V4: blockSize=31, C=12 for uneven lighting)
    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,   # handles larger lighting gradients (bent/curved paper)
        C=12,           # more aggressive noise removal
    )

    # Step 6 — Light morphological cleanup
    kernel  = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Step 7 — Deskew
    cleaned = _deskew(cleaned)

    return Image.fromarray(cleaned)


# ── Deskew ─────────────────────────────────────────────────────────────────────

def _deskew(image: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(image < 128))
    if len(coords) == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.5:
        return image
    h, w = image.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


# ── PIL-only fallback ──────────────────────────────────────────────────────────

def _preprocess_pil(pil_image: Image.Image) -> Image.Image:
    img = pil_image.convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)
    return img
