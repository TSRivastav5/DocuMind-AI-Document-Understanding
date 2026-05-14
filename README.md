# 🧠 DocuMind — AI-Powered Document Understanding

> **Automatically extract key information from invoices, receipts, letters, and scanned documents using OCR + NLP.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit)
![Tesseract](https://img.shields.io/badge/Tesseract_OCR-5.x-green)
![spaCy](https://img.shields.io/badge/spaCy-3.7%2B-09A3D5)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 What is DocuMind?

DocuMind is a privacy-first document intelligence platform built with **Streamlit**. Upload any scanned image or PDF and it will:

- **Extract all readable text** via Tesseract OCR with intelligent preprocessing
- **Classify the document** type (Invoice, Receipt, Business Letter, General)
- **Pull out named entities** — dates, amounts, vendor names, invoice numbers, GSTIN, PAN, emails, and more
- **Assess image quality** and automatically route to the best OCR pipeline
- **Display analytics** — entity distribution charts, processing timeline, and confidence metrics
- **Export results** as a downloadable JSON file

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Smart OCR Routing** | Automatically picks Standard, Aggressive, or Photo pipeline based on image quality score |
| 📄 **PDF Support** | Multi-page PDF handling — skips OCR for selectable-text PDFs |
| 🧹 **NLP Preprocessing** | NLTK sentence/token splitting + spaCy NER for entity extraction |
| 🎯 **Regex Fallback** | Extracts Invoice #, GST, PAN, Phone, Email even without spaCy |
| 📸 **Auto-Crop** | Detects and isolates document boundaries from noisy backgrounds |
| 📊 **Quality Assessment** | Blur detection (Laplacian variance), contrast score, resolution check |
| 🗂️ **JSON Export** | Download all extracted entities and timings as structured JSON |
| 🖼️ **Visual Overlays** | OCR bounding boxes and confidence heatmap on the original image |

---

## 🖥️ Demo Screenshots

### Upload & OCR Routing
The app scores your image and routes it to the correct processing pipeline before any OCR runs.

### Entity Extraction Table
Entities are color-coded by confidence level (High 🟢 / Medium 🟡 / Low 🔴) with type, value, and source displayed.

### Analytics Dashboard
Bar charts of entity distribution + a processing timeline showing time spent in each stage (Preprocess → OCR → Cleaning → NLP → Extraction).

---

## ⚙️ Prerequisites

Install the following **system dependencies** before running the app:

### 1. Tesseract OCR

**macOS**
```bash
brew install tesseract
```

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install -y tesseract-ocr
```

**Windows**
Download the installer from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your `PATH`.

### 2. Python 3.10+

Check your version:
```bash
python3 --version
```

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/TSRivastav5/DocuMind-AI-Document-Understanding.git
cd DocuMind-AI-Document-Understanding

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download the spaCy language model
python -m spacy download en_core_web_sm

# 5. Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 📂 Project Structure

```
DocuMind-AI-Document-Understanding/
│
├── app.py                        # Streamlit application
├── requirements.txt              # Python dependencies
├── generate_samples.py           # Script to regenerate sample documents
│
├── utils/
│   ├── ocr.py                   # Tesseract OCR wrapper + PSM options
│   ├── preprocess.py            # Text cleaning & NLTK tokenization
│   ├── extract.py               # spaCy NER + regex entity extraction
│   ├── image_preprocess.py      # Image quality assessment + enhancement
│   ├── router.py                # OCR routing engine (Standard / Aggressive / Reject)
│   ├── pdf_handler.py           # PyMuPDF PDF parsing
│   └── ui_helpers.py            # UI utilities
│
└── sample_docs/
    ├── sample_invoice.png
    ├── sample_letter.png
    └── sample_receipt.png
```

---

## 🎮 How to Use

### Step 1 — Upload or Try a Sample
- Click **"Try a Sample Document"** to test with built-in invoice, letter, or receipt images
- Or drag-and-drop your own **PNG, JPG, JPEG, or PDF** (max 10 MB)

### Step 2 — Configure Settings (Sidebar)
| Setting | What it does |
|---|---|
| **Image Preprocessing** | Toggle preprocessing on/off |
| **Preprocessing Mode** | `standard` (scanned PDFs) · `aggressive` (noisy/faded) · `photo` (camera/WhatsApp) |
| **PSM Mode** | Tesseract Page Segmentation Mode — controls how the page layout is read |
| **Min Confidence Threshold** | Filter out low-confidence entities |
| **Entity Types to Show** | Pick which entity types to display |

### Step 3 — View Results

Results are split across 5 tabs:

| Tab | Contents |
|---|---|
| 📄 **Extracted Text** | Raw OCR output vs. cleaned text, side by side; tokenization details; POS tags |
| 🧩 **Entities** | Filterable table of all extracted entities with type, value & confidence |
| 🗂️ **JSON View** | Structured JSON output + one-click download |
| 📈 **Analytics** | Entity distribution chart, Precision/Recall/F1 metrics, processing timeline |
| 🖼️ **Document Preview** | Original image with optional OCR bounding boxes or confidence heatmap overlay |

---

## 🧠 OCR Routing Logic

DocuMind scores every image before running OCR:

```
Image Quality Score (0–100)
        │
        ├─ ≥ 60  → ✅ Tesseract Standard
        ├─ 35–59 → ⚠️  Tesseract Aggressive (extra denoising + contrast boost)
        └─ < 35  → ❌ Reject (image too distorted — user shown actionable tips)
```

Quality is determined by:
- **Blur score** — Laplacian variance (≥100 = sharp)
- **Contrast score** — standard deviation of pixel intensities
- **Resolution** — minimum 100 × 100 px required

---

## 🏷️ Supported Entity Types

| Category | Entities |
|---|---|
| **Financial** | Money, Total Amount, Subtotal, Tax/GST, Currency |
| **Document IDs** | Invoice Number, PAN, GSTIN |
| **Dates & Time** | Invoice Date, Due Date, Time |
| **People & Orgs** | Person, Organization, Vendor Name, Customer Name |
| **Contact** | Email, Phone, Website, URL |
| **Location** | GPE (country/city), Facility |
| **General** | Cardinal numbers, Percentages, Products |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `pytesseract` | Python wrapper for Tesseract OCR |
| `Pillow` | Image loading and manipulation |
| `opencv-python-headless` | Image preprocessing (blur, contrast, deskew) |
| `spacy` | Named Entity Recognition (NER) |
| `nltk` | Sentence tokenization and POS tagging |
| `PyMuPDF` | PDF parsing and rendering |
| `pandas` | Entity table display |
| `plotly` | Interactive analytics charts |
| `numpy` | Numerical operations |

---

## 🛠️ Troubleshooting

**`TesseractNotFoundError`**
> Tesseract is not installed or not in your PATH.
```bash
# macOS
brew install tesseract
# Ubuntu
sudo apt install tesseract-ocr
```

**`OSError: [E050] Can't find model 'en_core_web_sm'`**
```bash
python -m spacy download en_core_web_sm
```

**`ModuleNotFoundError: No module named 'fitz'`**
```bash
pip install PyMuPDF
```

**OCR returns empty or garbled text**
- Try switching **Preprocessing Mode** to `aggressive` or `photo` in the sidebar
- Check the **Image Quality Report** — if the score is below 35, the image may need scanning again at higher resolution

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built as an MCA Major Project · Trishant Srivastava</sub>
</div>
