# DocuMind — AI Document Intelligence

> **Extract every name, date, amount & clause from any document — in milliseconds.**

DocuMind is an AI-powered document understanding tool that accepts PDF, DOCX, and scanned image uploads, runs OCR via Tesseract and NLP via spaCy, then surfaces every named entity — people, organizations, dates, monetary values, legal clauses, and more — in a clean, interactive web UI.

---

## ✨ Features

| Feature | Description |
|---|---|
| **OCR Engine** | Tesseract with configurable PSM modes (0–13) and preprocessing (Standard / Aggressive / Photo) |
| **NLP Extraction** | spaCy `en_core_web_sm` extracts PERSON, ORG, DATE, MONEY, GPE, CARDINAL, PERCENT, TIME, EMAIL, PHONE, GSTIN, PAN, and more |
| **3D Animated Hero** | CSS-only floating 3D document card with staggered word-drop headline and streaming entity tags |
| **Dual View Panel** | Side-by-Side, Raw Only, or Cleaned Only — compare Tesseract raw output vs AI-cleaned text at a glance |
| **Entities Tab** | Grouped by type, color-coded, with confidence badges (HIGH / MEDIUM / LOW) and live filter count |
| **Live Entity Filters** | Toggle any entity type on/off — Entities tab, JSON view, and tab badge all update instantly |
| **PSM Mode Control** | Sidebar settings panel exposes all 9 Tesseract PSM modes with human-readable hints |
| **Pipeline Strip** | After processing: animated OCR → Entities → Confidence status strip with real values |
| **Action Bar** | Export Results, Download JSON, Download CSV, Copy Cleaned Text, Run Another Document |
| **Analysis History** | Last 20 analyses stored in `localStorage` — click any to replay results |
| **Sample Documents** | Built-in sample docs (Invoice, Business Letter) for instant demo without uploading |
| **Template Presets** | Legal / Invoice / Business Letter templates pre-configure entity filters automatically |
| **Mobile Responsive** | Bottom navigation bar, stacked layouts, collapsible settings panel on screens < 1024px |
| **Reduced Motion** | All CSS animations disable cleanly under `prefers-reduced-motion: reduce` |

---

## 🖥️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Web Server | Flask 3.x |
| OCR | Tesseract (via `pytesseract`) |
| Image Preprocessing | OpenCV (`opencv-python-headless`), Pillow |
| NLP | spaCy 3.7+ (`en_core_web_sm`) |
| PDF Handling | PyMuPDF (`fitz`) |
| Text Processing | NLTK |

### Frontend
| Layer | Technology |
|---|---|
| Structure | Vanilla HTML5 |
| Styling | Vanilla CSS (design tokens, CSS custom properties) |
| Logic | Vanilla JavaScript (ES2020, no framework) |
| Fonts | Instrument Serif, Geist Sans, Geist Mono (Google Fonts) |
| Icons | Material Symbols Outlined |
| Animations | Pure CSS `@keyframes` (no GSAP, no Framer Motion) |

---

## 📁 Project Structure

```
doc_understanding_demo/
│
├── web_app.py              # Flask entry point — serves /static/index.html + /api/*
├── app.py                  # Legacy Streamlit app (untouched, parallel entry point)
│
├── static/
│   ├── index.html          # Single-page app shell
│   ├── css/
│   │   └── main.css        # Full design system + animations
│   └── js/
│       └── app.js          # All frontend logic (routing, rendering, filtering, export)
│
├── utils/
│   ├── ocr.py              # Tesseract wrapper, PSM options, confidence scoring
│   ├── preprocess.py       # Text cleaning, tokenization, sentence splitting
│   ├── extract.py          # spaCy NER, entity classification, metrics
│   ├── image_preprocess.py # Adaptive thresholding, perspective correction, auto-crop
│   ├── router.py           # Quality assessment → OCR engine routing
│   ├── pdf_handler.py      # PyMuPDF page extraction, scanned vs native PDF detection
│   └── ui_helpers.py       # Shared formatting utilities
│
├── sample_docs/            # Sample documents for demo (PNG/JPG)
├── uploads/                # Temp upload directory (auto-created)
├── docs/                   # Internal documentation
│
├── Dockerfile              # Container build for Render deployment
├── requirements.txt        # Python dependencies
└── packages.txt            # System packages (Tesseract, libGL)
```

---

## 🚀 Running Locally

### Prerequisites

- Python 3.10+
- Tesseract OCR installed on your system

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Install & Run

```bash
# 1. Clone the repo
git clone https://github.com/your-username/doc_understanding_demo.git
cd doc_understanding_demo

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download the spaCy model
python -m spacy download en_core_web_sm

# 5. Run the Flask web server
python web_app.py
```

The app will start at **http://localhost:8080**

> **Note:** The legacy Streamlit interface is still available. Run it with `streamlit run app.py` — it is fully independent of the Flask UI.

---

## 🐳 Docker

```bash
# Build the image
docker build -t documind .

# Run the container
docker run -p 8080:8080 documind
```

The `Dockerfile` installs Tesseract, libGL, and all Python dependencies automatically.

---

## 🌐 Deployment (Render)

The app is deployed at: **https://documind-ai-document-understanding.onrender.com**

Render is configured to:
1. Build via the `Dockerfile`
2. Expose port `8080`
3. Run `python web_app.py` as the start command

For your own Render deployment:
1. Connect your GitHub repo
2. Choose **Docker** as the environment
3. Set the port to `8080`
4. No environment variables required for basic operation

---

## 🔌 API Reference

### `POST /api/analyze`

Upload a document for OCR + NLP analysis.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | PDF, PNG, JPG, or JPEG (max 10 MB) |
| `mode` | string | OCR preprocessing mode: `standard` \| `aggressive` \| `photo` |
| `psm` | integer | Tesseract Page Segmentation Mode (0–13, default: 6) |

**Response:** `application/json`

```json
{
  "success": true,
  "filename": "invoice.png",
  "raw_text": "MR TRISHANT SRIVASTAVA...",
  "cleaned_text": "Mr Trishant Srivastava...",
  "entities": [
    { "value": "Trishant Srivastava", "type": "PERSON",  "confidence": "high" },
    { "value": "16/02/2022",          "type": "DATE",    "confidence": "high" },
    { "value": "₹12,400",             "type": "MONEY",   "confidence": "medium" }
  ],
  "entity_count": 14,
  "doc_type": "invoice",
  "ocr_confidence": 87.4,
  "avg_confidence": 82,
  "total_time_ms": 423.1,
  "timings": {
    "preprocess_ms": 38.2,
    "ocr_ms": 312.4,
    "clean_ms": 18.1,
    "nlp_pre_ms": 10.5,
    "extraction_ms": 43.9
  },
  "metrics": {
    "precision_proxy": 88,
    "recall_proxy": 76,
    "f1_proxy": 81
  },
  "model_used": "en_core_web_sm",
  "config_used": "--oem 3 --psm 6"
}
```

### `GET /api/samples`

Returns a list of available sample documents.

```json
[
  { "name": "sample_invoice", "filename": "sample_invoice.png" },
  { "name": "sample_letter",  "filename": "sample_letter.png"  }
]
```

### `GET /api/samples/<filename>`

Serves a sample document file by filename.

---

## 🎨 Design System

The UI uses a warm terracotta/charcoal design system defined as CSS custom properties in `main.css`:

| Token | Value | Usage |
|---|---|---|
| `--primary` | `#ab2f00` | Accent, borders, highlights |
| `--primary-dark` | `#271813` | Sidebar, dark buttons |
| `--surface` | `#fff8f6` | Main background |
| `--surface-white` | `#ffffff` | Cards, panels |
| `--on-surface` | `#271813` | Primary text |
| `--on-surface-var` | `#5b4039` | Secondary text |
| `--outline-var` | `#e4beb4` | Borders |
| `--font-serif` | Instrument Serif | Display headings |
| `--font-sans` | Geist Sans | Body, UI text |
| `--font-mono` | Geist Mono | Code, OCR output |

---

## 🧠 How It Works

```
Upload (PDF / PNG / JPG)
        │
        ▼
Image Quality Assessment     ← utils/router.py
(blur, brightness, contrast)
        │
        ▼
Auto-Crop + Perspective Fix  ← utils/image_preprocess.py
        │
        ▼
Tesseract OCR                ← utils/ocr.py
(configurable PSM + mode)
        │
        ├── raw_text
        │
        ▼
NLP Preprocessing            ← utils/preprocess.py
(tokenization, sentence split, cleaning)
        │
        ├── cleaned_text
        │
        ▼
spaCy Named Entity Recognition  ← utils/extract.py
(PERSON, ORG, DATE, MONEY, GPE, ...)
        │
        ├── entities[] with confidence scores
        │
        ▼
Flask JSON Response          ← web_app.py
        │
        ▼
Frontend Rendering           ← static/js/app.js
(Dual View, Entities Tab, JSON, Analytics, Preview)
```

---

## 📱 Browser Support

| Browser | Status |
|---|---|
| Chrome 100+ | ✅ Full support |
| Firefox 100+ | ✅ Full support |
| Safari 16+ | ✅ Full support |
| Edge 100+ | ✅ Full support |
| Mobile Chrome / Safari | ✅ Responsive layout with bottom nav |

---

## 🛡️ Constraints & Limits

- **File size:** Maximum 10 MB per upload
- **File types:** `.pdf`, `.png`, `.jpg`, `.jpeg`
- **OCR language:** English only (Tesseract `eng` tessdata)
- **NLP model:** `en_core_web_sm` — lightweight, fast, English only
- **PDF:** First page only for scanned PDFs; full text extraction for native PDFs
- **History:** Stored in browser `localStorage` — clears on browser data reset (max 20 entries)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Trishant Srivastava**
Built with Flask, Tesseract, spaCy, and Vanilla JS.
