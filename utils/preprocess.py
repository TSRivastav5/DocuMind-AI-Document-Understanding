"""
utils/preprocess.py
Enhanced text preprocessing pipeline.

Steps:
  1. Post-OCR noise filtering  (clean_ocr_output)
  2. Meaningful-line filtering (filter_meaningful_text)
  3. Classic NLP prep          (tokenization, sentence splitting)

Uses NLTK when available; falls back to regex-based tokenization.
"""
import re
import time

try:
    import nltk
    for _pkg in ["punkt", "stopwords", "punkt_tab"]:
        try:
            nltk.data.find(f"tokenizers/{_pkg}")
        except LookupError:
            try:
                nltk.download(_pkg, quiet=True, raise_on_error=False)
            except Exception:
                pass
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords as _sw
    try:
        _STOP_WORDS = set(_sw.words("english"))
    except Exception:
        _STOP_WORDS = set()
    _HAS_NLTK = True
except Exception:
    _HAS_NLTK = False
    _STOP_WORDS = set()


# ── Noise patterns (lines with no real content) ────────────────────────────────
_NOISE_PATTERNS = [
    re.compile(r'^[^a-zA-Z0-9]{0,3}$'),    # No alphanumeric at all
    re.compile(r'^[_\-=~\.]{2,}$'),         # Dashes / underscores (table borders)
    re.compile(r'^\W+$'),                    # Only special characters
    re.compile(r'^.{1,2}$'),                 # 1-2 char lines — almost always noise
]

# ── OCR substitution correction map ───────────────────────────────────────────
_OCR_CORRECTIONS = [
    (re.compile(r'(?<=[A-Z])0(?=[A-Z])'), 'O'),   # 0 ↔ O between uppercase letters
    (re.compile(r'(?<=[a-z])1(?=[a-z])'), 'l'),   # 1 ↔ l between lowercase letters
    (re.compile(r'\bI(?=\d)'),            '1'),   # I before digits → 1
    (re.compile(r'(?<!\d)O(?=\d)'),       '0'),   # O before digits → 0
    (re.compile(r'(?<=\d)O(?!\d)'),       '0'),   # O after digits → 0
    (re.compile(r'(?<!\w)l(?=\d)'),       '1'),   # l before digits → 1
]


# ── Stage 1: Post-OCR line-level noise filter ─────────────────────────────────

def clean_ocr_output(raw_text: str) -> str:
    """
    First-pass cleaning: remove noise lines and fix common OCR substitutions.
    Preserves meaningful line breaks.
    """
    lines = raw_text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip lines that match noise patterns
        if any(p.match(line) for p in _NOISE_PATTERNS):
            continue

        # Fix OCR substitutions
        for pat, repl in _OCR_CORRECTIONS:
            line = pat.sub(repl, line)

        # Normalise intra-line whitespace
        line = re.sub(r'\s{2,}', ' ', line)

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


# ── Stage 2: Keep only lines that contain real words ─────────────────────────

def filter_meaningful_text(text: str, min_word_len: int = 2,
                            min_line_words: int = 1) -> str:
    """
    Second-pass: discard lines whose words are all too short or non-alphanumeric.
    """
    lines = text.split('\n')
    meaningful = []
    for line in lines:
        words = [
            w for w in line.split()
            if len(w) >= min_word_len and re.search(r'[a-zA-Z0-9]', w)
        ]
        if len(words) >= min_line_words:
            meaningful.append(' '.join(words))
    return '\n'.join(meaningful)


# ── Stage 3: Full NLP preprocessing pipeline ─────────────────────────────────

def clean_text(raw_text: str) -> dict:
    """
    Full text preprocessing pipeline.

    Applies:
      • Post-OCR noise removal (clean_ocr_output)
      • Meaningful-line filtering (filter_meaningful_text)
      • Hyphenated line-break joining
      • Non-ASCII removal
      • NLTK / regex tokenization

    Returns dict with keys:
      cleaned, sentences, tokens, stopwords, duration_ms
    """
    t0 = time.time()

    # 1. OCR noise removal (line-aware)
    text = clean_ocr_output(raw_text)

    # 2. Meaningful-line filter
    text = filter_meaningful_text(text)

    # 3. Classic cleanup while preserving line structure
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Join hyphenated line breaks within a line
        line = re.sub(r'-\s*\n\s*', '', line)
        # Collapse repeated punctuation
        line = re.sub(r'\.{2,}', '.', line)
        line = re.sub(r'-{2,}', '-', line)
        # Strip non-ASCII
        line = re.sub(r'[^\x00-\x7F]+', ' ', line)
        # Normalise spaces
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            cleaned_lines.append(line)

    cleaned = '\n'.join(cleaned_lines)

    # 4. Tokenization — operate on the full text for sentence / word detection
    flat = ' '.join(cleaned_lines)
    if _HAS_NLTK:
        try:
            sentences = sent_tokenize(flat)
            tokens = word_tokenize(flat)
        except Exception:
            sentences = _simple_sentences(flat)
            tokens = flat.split()
    else:
        sentences = _simple_sentences(flat)
        tokens = flat.split()

    stop_tokens = [t for t in tokens if t.lower() in _STOP_WORDS]

    return {
        "cleaned": cleaned,
        "sentences": sentences,
        "tokens": tokens,
        "stopwords": stop_tokens,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    }


def _simple_sentences(text: str):
    """Minimal sentence splitter when NLTK is unavailable."""
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
