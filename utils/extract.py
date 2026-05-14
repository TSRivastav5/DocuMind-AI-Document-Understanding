"""
utils/extract.py
Entity extraction: spaCy NER (en_core_web_md) + context-aware invoice
regex patterns + deduplication + POS tagging + precision/recall/F1 proxy.
"""
import re
import time
from typing import List, Dict, Any

import spacy

# ── Load spaCy model (prefer md > sm > None) ───────────────────────────────────
try:
    nlp = spacy.load("en_core_web_md")
    _MODEL_USED = "en_core_web_md"
except OSError:
    try:
        nlp = spacy.load("en_core_web_sm")
        _MODEL_USED = "en_core_web_sm"
    except OSError:
        nlp = None
        _MODEL_USED = "unavailable"

# ── spaCy entity types to keep ─────────────────────────────────────────────────
SPACY_TYPES = {"PERSON", "ORG", "DATE", "GPE", "MONEY",
               "CARDINAL", "PERCENT", "TIME", "FAC", "PRODUCT"}

# ── POS tag → display colour ───────────────────────────────────────────────────
POS_COLORS = {
    "NOUN":  "#3b82f6",   # blue
    "PROPN": "#8b5cf6",   # purple
    "VERB":  "#10b981",   # green
    "NUM":   "#f97316",   # orange
    "ADJ":   "#f59e0b",   # amber
    "ADV":   "#06b6d4",   # cyan
}

# ── Document-type keyword sets ─────────────────────────────────────────────────
DOCUMENT_TYPE_KEYWORDS = {
    "invoice":  ["invoice", "bill", "receipt", "payment", "total", "gst", "tax", "amount due"],
    "letter":   ["dear", "sincerely", "regards", "to whom", "subject", "yours faithfully"],
    "form":     ["form no", "application", "fill in", "signature", "date of birth", "name:"],
    "report":   ["executive summary", "introduction", "conclusion", "findings", "methodology"],
}

# ── Invoice / form key-value regex patterns ────────────────────────────────────
INVOICE_FIELD_PATTERNS = {
    "Invoice Number":  r'(?:invoice\s*(?:no|number|#|num)?[\s:\-#]*)([\w\-\/]{3,})',
    "Invoice Date":    r'(?:invoice\s*date|date\s*of\s*invoice)[\s:\-]*([\d]{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})',
    "Due Date":        r'(?:due\s*date|payment\s*due)[\s:\-]*([\d]{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})',
    "Total Amount":    r'(?:total|grand\s*total|amount\s*due|net\s*amount)[\s:\-]*(?:₹|rs\.?|inr|usd|\$)?\s*([\d,]+(?:\.\d{2})?)',
    "Subtotal":        r'(?:subtotal|sub\s*total)[\s:\-]*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)',
    "Tax / GST":       r'(?:gst|tax|cgst|sgst|igst)[\s:\-@%\d]*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d{2})?)',
    "Vendor Name":     r'(?:from|vendor|seller|billed\s*by|company)[\s:\-]+([\w\s&.,]+)',
    "Customer Name":   r'(?:bill\s*to|buyer|client)[\s:\-]+([\w\s.,]+)',
    "Email":           r'[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}',
    "Phone":           r'(?:\+91[\-\s]?)?[6-9]\d{9}|(?:\+\d{1,3}[\s\-])?\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}',
    "GSTIN":           r'\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b',
    "PAN":             r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
    "Website":         r'(?:https?://|www\.)[^\s,]+',
}

# Legacy patterns (always run regardless of doc type)
REGEX_PATTERNS: List[Dict[str, Any]] = [
    {"type": "EMAIL",
     "pattern": re.compile(r'\b[\w.%+\-]+@[\w.\-]+\.[A-Za-z]{2,}\b'), "group": 0},
    {"type": "INVOICE_NUMBER",
     "pattern": re.compile(r'(?i)(?:invoice\s*(?:no|number|#)?[\s:\-]*)([A-Z0-9][\w\-\/]{2,})'), "group": 1},
    {"type": "PHONE",
     "pattern": re.compile(r'(?<!\d)(\+?[\d][\d\s\-]{8,14}\d)(?!\d)'), "group": 0},
    {"type": "PAN",
     "pattern": re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'), "group": 0},
    {"type": "GSTIN",
     "pattern": re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9Z][Z][0-9A-Z]\b'), "group": 0},
    {"type": "DATE",
     "pattern": re.compile(r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b'), "group": 1},
    {"type": "DATE",
     "pattern": re.compile(
         r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b',
         re.IGNORECASE), "group": 1},
    {"type": "CURRENCY",
     "pattern": re.compile(r'(?:₹|Rs\.?|INR|USD|\$)\s?[\d,]+(?:\.\d{2})?'), "group": 0},
    {"type": "URL",
     "pattern": re.compile(r'https?://[^\s]+'), "group": 0},
]


# ── Document type detection ────────────────────────────────────────────────────

def detect_document_type(text: str) -> str:
    """Return the most likely document type based on keyword scoring."""
    text_lower = text.lower()
    scores = {
        doc_type: sum(1 for kw in kws if kw in text_lower)
        for doc_type, kws in DOCUMENT_TYPE_KEYWORDS.items()
    }
    best_type = max(scores, key=scores.get)
    return best_type if scores[best_type] > 0 else "general"


# ── Invoice key-value extraction ───────────────────────────────────────────────

def extract_structured_fields(text: str) -> List[Dict[str, Any]]:
    """Context-aware invoice field extraction using label:value patterns."""
    results = []
    case_sensitive_fields = {"Email", "GSTIN", "PAN", "Website"}

    for field_name, pattern in INVOICE_FIELD_PATTERNS.items():
        search_text = text if field_name in case_sensitive_fields else text.lower()
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            value = match.strip() if isinstance(match, str) else match[0].strip()
            if value and len(value) > 1:
                results.append({
                    "type": field_name,
                    "value": value,
                    "source": "regex",
                    "confidence": "high",
                })
    return results


# ── Deduplication ──────────────────────────────────────────────────────────────

def deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by (type, normalised value); prefer high-confidence source."""
    seen: Dict[str, Dict] = {}
    for ent in entities:
        key = f"{ent['type']}::{ent['value'].lower().strip()}"
        if key not in seen:
            seen[key] = ent
        elif ent["confidence"] == "high" and seen[key]["confidence"] != "high":
            seen[key] = ent
    return list(seen.values())


# ── POS Tagging ────────────────────────────────────────────────────────────────

def get_pos_tags(text: str) -> List[Dict[str, str]]:
    """Return per-token POS tags for the cleaned text."""
    if nlp is None:
        return []
    try:
        doc = nlp(text[:5000])   # cap to avoid timeout
        return [
            {"word": tok.text, "pos": tok.pos_, "tag": tok.tag_,
             "color": POS_COLORS.get(tok.pos_, "#94a3b8")}
            for tok in doc
            if not tok.is_space and not tok.is_punct
        ]
    except Exception:
        return []


# ── Precision / Recall / F1 proxy ─────────────────────────────────────────────

def compute_extraction_metrics(entities: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute proxy P / R / F1 since ground truth is unavailable at runtime.

    Precision proxy: weighted ratio of high/medium confidence entities.
    Recall proxy:    fraction of core invoice fields found.
    """
    total = len(entities)
    if total == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    high_conf = sum(1 for e in entities if e["confidence"] == "high")
    med_conf  = sum(1 for e in entities if e["confidence"] == "medium")
    precision = (high_conf + 0.5 * med_conf) / total

    EXPECTED = {"Invoice Number", "Invoice Date", "Total Amount", "Email", "Phone"}
    found_types = {e["type"] for e in entities}
    recall = len(EXPECTED & found_types) / len(EXPECTED)

    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    return {
        "precision": round(precision * 100, 1),
        "recall":    round(recall    * 100, 1),
        "f1":        round(f1        * 100, 1),
    }


# ── Extraction accuracy table ──────────────────────────────────────────────────

def build_accuracy_table(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build per-entity-type confidence breakdown (Table 2 of the report)."""
    from collections import defaultdict
    rows: Dict[str, Dict] = defaultdict(lambda: {"Count": 0, "High": 0, "Medium": 0, "Low": 0})
    for e in entities:
        t = e["type"]
        rows[t]["Count"] += 1
        conf = e.get("confidence", "low")
        if conf == "high":
            rows[t]["High"] += 1
        elif conf == "medium":
            rows[t]["Medium"] += 1
        else:
            rows[t]["Low"] += 1
    return [{"Entity Type": k, **v} for k, v in rows.items()]


# ── Main extraction function ───────────────────────────────────────────────────

def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extract named entities from text using spaCy NER + invoice regex rules.

    Returns:
        dict with keys:
          entities        — list of {type, value, source, confidence}
          doc_type        — detected document type
          spacy_failed    — bool
          model_used      — spaCy model name
          duration_ms     — processing time in ms
    """
    t0 = time.time()
    results: List[Dict[str, Any]] = []
    spacy_failed = False

    # ── spaCy NER ──────────────────────────────────────────────────────────────
    if nlp is not None:
        try:
            doc = nlp(text[:10000])
            for ent in doc.ents:
                if ent.label_ in SPACY_TYPES:
                    # Use 'high' for multi-token or longer named entities,
                    # 'medium' for single short tokens — never 'low' so they
                    # always pass the default confidence threshold filter.
                    conf = "high" if len(ent.text.split()) > 1 or len(ent.text) > 5 else "medium"
                    results.append({
                        "type": ent.label_, "value": ent.text,
                        "source": "spacy", "confidence": conf,
                    })
        except Exception:
            spacy_failed = True
    else:
        spacy_failed = True

    # ── Legacy regex patterns ──────────────────────────────────────────────────
    for rule in REGEX_PATTERNS:
        for match in rule["pattern"].finditer(text):
            try:
                value = match.group(rule["group"])
            except IndexError:
                value = match.group(0)
            if value.strip():
                results.append({
                    "type": rule["type"], "value": value.strip(),
                    "source": "regex", "confidence": "high",
                })

    # ── Structured invoice fields ──────────────────────────────────────────────
    results.extend(extract_structured_fields(text))

    # ── Deduplicate ────────────────────────────────────────────────────────────
    results = deduplicate_entities(results)

    # ── Sort: high → medium → low ──────────────────────────────────────────────
    _conf_rank = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda e: _conf_rank.get(e.get("confidence", "low"), 2))

    doc_type = detect_document_type(text)

    return {
        "entities":     results,
        "doc_type":     doc_type,
        "spacy_failed": spacy_failed,
        "model_used":   _MODEL_USED,
        "duration_ms":  round((time.time() - t0) * 1000, 1),
    }