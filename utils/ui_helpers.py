"""utils/ui_helpers.py — reusable rendering helpers for DocuMind app."""
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

try:
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

CONF_SCORE = {"high": 1.0, "medium": 0.5, "low": 0.2}

ENTITY_COLORS = {
    "PERSON":"#f59e0b","ORG":"#3b82f6","DATE":"#10b981","GPE":"#8b5cf6",
    "MONEY":"#ef4444","CARDINAL":"#f97316","PERCENT":"#06b6d4","TIME":"#84cc16",
    "FAC":"#ec4899","PRODUCT":"#a78bfa","EMAIL":"#14b8a6","INVOICE_NUMBER":"#fb923c",
    "PHONE":"#60a5fa","PAN":"#f43f5e","GSTIN":"#a3e635","CURRENCY":"#fbbf24","URL":"#38bdf8",
    "Invoice Number":"#fb923c","Invoice Date":"#10b981","Due Date":"#f59e0b",
    "Total Amount":"#ef4444","Subtotal":"#f97316","Tax / GST":"#06b6d4",
    "Vendor Name":"#3b82f6","Customer Name":"#8b5cf6","Website":"#38bdf8",
}

DOC_TYPE_EMOJI = {"invoice":"🧾","letter":"📝","form":"📋","report":"📊","general":"📄"}
DOC_TYPE_COLOR = {"invoice":"#f59e0b","letter":"#3b82f6","form":"#10b981","report":"#8b5cf6","general":"#94a3b8"}


def metric_card(col, value, label):
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>""", unsafe_allow_html=True)


def draw_bboxes(pil_img: Image.Image, word_data: dict) -> Image.Image:
    img_copy = pil_img.convert("RGBA")
    overlay = Image.new("RGBA", img_copy.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(len(word_data.get("text", []))):
        conf = word_data["conf"][i]
        word = str(word_data["text"][i]).strip()
        if conf < 0 or not word:
            continue
        x, y, w, h = word_data["left"][i], word_data["top"][i], word_data["width"][i], word_data["height"][i]
        color = (16, 185, 129, 80) if conf > 70 else (245, 158, 11, 80)
        d.rectangle([x, y, x+w, y+h], outline=(16, 185, 129, 200), fill=color, width=1)
    return Image.alpha_composite(img_copy, overlay).convert("RGB")


def render_doc_type_badge(doc_type: str):
    emoji = DOC_TYPE_EMOJI.get(doc_type, "📄")
    color = DOC_TYPE_COLOR.get(doc_type, "#94a3b8")
    label = doc_type.title()
    st.markdown(
        f'<div style="display:inline-block;background:{color}22;border:1px solid {color};'
        f'border-radius:20px;padding:4px 16px;color:{color};font-weight:600;font-size:0.9rem;margin-bottom:12px;">'
        f'{emoji} {label} Detected</div>',
        unsafe_allow_html=True
    )


def render_pos_strip(pos_tags: list):
    if not pos_tags:
        return
    html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;">'
    for t in pos_tags[:80]:
        color = t.get("color", "#94a3b8")
        word = t["word"]
        pos  = t["pos"]
        html += (f'<span style="background:{color}22;border:1px solid {color};color:{color};'
                 f'padding:2px 6px;border-radius:6px;font-size:11px;" title="{pos}">'
                 f'{word}</span>')
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_metrics_cards(metrics: dict):
    c1, c2, c3 = st.columns(3)
    metric_card(c1, f"{metrics['precision']}%", "Precision (proxy)")
    metric_card(c2, f"{metrics['recall']}%",    "Recall (proxy)")
    metric_card(c3, f"{metrics['f1']}%",         "F1 Score (proxy)")


def render_performance_table(timings: dict):
    labels = {
        "preprocess_ms": "Image Preprocessing",
        "ocr_ms":        "OCR Extraction",
        "clean_ms":      "Text Cleaning",
        "nlp_pre_ms":    "NLP Processing",
        "extraction_ms": "Entity Extraction",
    }
    rows = [{"Stage": labels.get(k, k), "Time (ms)": round(v, 1), "Status": "✅"}
            for k, v in timings.items() if v is not None]
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    if _HAS_PLOTLY and not df.empty:
        fig = px.bar(df, x="Time (ms)", y="Stage", orientation="h",
                     color="Stage", template="plotly_dark",
                     title="Time per Processing Stage")
        fig.update_layout(showlegend=False, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117")
        st.plotly_chart(fig, width="stretch")


def render_accuracy_table(accuracy_rows: list):
    if not accuracy_rows:
        st.info("No entities extracted yet.")
        return
    df = pd.DataFrame(accuracy_rows)
    st.dataframe(df, width="stretch", hide_index=True)
