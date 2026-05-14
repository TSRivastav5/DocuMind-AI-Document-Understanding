# Project Overview: doc_understanding_demo

## 1. Project Description
The **doc_understanding_demo** is an AI-powered document understanding system built with Streamlit. It allows users to upload an image of a document (PNG, JPG, JPEG), extracts text from it using OCR (Optical Character Recognition), processes the text, and extracts structured entities (like Person, Organization, Dates, etc.) and specific data points (like emails and invoice numbers) using Natural Language Processing (NLP) and rule-based regular expressions. The final output is presented in both a JSON format and a structured tabular view.

## 2. Project Status
**Status: Functional Prototype**
The application is currently functional and implements the core pipeline required for document understanding:
- **Image Upload:** Handled successfully via Streamlit's file uploader.
- **OCR Engine:** Integrated using `pytesseract` to extract raw text from image files.
- **Preprocessing Pipeline:** Implemented basic text cleaning (lowercasing, whitespace reduction).
- **Entity Extraction Engine:** Integrated with `spaCy` (`en_core_web_sm`) for Named Entity Recognition (NER) and Regex for structured pattern matching.
- **UI & Presentation:** Complete user interface displaying extracted text, JSON object representations, and Pandas DataFrame tables.

## 3. Technology Stack
- **Frontend/UI Framework:** Streamlit (`app.py`)
- **OCR Module:** `pytesseract` with PIL (Python Imaging Library)
- **Data Manipulation:** `pandas`
- **NLP & Information Extraction:** `spaCy` (using the `en_core_web_sm` model)
- **Pattern Matching:** Python `re` (Regular Expressions)

## 4. Codebase Architecture
The project structure is clean and modularized:

- **`app.py`**: The main entry point for the Streamlit web application. It orchestrates the flow from file upload to displaying extracted results.
- **`utils/`**: Contains modularized logic for the pipeline.
  - **`ocr.py`**: Responsible for taking an image and returning raw string text using Tesseract.
  - **`preprocess.py`**: Cleans the raw text to make it suitable for NLP extraction (e.g., removing redundant new lines and spaces).
  - **`extract.py`**: Handles all the entity extraction logic. It leverages `spaCy` to find named entities (`PERSON`, `ORG`, `DATE`, `GPE`, `MONEY`) and uses regex to find `invoice_number` and `emails`.
- **`sample_docs/`**: A directory intended to store test images or sample documents.
- **`.venv/`**: The local Python virtual environment containing the project dependencies.

## 5. How It Works (Execution Flow)
1. **Upload:** A user visits the Streamlit app and uploads a document image (e.g., an invoice or a letter).
2. **Read Image:** The image is loaded into memory using `PIL.Image`.
3. **Text Extraction:** `app.py` calls `utils.ocr.extract_text()`, which passes the image to `pytesseract` to get the `raw_text`.
4. **Text Cleaning:** The `raw_text` is passed to `utils.preprocess.clean_text()`, which normalizes it (lowercase, removes newlines, trims spaces).
5. **Information Extraction:** The `cleaned_text` is fed to `utils.extract.extract_entities()`. 
   - `spaCy` parses the text to identify named entities.
   - Regex patterns scan for specific keywords and formats (emails and "invoice no").
6. **Data Presentation:** 
   - The UI displays the raw extracted text.
   - The UI renders the extracted entities and variables as a JSON object.
   - Finally, a formatted `pandas` DataFrame displays a clean tabular view of the `Type` and `Value` of the parsed entities.
