"""
DocuMind V2 — AI-Powered Document Understanding & Key-Information Extraction
Main Streamlit application.
"""
import io, json, time, os
import pandas as pd
import streamlit as st
from PIL import Image

try:
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

try:
    import fitz
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

from utils.ocr import extract_text, draw_confidence_heatmap, PSM_OPTIONS, DEFAULT_PSM_LABEL, PHOTO_PSM_LABEL
from utils.preprocess import clean_text
from utils.extract import (extract_entities, get_pos_tags,
                            compute_extraction_metrics, build_accuracy_table)
from utils.ui_helpers import (CONF_SCORE, ENTITY_COLORS, metric_card,
                               draw_bboxes, render_doc_type_badge,
                               render_pos_strip, render_metrics_cards,
                               render_performance_table, render_accuracy_table)
from utils.image_preprocess import assess_image_quality, auto_crop_document
from utils.router import route_ocr_engine, REJECTION_TIPS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind — AI Document Understanding",
    page_icon="🧠", layout="centered", initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Sans:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap');

/* Base / Background */
.stApp {
    background-color: #fff8f6;
    color: #271813;
}
html, body, [class*="css"] {
    font-family: 'Geist Sans', sans-serif;
    color: #271813;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111318 !important;
    border-right: 1px solid rgba(228, 190, 180, 0.2);
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
    color: #f8f7f4 !important;
}
[data-testid="stSidebar"] svg {
    fill: #f8f7f4 !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Geist Sans', sans-serif;
    color: #5b4039 !important;
    background-color: transparent !important;
    font-weight: 500;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #ab2f00 !important;
    border-bottom-color: #ab2f00 !important;
}

/* Headings */
h1, h2, h3 {
    font-family: 'Instrument Serif', serif;
    font-weight: 400;
    color: #271813;
}
h1 { font-size: 3rem !important; }

/* Metric Cards */
.metric-card {
    background: #ffffff;
    border: 1px solid rgba(228, 190, 180, 0.5);
    border-bottom: 2px solid #ab2f00;
    padding: 24px;
    border-radius: 4px;
    box-shadow: 1px 1px 0 0 #e2e1de, 0 12px 24px -8px rgba(39,24,19,.08);
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    margin-bottom: 16px;
    text-align: left;
}
.metric-card:hover {
    transform: scale(1.02) rotate(0.5deg);
}
.metric-card .label {
    font-size: 11px;
    font-weight: 600;
    color: #5b4039;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.metric-card .value {
    font-family: 'Instrument Serif', serif;
    font-size: 42px;
    font-weight: 400;
    color: #ab2f00;
    line-height: 1;
}

/* Badges / Confidence */
.conf-high { background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; }
.conf-medium { background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; }
.conf-low { background: #fee2e2; color: #ba1a1a; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; }

/* Timeline Bar */
.timeline-bar { display: flex; border-radius: 4px; overflow: hidden; height: 16px; margin: 8px 0; }
.tl-seg { display: flex; align-items: center; justify-content: center; font-size: 10px; color: white; font-weight: 600; }

/* Info Boxes */
.warn-box { background: rgba(217, 119, 6, 0.1); border: 1px solid rgba(217, 119, 6, 0.3); border-radius: 4px; padding: 12px; color: #d97706; font-size: 13px; margin: 8px 0; }
.info-box { background: rgba(144, 112, 103, 0.1); border: 1px solid rgba(144, 112, 103, 0.3); border-radius: 4px; padding: 12px; color: #5b4039; font-size: 13px; margin: 8px 0; }
.photo-notice { background: rgba(22, 163, 74, 0.1); border: 1px solid rgba(22, 163, 74, 0.3); border-radius: 4px; padding: 12px; color: #16a34a; font-size: 13px; margin: 8px 0; }

/* Buttons */
.stButton>button[kind="secondary"] {
    width: 100%;
    background: #271813;
    border: none;
    color: #ffffff;
    border-radius: 4px;
    font-weight: 500;
    transition: opacity 0.2s;
}
.stButton>button[kind="secondary"]:hover {
    opacity: 0.85;
    background: #271813;
    color: #ffffff;
}

/* Expander / Headers */
.streamlit-expanderHeader {
    font-family: 'Geist Sans', sans-serif;
    color: #271813 !important;
    background: #ffffff;
    border-radius: 4px;
}

/* Sidebar Nav */
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 8px;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 8px 12px;
    border-radius: 6px;
    background: transparent;
    cursor: pointer;
    transition: background 0.2s;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(250, 220, 212, 0.05);
}
[data-testid="stSidebar"] [role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
    font-size: 15px !important;
    font-weight: 500 !important;
    color: rgba(250, 220, 212, 0.7) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"],
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] [role="radiogroup"] label[aria-checked="true"] {
    background: rgba(250, 220, 212, 0.1);
}
[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [role="radiogroup"] label[aria-checked="true"] div[data-testid="stMarkdownContainer"] p {
    color: #fff8f6 !important;
    font-weight: 600 !important;
}
/* Hide the actual radio circle safely by targeting the SVG or specific inner divs */
[data-testid="stSidebar"] [role="radiogroup"] label svg {
    display: none !important;
}
</style>""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:32px;padding-top:10px;'>
        <div style='width:36px;height:36px;background:#ab2f00;border-radius:2px;display:flex;align-items:center;justify-content:center;'>
            <span class="material-symbols-outlined" style="color:#fff;font-size:20px;">psychology</span>
        </div>
        <div>
            <div style='font-family:"Instrument Serif",serif;font-style:italic;font-size:24px;color:#fff8f6;line-height:1.2;'>DocuMind</div>
            <div style='font-size:10px;color:rgba(250,220,212,0.5);letter-spacing:0.15em;font-weight:600;'>AI INTELLIGENCE</div>
        </div>
    </div>
    <hr style='border-color:rgba(228,190,180,0.1);margin:0 0 16px;'>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", ["Dashboard", "Automation", "History"], label_visibility="collapsed")
    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Reset button ────────────────────────────────────────────────────────
    if st.button("➕ New Analysis", key="reset_btn", type="secondary"):
        for key in ["auto_image", "auto_label", "direct_text"]:
            st.session_state.pop(key, None)
        st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
        st.rerun()

    st.markdown("""
    <div style='margin-top:24px;display:flex;flex-direction:column;gap:12px;font-size:13px;color:rgba(250,220,212,0.6);font-weight:500;'>
        <div style="display:flex;align-items:center;gap:8px;cursor:pointer;"><span class="material-symbols-outlined" style="font-size:16px;">help</span> Help Center</div>
        <div style="display:flex;align-items:center;gap:8px;cursor:pointer;"><span class="material-symbols-outlined" style="font-size:16px;">account_circle</span> Account</div>
    </div>
    <div style='font-size:11px;color:rgba(250,220,212,0.3);margin-top:24px;'>
        MCA Major Project<br>Trishant Srivastava
    </div>""", unsafe_allow_html=True)

# ── Global State Settings ──────────────────────────────────────────────────────
if "settings" not in st.session_state:
    st.session_state["settings"] = {
        "use_preprocess": True,
        "preprocess_mode": "standard",
        "psm_label": DEFAULT_PSM_LABEL,
        "conf_threshold": 0.0,
        "filter_types": [
            "PERSON","ORG","DATE","GPE","MONEY","CARDINAL","PERCENT","TIME",
            "FAC","PRODUCT","EMAIL","INVOICE_NUMBER","PHONE","PAN","GSTIN","CURRENCY","URL",
            "Invoice Number","Invoice Date","Due Date","Total Amount","Subtotal",
            "Tax / GST","Vendor Name","Customer Name","Website",
        ]
    }

settings = st.session_state["settings"]
use_preprocess = settings["use_preprocess"]
preprocess_mode = settings["preprocess_mode"]
psm_label = settings["psm_label"]
psm_config = PSM_OPTIONS[psm_label]
conf_threshold = settings["conf_threshold"]
filter_types = settings["filter_types"]

# ── Helpers ────────────────────────────────────────────────────────────────────
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_docs")


def _load_sample(name):
    path = os.path.join(SAMPLE_DIR, name)
    return Image.open(path) if os.path.exists(path) else None


def _auto_detect_mode(uploaded_file) -> tuple:
    """Return (preprocess_mode, show_notice, best_psm_label) based on file type/size."""
    if uploaded_file is None:
        return preprocess_mode, False, psm_label
    ext = uploaded_file.name.split(".")[-1].lower()
    size = uploaded_file.size
    if ext in ("jpg", "jpeg") and size < 2 * 1024 * 1024:
        return "photo", True, PHOTO_PSM_LABEL
    return preprocess_mode, False, psm_label


def _process_image(pil_img: Image.Image, mode: str, psm: str) -> dict:
    timings = {}

    t0 = time.perf_counter()
    ocr_result = extract_text(
        pil_img,
        preprocess=use_preprocess,
        preprocess_mode=mode,
        psm_config=psm,
    )
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

    return {
        "raw_text":      raw_text,
        "cleaned_text":  cleaned,
        "sentences":     pre_result["sentences"],
        "tokens":        pre_result["tokens"],
        "entities":      ext_result["entities"],
        "doc_type":      ext_result.get("doc_type", "general"),
        "model_used":    ext_result.get("model_used", "N/A"),
        "spacy_failed":  ext_result.get("spacy_failed", False),
        "ocr_confidence": ocr_conf,
        "word_data":     word_data,
        "timings":       timings,
        "image":         pil_img,
        "config_used":   ocr_result.get("config_used", "N/A"),
        "pos_tags":      pos_tags,
    }


def _render_results(result: dict):
    entities = result["entities"]
    filtered = [
        e for e in entities
        if e["type"] in filter_types
        and CONF_SCORE.get(e["confidence"], 0) >= conf_threshold
    ]

    # ── Document type badge ────────────────────────────────────────────────────
    render_doc_type_badge(result.get("doc_type", "general"))

    # ── Summary metrics ────────────────────────────────────────────────────────
    total_time = sum(result["timings"].values())
    avg_conf_pct = round(
        (sum(CONF_SCORE.get(e["confidence"], 0) for e in entities) / len(entities) * 100)
        if entities else 0, 1
    )
    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, len(filtered),                   "Entities Found")
    metric_card(c2, f"{result['ocr_confidence']:.1f}%", "OCR Confidence")
    metric_card(c3, f"{avg_conf_pct}%",              "Extraction Confidence")
    metric_card(c4, f"{total_time:.0f} ms",          "Total Processing")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Warnings ───────────────────────────────────────────────────────────────
    if len(result["raw_text"].strip()) < 20:
        st.markdown('<div class="warn-box">⚠️ OCR extraction appears incomplete — try Photo mode or check image quality.</div>', unsafe_allow_html=True)
    if result.get("spacy_failed"):
        st.markdown('<div class="info-box">ℹ️ spaCy NLP unavailable — using regex-only extraction.</div>', unsafe_allow_html=True)
    if not filtered:
        st.markdown('<div class="warn-box">⚠️ No entities matched current filters.</div>', unsafe_allow_html=True)

    model = result.get("model_used", "N/A")
    st.markdown(f'<div class="info-box">🤖 spaCy model: <code>{model}</code> &nbsp;|&nbsp; Tesseract: <code>{result.get("config_used","N/A")}</code></div>', unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Extracted Text", "🧩 Entities", "🗂️ JSON View", "📈 Analytics", "🖼️ Document Preview"
    ])

    # Tab 1 — Text
    with tab1:
        mode_view = st.radio("View Mode", ["Side by Side","Raw Only","Cleaned Only"],
                             horizontal=True, label_visibility="collapsed")
        if mode_view == "Side by Side":
            col_r, col_c = st.columns(2)
            with col_r:
                st.markdown("**Raw OCR Output**")
                st.text_area("Raw OCR Output", result["raw_text"], height=400, key="raw_txt", label_visibility="collapsed")
            with col_c:
                st.markdown("**Cleaned / Preprocessed Text**")
                st.text_area("Cleaned Text", result["cleaned_text"], height=400, key="clean_txt", label_visibility="collapsed")
        elif mode_view == "Raw Only":
            st.text_area("Raw OCR Output", result["raw_text"], height=450)
        else:
            st.text_area("Cleaned Text", result["cleaned_text"], height=450)

        with st.expander("📊 Tokenization Details"):
            st.markdown(f"**Sentences:** {len(result['sentences'])} &nbsp;|&nbsp; **Tokens:** {len(result['tokens'])}", unsafe_allow_html=True)
            st.write(result["sentences"][:10])
            if result.get("pos_tags"):
                st.markdown("**POS Tags** (NOUN=🔵 VERB=🟢 NUM=🟠 PROPN=🟣)")
                render_pos_strip(result["pos_tags"])

    # Tab 2 — Entities
    with tab2:
        if filtered:
            df = pd.DataFrame(filtered)
            def _color_conf(val):
                m = {"high":"background-color:#064e3b;color:#6ee7b7",
                     "medium":"background-color:#78350f;color:#fcd34d",
                     "low":"background-color:#450a0a;color:#fca5a5"}
                return m.get(val,"")
            st.dataframe(df.style.map(_color_conf, subset=["confidence"]),
                         width="stretch", height=380)

            st.markdown("#### 📋 Entity Extraction Accuracy Table (Table 2)")
            render_accuracy_table(build_accuracy_table(filtered))
        else:
            st.info("No entities to display with current filters.")

    # Tab 3 — JSON
    with tab3:
        payload = {"entities": filtered, "ocr_confidence": result["ocr_confidence"],
                   "doc_type": result.get("doc_type"), "processing_timings_ms": result["timings"]}
        json_str = json.dumps(payload, indent=2)
        col_a, col_b = st.columns(2)
        col_a.json(payload)
        col_b.download_button("⬇️ Download JSON", data=json_str,
                              file_name="documind_extraction.json", mime="application/json")

    # Tab 4 — Analytics
    with tab4:
        if filtered:
            type_counts = pd.Series([e["type"] for e in filtered]).value_counts().reset_index()
            type_counts.columns = ["Entity Type","Count"]
            if _HAS_PLOTLY:
                fig = px.bar(type_counts, x="Entity Type", y="Count",
                             color="Entity Type",
                             color_discrete_sequence=list(ENTITY_COLORS.values()),
                             title="Entity Type Distribution", template="plotly_dark")
                fig.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117")
                st.plotly_chart(fig, width="stretch")

        # Precision / Recall / F1
        st.markdown("#### 🎯 Extraction Metrics (Proxy P / R / F1)")
        metrics = compute_extraction_metrics(entities)
        render_metrics_cards(metrics)

        # Processing timeline
        st.markdown("#### ⏱️ Processing Timeline")
        timings = result["timings"]
        total = sum(timings.values()) or 1
        seg_colors = {"preprocess_ms":"#f59e0b","ocr_ms":"#3b82f6",
                      "clean_ms":"#10b981","nlp_pre_ms":"#84cc16","extraction_ms":"#8b5cf6"}
        seg_labels = {"preprocess_ms":"Preprocess","ocr_ms":"OCR",
                      "clean_ms":"Cleaning","nlp_pre_ms":"NLP","extraction_ms":"Extraction"}
        segs = "".join(
            f'<div class="tl-seg" style="width:{max(round(timings.get(k,0)/total*100,1),1)}%;background:{c};">'
            f'{seg_labels[k]} ({timings.get(k,0):.0f}ms)</div>'
            for k, c in seg_colors.items() if timings.get(k, 0) > 0
        )
        st.markdown(f'<div class="timeline-bar">{segs}</div>', unsafe_allow_html=True)

        # Performance table (Table 3)
        st.markdown("#### 📋 Performance Metrics Table (Table 3)")
        render_performance_table(timings)

        st.markdown(f'<div class="info-box">🔧 Config: <code>{result.get("config_used","N/A")}</code></div>',
                    unsafe_allow_html=True)

    # Tab 5 — Preview
    with tab5:
        img = result["image"]
        word_data = result.get("word_data", {})
        view_opt = st.radio("Overlay", ["None","OCR Bounding Boxes","Confidence Heatmap"],
                            horizontal=True)
        if view_opt == "OCR Bounding Boxes" and word_data.get("text"):
            with st.spinner("Drawing boxes…"):
                img = draw_bboxes(img, word_data)
        elif view_opt == "Confidence Heatmap" and word_data.get("text"):
            with st.spinner("Building heatmap…"):
                img = draw_confidence_heatmap(img, word_data)
        st.image(img, width="stretch", caption="Document Preview")

        st.markdown("**🟢 ≥80% conf &nbsp; 🟡 50-79% &nbsp; 🔴 <50%** (heatmap key)")

        st.markdown("#### 🎨 Entity Color Legend")
        cols = st.columns(4)
        for i,(etype,color) in enumerate(ENTITY_COLORS.items()):
            cols[i%4].markdown(
                f'<span style="background:{color};color:#111;padding:2px 8px;'
                f'border-radius:8px;font-size:11px;font-weight:600;">{etype}</span>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
if page == "Automation":
    st.markdown("""
    <h5 style='color:#ab2f00;font-size:12px;font-weight:700;letter-spacing:0.1em;'>AUTOMATION</h5>
    <h1 style='color:#271813;margin-bottom:8px;font-family:"Instrument Serif",serif;font-size:48px;'>Configure pipelines.</h1>
    <p style='color:#5b4039;font-size:1.1rem;margin-bottom:32px;'>Set up extraction rules and automated workflows for recurring document types.</p>
    """, unsafe_allow_html=True)

    col_set1, col_set2 = st.columns([1, 1], gap="large")
    with col_set1:
        st.markdown("<h3 style='font-size:24px;margin-bottom:16px;'>OCR Settings</h3>", unsafe_allow_html=True)
        st.session_state["settings"]["use_preprocess"] = st.checkbox("Enable Image Preprocessing", value=settings["use_preprocess"])
        st.session_state["settings"]["preprocess_mode"] = st.selectbox("Preprocessing Mode", ["standard", "aggressive", "photo"], index=["standard", "aggressive", "photo"].index(settings["preprocess_mode"]))
        st.session_state["settings"]["psm_label"] = st.selectbox("PSM Mode (Tesseract)", list(PSM_OPTIONS.keys()), index=list(PSM_OPTIONS.keys()).index(settings["psm_label"]))
        st.session_state["settings"]["conf_threshold"] = st.slider("Min Confidence Threshold", 0.0, 1.0, settings["conf_threshold"], 0.05)
    
    with col_set2:
        st.markdown("<h3 style='font-size:24px;margin-bottom:16px;'>Entity Filters</h3>", unsafe_allow_html=True)
        all_types = [
            "PERSON","ORG","DATE","GPE","MONEY","CARDINAL","PERCENT","TIME",
            "FAC","PRODUCT","EMAIL","INVOICE_NUMBER","PHONE","PAN","GSTIN","CURRENCY","URL",
            "Invoice Number","Invoice Date","Due Date","Total Amount","Subtotal",
            "Tax / GST","Vendor Name","Customer Name","Website",
        ]
        st.session_state["settings"]["filter_types"] = st.multiselect("Entity Types to Show", all_types, default=settings["filter_types"], label_visibility="collapsed")

    st.stop()

if page == "History":
    st.markdown("""
    <h5 style='color:#ab2f00;font-size:12px;font-weight:700;letter-spacing:0.1em;'>HISTORY</h5>
    <h1 style='color:#271813;margin-bottom:8px;font-family:"Instrument Serif",serif;font-size:48px;'>Analysis history.</h1>
    <p style='color:#5b4039;font-size:1.1rem;margin-bottom:32px;'>Past analyses are not stored permanently in Streamlit Community Cloud.</p>
    """, unsafe_allow_html=True)
    st.info("No persistent history available in this session.")
    st.stop()

# ── Dashboard (Main App) ──────────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#ab2f00;margin-bottom:4px;font-family:"Instrument Serif",serif;font-size:48px;'>DocuMind</h1>
<p style='color:#5b4039;margin-top:0;font-size:1.1rem;font-weight:400;'>
Start your intelligence analysis.
</p>
<hr style='border-color:rgba(228,190,180,0.4);margin:8px 0 24px;'>
""", unsafe_allow_html=True)

# Sample gallery
samples = {"🧾 Invoice":"sample_invoice.png","📝 Business Letter":"sample_letter.png","🛒 Receipt":"sample_receipt.png"}
sample_images = {lbl: _load_sample(fn) for lbl, fn in samples.items()}
if any(v for v in sample_images.values()):
    with st.expander("🎯 Try a Sample Document", expanded=False):
        s_cols = st.columns(3)
        for i,(lbl,img) in enumerate(sample_images.items()):
            if img:
                with s_cols[i]:
                    st.image(img, caption=lbl, width="stretch")
                    if st.button(f"Use {lbl}", key=f"sample_{i}"):
                        st.session_state["auto_image"] = img
                        st.session_state["auto_label"] = lbl
                        st.rerun()

# File uploader
st.markdown("### 📁 Upload Your Document")
_uploader_key = st.session_state.get("uploader_key", 0)
uploaded_file = st.file_uploader(
    "PNG, JPG, JPEG, PDF — max 10 MB",
    type=["png", "jpg", "jpeg", "pdf"],
    label_visibility="collapsed",
    key=f"file_uploader_{_uploader_key}",
)

active_image = None
active_label = "Uploaded Document"
effective_mode = preprocess_mode
photo_notice = False

if uploaded_file and uploaded_file.size > 10*1024*1024:
    st.error("❌ File exceeds 10 MB limit.")
    uploaded_file = None

if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    effective_mode, photo_notice, effective_psm_label = _auto_detect_mode(uploaded_file)
    effective_psm = PSM_OPTIONS[effective_psm_label]
    if ext == "pdf":
        if not _HAS_FITZ:
            st.error("❌ PDF support requires PyMuPDF. Run: `pip install PyMuPDF`")
            uploaded_file = None
        else:
            from utils.pdf_handler import open_pdf, is_scanned_page, page_to_pil, extract_page_text, get_pdf_info
            pdf_bytes = uploaded_file.read()
            doc = open_pdf(pdf_bytes)
            info = get_pdf_info(doc)
            st.markdown(f'<div class="info-box">📄 PDF — <b>{info["page_count"]} page(s)</b> | {info["title"] or "N/A"}</div>',
                        unsafe_allow_html=True)
            page_idx = 0
            if info["page_count"] > 1:
                page_idx = st.slider("Select Page", 1, info["page_count"], 1) - 1
            page = doc[page_idx]
            if not is_scanned_page(page):
                st.markdown('<div class="info-box">ℹ️ Selectable text detected — skipping OCR.</div>', unsafe_allow_html=True)
                st.session_state["direct_text"] = extract_page_text(page)
            else:
                st.session_state.pop("direct_text", None)
            active_image = page_to_pil(page)
            active_label = f"PDF Page {page_idx+1}"
    else:
        active_image = Image.open(uploaded_file)
        active_label = uploaded_file.name
        st.session_state.pop("direct_text", None)
elif "auto_image" in st.session_state:
    active_image = st.session_state["auto_image"]
    active_label = st.session_state.get("auto_label","Sample Document")
    effective_mode = preprocess_mode
    effective_psm  = psm_config
    effective_psm_label = psm_label
    photo_notice = False
    st.session_state.pop("direct_text", None)

# Process & render
if active_image is not None:
    # ── Quality assessment + smart routing (Option B) ──────────────────────
    quality  = assess_image_quality(active_image)
    file_ext = (uploaded_file.name.split(".")[-1] if uploaded_file else "png")
    routing  = route_ocr_engine(quality, file_ext)

    # Routing decision badge
    engine_color = {
        "tesseract_standard":   "#10b981",
        "tesseract_aggressive": "#f59e0b",
        "reject":               "#ef4444",
    }.get(routing["engine"], "#94a3b8")
    engine_icon = {
        "tesseract_standard":   "🟢",
        "tesseract_aggressive": "🟡",
        "reject":               "🔴",
    }.get(routing["engine"], "⚪")
    st.markdown(
        f'<div style="display:inline-block;background:{engine_color}22;border:1px solid {engine_color};'
        f'border-radius:20px;padding:4px 16px;color:{engine_color};font-size:0.85rem;margin-bottom:10px;">'
        f'{engine_icon} OCR Route: <b>{routing["engine"]}</b> — {routing["reason"]}</div>',
        unsafe_allow_html=True,
    )

    # Hard reject — show honest guidance and stop
    if routing["engine"] == "reject":
        st.error("❌ This image cannot be reliably processed by Tesseract OCR.")
        st.markdown(REJECTION_TIPS)
        with st.expander("📊 Image Quality Report"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall Score",  f"{quality['overall_score']}/100")
            c2.metric("Blur Score",     f"{quality['blur_score']}/100",
                      delta="Blurry" if quality['is_blurry'] else "Sharp")
            c3.metric("Contrast",       f"{quality['contrast_score']}/100")
            c4.metric("Resolution",     quality['resolution_px'])
            if quality.get("perspective_warning"):
                st.warning(f"📐 {quality['perspective_note']}")
        st.stop()

    # Show quality banner for accepted images
    verdict = quality["verdict"]
    if verdict == "good":
        st.success(f"✅ Image quality: Good ({quality['overall_score']}/100)")
    elif verdict == "marginal":
        st.warning(f"⚠️ Image quality: Marginal ({quality['overall_score']}/100) — {quality['message']}")

    with st.expander("📊 Image Quality Report"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Score",  f"{quality['overall_score']}/100")
        c2.metric("Blur Score",     f"{quality['blur_score']}/100",
                  delta="Blurry" if quality['is_blurry'] else "Sharp")
        c3.metric("Contrast",       f"{quality['contrast_score']}/100",
                  delta="Low" if quality['is_low_contrast'] else "Good")
        c4.metric("Resolution",     quality['resolution_px'])
        st.caption(f"Laplacian variance: {quality['laplacian_variance']} (≥100 = sharp)")
        if quality.get("perspective_warning"):
            st.warning(f"📐 {quality['perspective_note']}")

    # Router-recommended mode and PSM override sidebar selectors
    final_mode = routing["mode"]
    final_psm  = routing["psm"]

    if photo_notice:
        st.markdown(
            f'<div class="photo-notice">📷 Photo document detected — '
            f'routing to <b>{routing["engine"]}</b> mode.</div>',
            unsafe_allow_html=True)
    st.markdown(f"**Processing:** `{active_label}`")

    if "direct_text" in st.session_state:
        from utils.preprocess import clean_text as _ct
        from utils.extract import extract_entities as _ee, get_pos_tags as _pt
        raw = st.session_state["direct_text"]
        pre = _ct(raw)
        ext = _ee(pre["cleaned"])
        result = {
            "raw_text": raw, "cleaned_text": pre["cleaned"],
            "sentences": pre["sentences"], "tokens": pre["tokens"],
            "entities": ext["entities"], "doc_type": ext.get("doc_type","general"),
            "model_used": ext.get("model_used","N/A"),
            "spacy_failed": ext.get("spacy_failed",False),
            "ocr_confidence": 100.0, "word_data": {},
            "timings": {"preprocess_ms":0,"ocr_ms":0,"clean_ms":pre["duration_ms"],
                        "nlp_pre_ms":0,"extraction_ms":ext["duration_ms"]},
            "image": active_image, "config_used":"N/A (direct PDF text)",
            "pos_tags": _pt(pre["cleaned"]),
        }
    else:
        with st.spinner("📐 Auto-cropping document…"):
            original_for_preview = active_image
            cropped_img, strategy = auto_crop_document(active_image)

        if strategy:
            st.success(f"📐 Document automatically isolated ({strategy}).")
            with st.expander("👁️ Before / After Auto-Crop", expanded=False):
                col_b, col_a = st.columns(2)
                col_b.image(original_for_preview, caption="Original",
                            width="stretch")
                col_a.image(cropped_img, caption=f"Auto-cropped ({strategy})",
                            width="stretch")
        else:
            st.info("ℹ️ Document boundary not detected — processing full image.")

        with st.spinner("🔡 Running OCR…"):
            result = _process_image(cropped_img, final_mode, final_psm)
        with st.spinner("🧠 Extracting entities…"):
            pass

    _render_results(result)
else:
    st.markdown("""
    <div style='text-align:center;padding:64px 32px;
                background-color:#ffffff;
                border-radius:8px;border:1px dashed #907067;'>
        <span class="material-symbols-outlined" style="font-size:48px;color:#ab2f00;">upload_file</span>
        <h3 style='color:#271813;margin:16px 0 8px;font-family:"Instrument Serif",serif;font-size:32px;'>Click to upload or drag and drop</h3>
        <p style='color:#5b4039;max-width:480px;margin:0 auto;font-size:15px;'>
            PDF, DOCX, and scanned images (PNG, JPG) supported.<br>
            High-resolution scans recommended for OCR accuracy.
        </p>
    </div>
    """, unsafe_allow_html=True)
