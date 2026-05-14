"""
generate_samples.py
Run once to create clean sample documents for testing DocuMind.

Usage:
    python generate_samples.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "sample_docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font paths to try on macOS / Linux
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _font(size: int):
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Sample Invoice ─────────────────────────────────────────────────────────────

def make_invoice():
    W, H = 1240, 1754          # A4 @ 150 DPI
    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    f_xl  = _font(52)
    f_lg  = _font(36)
    f_md  = _font(28)
    f_sm  = _font(22)

    # Header bar
    draw.rectangle([0, 0, W, 130], fill="#1a1a2e")
    draw.text((60, 30), "TECHCORP SOLUTIONS PVT LTD", fill="#ffffff", font=f_xl)

    # Sub-header
    draw.rectangle([0, 130, W, 165], fill="#f59e0b")
    draw.text((60, 138), "TAX INVOICE", fill="#1a1a2e", font=f_md)
    draw.text((900, 138), "ORIGINAL COPY", fill="#1a1a2e", font=f_sm)

    # Invoice metadata
    y = 195
    fields = [
        ("Invoice No:",    "INV-2024-001"),
        ("Invoice Date:",  "15 January 2024"),
        ("Due Date:",      "15 February 2024"),
        ("Customer:",      "Narain Singh"),
        ("Email:",         "narain.singh@example.com"),
        ("Phone:",         "+91 98765 43210"),
        ("GSTIN:",         "27AABCT1332L1ZK"),
        ("PAN:",           "AABCT1332L"),
        ("Address:",       "42, MG Road, Mumbai, Maharashtra 400001"),
    ]
    for label, value in fields:
        draw.text((60,  y), label, fill="#888888", font=f_sm)
        draw.text((340, y), value, fill="#111111", font=f_md)
        draw.line([60, y + 42, W - 60, y + 42], fill="#eeeeee")
        y += 48

    # Line items header
    y += 16
    draw.rectangle([60, y, W - 60, y + 52], fill="#1a1a2e")
    for x, text in [(75, "Description"), (720, "Qty"), (820, "Rate"), (1020, "Amount")]:
        draw.text((x, y + 12), text, fill="#ffffff", font=f_md)
    y += 52

    items = [
        ("Web Development Services",  "1", "Rs 30,000", "Rs 30,000"),
        ("UI/UX Design",              "2", "Rs 5,000",  "Rs 10,000"),
        ("Server Setup & Configuration", "1", "Rs 8,000", "Rs 8,000"),
        ("Annual Maintenance Contract", "1", "Rs 12,000", "Rs 12,000"),
    ]
    for i, (desc, qty, rate, amt) in enumerate(items):
        bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        draw.rectangle([60, y, W - 60, y + 50], fill=bg)
        draw.text((75,  y + 12), desc, fill="#333333", font=f_sm)
        draw.text((720, y + 12), qty,  fill="#333333", font=f_sm)
        draw.text((820, y + 12), rate, fill="#333333", font=f_sm)
        draw.text((1020,y + 12), amt,  fill="#333333", font=f_sm)
        y += 50

    # Totals
    y += 30
    for label, value in [("Subtotal:", "Rs 60,000"), ("GST (18%):", "Rs 10,800")]:
        draw.text((820, y), label, fill="#666666", font=f_sm)
        draw.text((1020,y), value, fill="#333333", font=f_md)
        y += 48

    draw.rectangle([800, y, W - 60, y + 65], fill="#1a1a2e")
    draw.text((820, y + 14), "TOTAL DUE:", fill="#f59e0b", font=f_md)
    draw.text((1010,y + 10), "Rs 70,800", fill="#ffffff", font=f_lg)
    y += 90

    # Footer
    draw.line([60, y, W - 60, y], fill="#dddddd")
    draw.text((60, y + 14), "Bank: HDFC Bank | A/C: 50100123456789 | IFSC: HDFC0001234",
              fill="#888888", font=f_sm)
    draw.text((60, y + 46), "Website: www.techcorp.in | Email: info@techcorp.in",
              fill="#888888", font=f_sm)

    out = os.path.join(OUTPUT_DIR, "sample_invoice.png")
    img.save(out, dpi=(150, 150))
    print(f"✅  Saved {out}")


# ── Sample Business Letter ─────────────────────────────────────────────────────

def make_letter():
    W, H = 1240, 1754
    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    f_lg = _font(34)
    f_md = _font(26)
    f_sm = _font(22)

    y = 60
    draw.text((60, y), "TECHCORP SOLUTIONS PVT LTD", fill="#1a1a2e", font=f_lg)
    draw.text((60, y + 48), "42, MG Road, Mumbai, Maharashtra 400001", fill="#555", font=f_sm)
    draw.text((60, y + 80), "info@techcorp.in | +91 98765 43210", fill="#555", font=f_sm)
    draw.line([60, y + 118, W - 60, y + 118], fill="#1a1a2e", width=3)

    y += 150
    draw.text((60, y), "Date: 15 January 2024", fill="#333", font=f_sm)
    y += 50
    draw.text((60, y), "To,", fill="#333", font=f_md)
    y += 40
    draw.text((60, y), "Mr. Narain Singh", fill="#111", font=f_md)
    draw.text((60, y + 36), "Senior Manager, ABC Enterprises", fill="#555", font=f_sm)
    draw.text((60, y + 68), "Mumbai, Maharashtra", fill="#555", font=f_sm)
    y += 130

    draw.text((60, y), "Subject: Proposal for IT Services", fill="#1a1a2e", font=f_md)
    draw.line([60, y + 40, W - 60, y + 40], fill="#cccccc")
    y += 70

    draw.text((60, y), "Dear Mr. Narain Singh,", fill="#333", font=f_md)
    y += 55

    body = (
        "We are pleased to present our proposal for providing comprehensive IT services "
        "to your esteemed organisation. TechCorp Solutions has been a trusted partner "
        "for over 10 years, delivering excellence in software development, cloud "
        "infrastructure, and managed IT support.\n\n"
        "Our proposed engagement includes web development, UI/UX design, and an annual "
        "maintenance contract. The total investment for the first year amounts to "
        "Rs 70,800 inclusive of GST at 18%.\n\n"
        "We look forward to a long and productive association.\n\n"
        "Yours sincerely,\n"
        "Ravi Kumar\n"
        "Business Development Manager\n"
        "TechCorp Solutions Pvt Ltd\n"
        "ravi.kumar@techcorp.in | +91 91234 56789"
    )
    for para in body.split("\n"):
        draw.text((60, y), para, fill="#333" if para else "#333", font=f_sm)
        y += 36

    out = os.path.join(OUTPUT_DIR, "sample_letter.png")
    img.save(out, dpi=(150, 150))
    print(f"✅  Saved {out}")


# ── Sample Receipt ─────────────────────────────────────────────────────────────

def make_receipt():
    W, H = 600, 900
    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    f_lg = _font(28)
    f_md = _font(22)
    f_sm = _font(18)

    draw.rectangle([0, 0, W, 80], fill="#1a1a2e")
    draw.text((20, 20), "TECHCORP MART", fill="#f59e0b", font=f_lg)

    y = 100
    draw.text((20, y), "Receipt No: REC-2024-0042", fill="#333", font=f_sm)
    draw.text((20, y+28), "Date: 15 Jan 2024  10:42 AM", fill="#333", font=f_sm)
    draw.text((20, y+56), "Customer: Walk-in", fill="#333", font=f_sm)
    y += 100

    draw.line([20, y, W-20, y], fill="#cccccc")
    y += 10
    draw.text((20, y), "Item", fill="#888", font=f_sm)
    draw.text((380, y), "Qty", fill="#888", font=f_sm)
    draw.text((440, y), "Price", fill="#888", font=f_sm)
    y += 32
    draw.line([20, y, W-20, y], fill="#cccccc")
    y += 8

    items = [("Laptop Stand", "1", "Rs 1,499"), ("USB-C Hub", "2", "Rs 1,200"),
             ("HDMI Cable 2m", "1", "Rs 349"), ("Mouse Pad XL", "1", "Rs 599")]
    for desc, qty, price in items:
        draw.text((20, y), desc, fill="#333", font=f_sm)
        draw.text((380,y), qty,  fill="#333", font=f_sm)
        draw.text((440,y), price,fill="#333", font=f_sm)
        y += 34

    y += 10
    draw.line([20, y, W-20, y], fill="#cccccc")
    y += 16
    for label, val in [("Subtotal:", "Rs 3,647"), ("GST (18%):", "Rs 657"),
                        ("Total:", "Rs 4,304")]:
        draw.text((300, y), label, fill="#666", font=f_sm)
        draw.text((430, y), val,   fill="#111", font=f_md)
        y += 36

    draw.rectangle([20, y+10, W-20, y+55], fill="#1a1a2e")
    draw.text((30, y+18), "PAID — Thank you!", fill="#f59e0b", font=f_md)
    y += 80
    draw.text((20, y), "www.techcorp.in | +91 98765 43210", fill="#888", font=f_sm)

    out = os.path.join(OUTPUT_DIR, "sample_receipt.png")
    img.save(out, dpi=(150, 150))
    print(f"✅  Saved {out}")


if __name__ == "__main__":
    print("Generating sample documents…")
    make_invoice()
    make_letter()
    make_receipt()
    print("\nAll samples generated in sample_docs/")
    print("Upload sample_invoice.png in DocuMind for best OCR results.")
