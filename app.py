# app.py
# Arabic Cataloger (Streamlit)
# Upload images -> Arabic OCR (Tesseract) -> Extract bibliographic fields -> Suggest LCC/LCSH -> Generate MARC21 + MARCXML
# Requires:
# - requirements.txt (python deps)
# - packages.txt (tesseract-ocr + tesseract-ocr-ara + libs) for Streamlit Community Cloud

from __future__ import annotations

import io
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict

import streamlit as st
from PIL import Image

import numpy as np
import cv2
import pytesseract
from pymarc import Record, Field, XMLWriter


# ======================================================================================
# Page Config + UI Helpers
# ======================================================================================

st.set_page_config(
    page_title="Arabic Cataloger",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

RTL_CSS = """
<style>
* { direction: rtl; }
html, body, [data-testid="stAppViewContainer"] { font-family: "Segoe UI", Tahoma, Arial, sans-serif; }
code, pre, textarea { direction: ltr !important; } /* keep MARC + XML readable */
.small-note { color: #64748b; font-size: 0.9rem; }
.badge { display:inline-block; padding: 2px 10px; border-radius: 999px; background:#0f172a; color:#fff; font-size: 12px; }
.card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 16px; box-shadow: 0 1px 1px rgba(15,23,42,.04); }
</style>
"""
st.markdown(RTL_CSS, unsafe_allow_html=True)


# ======================================================================================
# Data Model
# ======================================================================================

@dataclass
class ExtractedEntity:
    title: Optional[str] = None
    subtitle: Optional[str] = None
    statement_of_responsibility: Optional[str] = None
    authors: List[str] = None
    edition: Optional[str] = None
    place_of_publication: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[str] = None
    isbn: Optional[str] = None
    language: str = "ara"
    physical_description: Optional[str] = None
    notes: List[str] = None


@dataclass
class SubjectSuggestion:
    scheme: str
    heading: str
    confidence: float


@dataclass
class ClassificationSuggestion:
    scheme: str
    classmark: str
    confidence: float


# ======================================================================================
# Image Preprocessing for OCR
# ======================================================================================

def preprocess_image(pil_img: Image.Image) -> np.ndarray:
    """
    Improve OCR accuracy:
    - RGB -> gray
    - bilateral filter (denoise while preserving edges)
    - adaptive threshold
    """
    rgb = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        41, 11
    )
    return th


# ======================================================================================
# OCR (Tesseract)
# ======================================================================================

@st.cache_resource
def tesseract_config() -> str:
    # Arabic language + decent paragraph segmentation
    # --psm 6: Assume a block of text
    return r"-l ara --oem 1 --psm 6"


def run_ocr(images: List[Image.Image]) -> str:
    cfg = tesseract_config()
    pages: List[str] = []
    for idx, img in enumerate(images):
        arr = preprocess_image(img)
        text = pytesseract.image_to_string(arr, config=cfg)
        pages.append(text.strip())
    return "\n\n".join([p for p in pages if p])


# ======================================================================================
# Heuristic Extraction (Starter Rules)
# ======================================================================================

ISBN_RE = re.compile(r"(97[89][-\s]?)?\d{9}[\dXx]")
YEAR_RE = re.compile(r"(19|20)\d{2}")

def _clean(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s2 = " ".join(s.split()).strip()
    return s2 if s2 else None


def normalize_authors(authors: List[str] | None) -> List[str]:
    if not authors:
        return []
    cleaned: List[str] = []
    for a in authors:
        a2 = " ".join(a.split()).strip().strip("،. ")
        if a2:
            cleaned.append(a2)
    # unique keep order
    seen = set()
    out = []
    for a in cleaned:
        if a not in seen:
            out.append(a)
            seen.add(a)
    return out


def split_title_subtitle(title_line: str) -> Tuple[str, Optional[str]]:
    """
    Try to split title/subtitle by common separators:
    "العنوان : العنوان الفرعي"
    "العنوان - العنوان الفرعي"
    """
    for sep in [" : ", " - ", " — ", " ـ "]:
        if sep in title_line:
            parts = [p.strip() for p in title_line.split(sep, 1)]
            if len(parts) == 2 and parts[0]:
                return parts[0], parts[1] if parts[1] else None
    return title_line.strip(), None


def heuristic_extract(ocr_text: str) -> ExtractedEntity:
    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
    joined = " ".join(lines)

    isbn = None
    m = ISBN_RE.search(joined)
    if m:
        isbn = m.group(0).replace(" ", "").replace("-", "")

    year = None
    ym = YEAR_RE.search(joined)
    if ym:
        year = ym.group(0)

    # Title guess: first meaningful long line among first 6 lines
    title_line = None
    if lines:
        head = lines[: min(6, len(lines))]
        title_line = max(head, key=len) if head else lines[0]
    title = None
    subtitle = None
    if title_line:
        t, stt = split_title_subtitle(title_line)
        title = _clean(t)
        subtitle = _clean(stt)

    # Authors guess by keywords
    authors: List[str] = []
    for kw in ["تأليف", "إعداد", "بقلم", "تحرير", "ترجمة", "مراجعة"]:
        m2 = re.search(rf"{kw}\s*[:\-]?\s*(.+)", joined)
        if m2:
            cand = m2.group(1)
            # stop at common separators
            cand = cand.split("،")[0].split("/")[0].split("؛")[0].strip()
            if cand:
                authors.append(cand)

    # Edition guess
    edition = None
    ed_m = re.search(r"(الطبعة\s+[اأإآء-ي0-9\s]+)", joined)
    if ed_m:
        edition = ed_m.group(1).strip()

    # Publication place/publisher guess (very heuristic)
    place = None
    publisher = None
    # Example: "مسقط : دار المعرفة"
    pub_m = re.search(r"([اأإآء-ي\s]{2,})\s*:\s*([اأإآء-ي\s]{2,})", joined)
    if pub_m:
        place = pub_m.group(1).strip()
        publisher = pub_m.group(2).strip()

    # Physical description guess (pages)
    physical = None
    ph_m = re.search(r"(\d+\s*(?:ص|صفحة|صفحات).{0,20}(?:سم)?)", joined)
    if ph_m:
        physical = ph_m.group(1).strip()

    ent = ExtractedEntity(
        title=title,
        subtitle=subtitle,
        statement_of_responsibility=None,
        authors=normalize_authors(authors),
        edition=_clean(edition),
        place_of_publication=_clean(place),
        publisher=_clean(publisher),
        year=_clean(year),
        isbn=_clean(isbn),
        language="ara",
        physical_description=_clean(physical),
        notes=[],
    )
    return ent


# ======================================================================================
# LCC + LCSH Suggestions (Local starter mapping)
# ======================================================================================

# You can expand these dictionaries later or replace with an API/authority file.
LCC_LOCAL = [
    {"classmark": "QM", "label": "Human anatomy", "ar": ["التشريح", "علم التشريح"]},
    {"classmark": "R",  "label": "Medicine (General)", "ar": ["الطب", "علوم طبية"]},
    {"classmark": "Z",  "label": "Library science", "ar": ["فهرسة", "علم المكتبات", "المكتبات"]},
    {"classmark": "QA", "label": "Mathematics / Computer Science", "ar": ["حوسبة", "ذكاء اصطناعي", "حاسوب", "خوارزميات"]},
]

LCSH_LOCAL = [
    {"heading": "Anatomy", "ar": ["التشريح", "علم التشريح"]},
    {"heading": "Medicine", "ar": ["الطب", "علوم طبية"]},
    {"heading": "Cataloging", "ar": ["الفهرسة", "الوصف الببليوجرافي"]},
    {"heading": "Library science", "ar": ["علم المكتبات", "المكتبات"]},
    {"heading": "Artificial intelligence", "ar": ["الذكاء الاصطناعي"]},
]


def _simple_confidence(keyword: str, hay: str) -> float:
    """
    Very simple confidence:
    - exact keyword occurrence -> higher score
    - partial word overlap -> moderate
    """
    if not keyword or not hay:
        return 0.0
    if keyword in hay:
        return 0.92
    # overlap
    k_tokens = set(keyword.split())
    h_tokens = set(hay.split())
    if not k_tokens:
        return 0.0
    inter = len(k_tokens & h_tokens)
    return min(0.85, inter / max(1, len(k_tokens)) * 0.85)


def suggest_lcc(ent: ExtractedEntity, ocr_text: str) -> List[ClassificationSuggestion]:
    hay = f"{ent.title or ''} {ent.subtitle or ''} {ocr_text}".strip()
    out: List[ClassificationSuggestion] = []
    for item in LCC_LOCAL:
        best = 0.0
        for kw in item["ar"]:
            best = max(best, _simple_confidence(kw, hay))
        if best >= 0.75:
            out.append(ClassificationSuggestion(scheme="LCC", classmark=item["classmark"], confidence=best))
    out.sort(key=lambda x: x.confidence, reverse=True)
    return out[:3]


def suggest_lcsh(ent: ExtractedEntity, ocr_text: str) -> List[SubjectSuggestion]:
    hay = f"{ent.title or ''} {ent.subtitle or ''} {ocr_text}".strip()
    out: List[SubjectSuggestion] = []
    for item in LCSH_LOCAL:
        best = 0.0
        for kw in item["ar"]:
            best = max(best, _simple_confidence(kw, hay))
        if best >= 0.75:
            out.append(SubjectSuggestion(scheme="LCSH", heading=item["heading"], confidence=best))
    out.sort(key=lambda x: x.confidence, reverse=True)
    return out[:6]


# ======================================================================================
# MARC21 + MARCXML Generation (RDA-friendly baseline)
# ======================================================================================

def build_marc(ent: ExtractedEntity,
               subjects: List[SubjectSuggestion] | None = None,
               classifications: List[ClassificationSuggestion] | None = None) -> Tuple[str, str]:
    record = Record(force_utf8=True)
    record.leader = "00000nam a2200000 a 4500"

    # 040 Cataloging source + RDA
    record.add_field(Field(tag="040", indicators=[" ", " "], subfields=[
        "a", "AR-CAT",
        "b", "ara",
        "e", "rda"
    ]))

    # 020 ISBN
    if ent.isbn:
        record.add_field(Field(tag="020", indicators=[" ", " "], subfields=["a", ent.isbn]))

    # 100 Main entry - personal name (first author)
    if ent.authors:
        record.add_field(Field(tag="100", indicators=["1", " "], subfields=["a", ent.authors[0]]))

    # 245 Title statement
    title = ent.title or "[عنوان غير محدد]"
    subfields = ["a", title]
    if ent.subtitle:
        subfields += ["b", ent.subtitle]
    if ent.statement_of_responsibility:
        subfields += ["c", ent.statement_of_responsibility]
    elif ent.authors:
        subfields += ["c", "؛ ".join(ent.authors)]

    record.add_field(Field(tag="245", indicators=["1", "0"], subfields=subfields))

    # 250 Edition statement
    if ent.edition:
        record.add_field(Field(tag="250", indicators=[" ", " "], subfields=["a", ent.edition]))

    # 264 Publication (RDA)
    pub_sub = []
    if ent.place_of_publication:
        pub_sub += ["a", ent.place_of_publication]
    if ent.publisher:
        pub_sub += ["b", ent.publisher]
    if ent.year:
        pub_sub += ["c", ent.year]
    if pub_sub:
        record.add_field(Field(tag="264", indicators=[" ", "1"], subfields=pub_sub))

    # 300 Physical description
    if ent.physical_description:
        record.add_field(Field(tag="300", indicators=[" ", " "], subfields=["a", ent.physical_description]))

    # 041 Language code
    if ent.language:
        record.add_field(Field(tag="041", indicators=["0", " "], subfields=["a", ent.language]))

    # 650 Subject headings (LCSH)
    if subjects:
        for s in subjects[:6]:
            record.add_field(Field(tag="650", indicators=[" ", "0"], subfields=["a", s.heading]))

    # 050 LCC classification
    if classifications and len(classifications) > 0:
        # Put best classmark into 050 $a
        record.add_field(Field(tag="050", indicators=[" ", "0"], subfields=["a", classifications[0].classmark]))

    # 500 Notes
    for n in ent.notes or []:
        if n and n.strip():
            record.add_field(Field(tag="500", indicators=[" ", " "], subfields=["a", n.strip()]))

    marc_text = record.as_marc21().decode("utf-8", errors="ignore")

    # MARCXML
    buff = io.BytesIO()
    writer = XMLWriter(buff)
    writer.write(record)
    writer.close()
    marcxml = buff.getvalue().decode("utf-8", errors="ignore")

    return marc_text, marcxml


# ======================================================================================
# Streamlit UI
# ======================================================================================

st.title("📚 Arabic Cataloger — الفهرسة العربية الذكية")
st.write(
    "ارفع صور صفحة العنوان/البيانات الببليوجرافية، وسيقوم النظام بـ OCR عربي ثم استخراج الحقول وتوليد MARC21/MARCXML."
)
st.markdown('<div class="small-note">نسخة أولية قابلة للتطوير (RDA/MARC21 + اقتراحات LCC/LCSH مبدئية).</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    st.markdown("**OCR:** Tesseract (Arabic) — يعتمد على `packages.txt`.")
    st.markdown("**ملاحظة:** كلما كانت الصورة أوضح، كانت النتائج أدق.")
    show_debug = st.toggle("عرض معلومات إضافية (Debug)", value=False)

# Upload images
uploaded = st.file_uploader(
    "ارفع صور صفحة العنوان/البيانات (يمكن رفع أكثر من صورة)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

if not uploaded:
    st.info("⬆️ ابدأ برفع صور لصفحة العنوان/البيانات الببليوجرافية.")
    st.stop()

images = [Image.open(io.BytesIO(f.getvalue())) for f in uploaded]

# Show thumbnails
with st.expander("🖼️ معاينة الصور المرفوعة", expanded=False):
    cols = st.columns(min(4, len(images)))
    for i, img in enumerate(images):
        cols[i % len(cols)].image(img, caption=f"صورة {i+1}", use_container_width=True)

# OCR
with st.spinner("🔍 جاري تنفيذ OCR عربي..."):
    ocr_text = run_ocr(images)

# Extract
with st.spinner("🧠 جاري استخراج البيانات..."):
    extracted = heuristic_extract(ocr_text)

# Suggestions
subjects = suggest_lcsh(extracted, ocr_text)
classifs = suggest_lcc(extracted, ocr_text)

# Allow editing
st.markdown("---")
st.markdown("## ✍️ مراجعة وتعديل البيانات قبل توليد MARC")

c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("البيانات المستخرجة (قابلة للتعديل)")
    title = st.text_input("العنوان (Title)", value=extracted.title or "")
    subtitle = st.text_input("العنوان الفرعي (Subtitle)", value=extracted.subtitle or "")
    sor = st.text_input("بيان المسؤولية (Statement of Responsibility)", value=extracted.statement_of_responsibility or "")
    authors_str = st.text_area("المؤلفون (افصل بينهم بـ ؛)", value="؛ ".join(extracted.authors or []), height=70)
    edition = st.text_input("الطبعة (Edition)", value=extracted.edition or "")
    place = st.text_input("مكان النشر (Place)", value=extracted.place_of_publication or "")
    publisher = st.text_input("الناشر (Publisher)", value=extracted.publisher or "")
    year = st.text_input("سنة النشر (Year)", value=extracted.year or "")
    isbn = st.text_input("ISBN", value=extracted.isbn or "")
    physical = st.text_input("الوصف المادي (Physical)", value=extracted.physical_description or "")
    notes_str = st.text_area("ملاحظات (كل سطر ملاحظة)", value="\n".join(extracted.notes or []), height=90)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("اقتراحات التصنيف والموضوعات")
    st.markdown("**LCC (تصنيف):**")
    if classifs:
        for c in classifs:
            st.write(f"- `{c.classmark}`  —  {int(c.confidence*100)}%")
    else:
        st.write("لا توجد اقتراحات حالياً.")

    st.markdown("**LCSH (رؤوس موضوعات):**")
    if subjects:
        for s in subjects:
            st.write(f"- {s.heading}  —  {int(s.confidence*100)}%")
    else:
        st.write("لا توجد اقتراحات حالياً.")
    st.markdown("</div>", unsafe_allow_html=True)

# Update entity based on edits
edited_entity = ExtractedEntity(
    title=_clean(title),
    subtitle=_clean(subtitle),
    statement_of_responsibility=_clean(sor),
    authors=normalize_authors([a.strip() for a in authors_str.split("؛") if a.strip()]),
    edition=_clean(edition),
    place_of_publication=_clean(place),
    publisher=_clean(publisher),
    year=_clean(year),
    isbn=_clean(isbn),
    language="ara",
    physical_description=_clean(physical),
    notes=[n.strip() for n in notes_str.splitlines() if n.strip()],
)

# Generate MARC
st.markdown("---")
st.markdown("## 📦 إخراج MARC21 / MARCXML")

with st.spinner("🧾 جاري توليد MARC..."):
    marc_text, marc_xml = build_marc(edited_entity, subjects=subjects, classifications=classifs)

out1, out2 = st.columns([1, 1], gap="large")

with out1:
    st.subheader("MARC21 (Text)")
    st.code(marc_text, language="text")
    st.download_button(
        "⬇️ تنزيل MARC21 (txt)",
        data=marc_text.encode("utf-8"),
        file_name="record.marc21.txt",
        mime="text/plain",
        use_container_width=True
    )

with out2:
    st.subheader("MARCXML")
    st.code(marc_xml, language="xml")
    st.download_button(
        "⬇️ تنزيل MARCXML (xml)",
        data=marc_xml.encode("utf-8"),
        file_name="record.marc.xml",
        mime="application/xml",
        use_container_width=True
    )

# OCR text + Debug
st.markdown("---")
with st.expander("🧾 نص OCR (للمراجعة)", expanded=False):
    st.text_area("OCR Text", value=ocr_text, height=260)

if show_debug:
    st.markdown("---")
    st.markdown("## 🧪 Debug")
    st.json({
        "edited_entity": asdict(edited_entity),
        "subjects": [asdict(s) for s in subjects],
        "classifications": [asdict(c) for c in classifs],
        "images_count": len(images),
    }, expanded=False)
