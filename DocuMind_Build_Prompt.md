# 🧠 DocuMind — Build Prompt
### AI-Powered Document Understanding & Key-Information Extraction System
**Project Codename:** `DocuMind`
**Based on:** MCA Major Project — *AI-Powered Document Understanding and Key-Information Extraction System* by Trishant Srivastava

---

## 📌 Context: What Already Exists

The current prototype (`doc_understanding_demo`) has the following working pieces:

| Module | Status |
|---|---|
| Streamlit UI (file upload + basic display) | ✅ Done |
| `utils/ocr.py` — pytesseract text extraction | ✅ Done |
| `utils/preprocess.py` — lowercase + whitespace clean | ✅ Done |
| `utils/extract.py` — spaCy NER + regex for email & invoice no. | ✅ Done |
| Display raw text + JSON + pandas DataFrame table | ✅ Done |

Everything below is **what you need to build** — the full gap between the current prototype and the complete system described in the project report.

---

## 🏗️ PART 1 — Image Preprocessing Pipeline (Missing Entirely)

The report specifies a full image preprocessing step **before** OCR. Currently the image is fed raw into pytesseract. You must implement `utils/image_preprocess.py` with the following pipeline using **OpenCV**:

1. **Grayscale conversion** — convert the uploaded image to grayscale using `cv2.cvtColor`.
2. **Noise reduction** — apply Gaussian blur (`cv2.GaussianBlur`) to remove artifacts.
3. **Binarization / Thresholding** — use Otsu's thresholding (`cv2.threshold` with `THRESH_OTSU`) to make text crisp and background clean.
4. **Contrast enhancement** — use CLAHE (`cv2.createCLAHE`) to improve readability of faint text.
5. **Skew correction** — detect and correct document tilt using Hough line transform or minAreaRect on contours so OCR is not fed a tilted image.
6. **Return the processed image** as a PIL Image object for compatibility with pytesseract.

Update `utils/ocr.py` to call `image_preprocess()` before passing the image to pytesseract. Add a toggle in `app.py` (a Streamlit checkbox) that lets the user enable/disable preprocessing to compare results.

---

## 🔤 PART 2 — Enhanced Text Preprocessing (Upgrade `preprocess.py`)

The current implementation only does lowercasing and whitespace reduction. Expand it using **NLTK**:

1. **Tokenization** — tokenize the cleaned text into sentences and words using `nltk.sent_tokenize` and `nltk.word_tokenize`.
2. **Stopword handling** — do NOT remove stopwords (they are needed for NER context), but flag and store them separately for any future analysis.
3. **Punctuation normalization** — standardize inconsistent punctuation like multiple dots, dashes, or special characters that OCR often produces.
4. **Number normalization** — detect patterns like `2O23` (letter O instead of zero) and auto-correct common OCR substitution errors (O→0, l→1, etc.) using a small rule map.
5. **Line reconstruction** — rejoin broken words that OCR splits across lines (e.g., `in-\nvoice` → `invoice`) using hyphen-newline detection.

The function should return both the cleaned string (for NLP) and the tokenized representation (for display/debug).

---

## 🧩 PART 3 — Expanded Entity Extraction (Upgrade `extract.py`)

The current extraction handles: `PERSON`, `ORG`, `DATE`, `GPE`, `MONEY` via spaCy, plus `invoice_number` and `email` via regex. You must add the following:

### 3a. More spaCy Entity Types
Add extraction for:
- `CARDINAL` — raw numbers
- `PERCENT` — percentage values
- `TIME` — time expressions
- `FAC` — facilities / addresses (partial)
- `PRODUCT` — product names

### 3b. Expanded Regex Patterns
Add these regex extractors to the `extract.py` module:

```python
# Phone numbers (Indian + international)
r'(\+?[\d\s\-]{10,15})'

# Invoice/reference numbers (broader pattern)
r'(?:invoice\s*(?:no|number|#)?[\s:\-]*)([\w\-\/]+)'

# PAN / GST numbers (Indian documents)
r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'          # PAN
r'\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9Z][Z][0-9A-Z]\b'  # GSTIN

# Dates (multiple formats)
r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b'
r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b'

# Currency amounts (₹, $, USD, INR)
r'(?:₹|Rs\.?|INR|USD|\$)\s?[\d,]+(?:\.\d{2})?'

# URLs
r'https?://[^\s]+'
```

### 3c. Confidence Scoring
For each extracted entity, attach a `confidence` field:
- Regex matches → `"high"` (exact pattern match)
- spaCy entities with `ent.kb_id_` → `"medium"`
- spaCy entities without KB ID → `"low"`

Return a list of dicts: `{"type": ..., "value": ..., "source": "spacy"|"regex", "confidence": ...}`

---

## 📄 PART 4 — PDF Support (New Input Type)

The report specifies the system should accept **PDF files**, not just images. Add PDF handling:

1. In `app.py`, update the file uploader to accept `["png", "jpg", "jpeg", "pdf"]`.
2. Create `utils/pdf_handler.py`:
   - Use **PyMuPDF (`fitz`)** to open PDFs.
   - Convert each page to a PIL Image at 200 DPI using `page.get_pixmap(dpi=200)`.
   - If the PDF has selectable text (not scanned), extract it directly with `page.get_text()` and skip OCR — show a notice in the UI.
   - If it's a scanned PDF, run each page image through the preprocessing + OCR pipeline.
   - For multi-page PDFs, process each page and concatenate the text with a page separator.
3. Show a page selector slider in the UI when a multi-page PDF is uploaded.

---

## 📊 PART 5 — Results & Analytics UI (Major UI Overhaul)

The current UI is minimal. The report describes a complete output representation with multiple views. Rebuild the results section of `app.py` with Streamlit tabs:

### Tab 1: 📄 Extracted Text
- Show the **raw OCR text** in a scrollable `st.text_area`.
- Show the **cleaned/preprocessed text** below it.
- Add a side-by-side diff toggle (use `st.columns`) to compare raw vs cleaned.

### Tab 2: 🧩 Entities (Interactive Table)
- Show extracted entities as a styled `st.dataframe` with columns: `Type`, `Value`, `Source`, `Confidence`.
- Add a multiselect filter at the top so the user can filter by entity type (e.g., show only `DATE` and `MONEY`).
- Color-code the confidence column: green for high, yellow for medium, red for low (use `st.dataframe` with `Styler`).

### Tab 3: 🗂️ JSON View
- Show the full extracted JSON using `st.json()`.
- Add a **"Copy JSON"** button using `st.code` with the JSON string and a copy icon.
- Add a **"Download JSON"** button using `st.download_button`.

### Tab 4: 📈 Analytics
- Show a **bar chart** of entity type distribution using `st.bar_chart` or Plotly.
- Show **OCR confidence score** (calculated as: percentage of recognized words vs total tokens).
- Show **extraction summary**: total entities found, breakdown by type, processing time in ms.
- Display a **processing timeline** as a simple horizontal bar showing time spent in each stage (preprocessing → OCR → NLP → extraction).

### Tab 5: 🖼️ Document Preview
- Show the uploaded image (or each PDF page as an image) in the UI.
- Overlay bounding boxes on the image for each extracted entity using PIL `ImageDraw` — different colors per entity type.
- Show a legend mapping colors to entity types.

---

## ⚙️ PART 6 — Error Handling & Confidence System

The report specifically calls out error propagation as a weakness. Add robust error handling throughout:

1. **OCR errors:** If pytesseract returns fewer than 20 characters, show a warning: *"OCR extraction appears incomplete — try enabling image preprocessing or check image quality."*
2. **NLP errors:** Wrap spaCy processing in try/except; if it fails, fall back to regex-only extraction and show a notice.
3. **Empty extraction:** If no entities are found, show a friendly message with suggestions (check image quality, try a clearer scan).
4. **File validation:** Reject files over 10MB with a clear error. Reject non-image/PDF files.
5. **Processing time limit:** If any stage takes over 30 seconds, show a spinner with stage label and a timeout warning.
6. **Confidence summary panel:** After extraction, show a small summary box with overall extraction confidence (average of all entity confidence scores as a percentage).

---

## 🗃️ PART 7 — Sample Documents Gallery

The `sample_docs/` directory exists but is unused. Build a working sample gallery:

1. Add at least 3 sample document images to `sample_docs/`:
   - A mock invoice (generate using PIL — include invoice number, date, vendor name, total amount, email).
   - A mock business letter (include person name, org name, date, address).
   - A mock form/receipt.
2. In `app.py`, add a **"Try a Sample Document"** section above the file uploader with thumbnail previews using `st.image`.
3. When a sample is selected, load it automatically and run the full pipeline without requiring an upload.

Create a script `generate_samples.py` at the project root that generates these sample images programmatically using `PIL.ImageDraw` and `PIL.ImageFont`.

---

## 📁 Final Project Structure

After all the above is implemented, the project structure should look like this:

```
DocuMind/
│
├── app.py                    # Main Streamlit app (heavily updated)
├── generate_samples.py       # Script to create sample documents
├── requirements.txt          # All dependencies
│
├── utils/
│   ├── ocr.py                # OCR extraction (updated to use image_preprocess)
│   ├── preprocess.py         # Text cleaning + NLTK tokenization (upgraded)
│   ├── extract.py            # Entity extraction (expanded NER + regex)
│   ├── image_preprocess.py   # NEW: OpenCV image enhancement pipeline
│   └── pdf_handler.py        # NEW: PDF page extraction + routing logic
│
└── sample_docs/
    ├── sample_invoice.png
    ├── sample_letter.png
    └── sample_receipt.png
```

---

## 📦 Requirements (`requirements.txt`)

```
streamlit
pytesseract
Pillow
spacy
pandas
opencv-python-headless
nltk
PyMuPDF
plotly
```

Also run after install:
```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
```

---

## 🎨 UI Design Guidelines

- Use a **dark sidebar** with the DocuMind logo (text-based using `st.markdown`).
- Sidebar should contain: app title, description, settings (preprocessing toggle, confidence threshold slider from 0.0–1.0, entity type multiselect for filtering).
- Main area uses full width (`st.set_page_config(layout="wide")`).
- Use `st.spinner` with stage-specific messages during processing: *"Enhancing image..."*, *"Extracting text..."*, *"Running NLP..."*, *"Building output..."*.
- Color scheme: deep navy + amber accent (CSS injection via `st.markdown` with `unsafe_allow_html=True`).
- All tables should have alternating row colors and be sortable.

---

## ✅ Acceptance Criteria (How to Know It's Done)

- [ ] Upload a PNG invoice → see preprocessed image preview, extracted entities in table, downloadable JSON.
- [ ] Upload a scanned PDF → each page is processed, entities shown per page.
- [ ] Upload a low-quality image → system shows confidence warning, doesn't crash.
- [ ] Click a sample document → pipeline runs automatically.
- [ ] Filter entities by type → table updates in real time.
- [ ] Download button exports valid JSON file.
- [ ] Analytics tab shows bar chart of entity types + processing time.
- [ ] Bounding box overlay is visible on Document Preview tab.
