import streamlit as st
import os
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# استيراد المحركات المحدثة
from marc_generator import build_rda_marc_record, generate_marc_iso2709
from lcc_classifier import LCCClassifier

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="المفهرس العربي الاحترافي | RDA & LCC", layout="wide")

def analyze_arabic_book(images):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # البرومبت هنا مصمم لاستخراج بيانات متوافقة مع معايير RDA و LCC
    prompt = """
    قم بتحليل صور الكتاب العربي بدقة لاستخراج بيانات ببليوغرافية متوافقة مع معايير RDA ومارك 21:
    1. العنوان والمسؤولية (245): استخرج العنوان كاملاً والمؤلفين والمترجمين.
    2. بيانات النشر (264): المدينة، الناشر، السنة (استخدم معيار RDA: لا تستخدم اختصارات مثل د.ن).
    3. الوصف المادي (300): قدر عدد الصفحات ووجود رسوم توضيحية.
    4. رؤوس الموضوعات (650): حدد موضوعات الكتاب بناءً على قائمة رؤوس موضوعات مكتبة الكونجرس (LCSH).
    5. تصنيف مكتبة الكونجرس (LCC): اقترح رمز التصنيف (مثال: PJ7501).
    6. لغة المحتوى (041).

    أعطني النتيجة بتنسيق JSON:
    {
        "title_statement": "", "author_primary": "", "other_authors": [],
        "publication": {"place": "", "publisher": "", "year": ""},
        "physical_desc": {"pages": "", "illus": bool},
        "subjects": [], "lcc_suggested": "", "isbn": "", "language": "ara"
    }
    """
    content = [prompt]
    for img in images:
        content.append(Image.open(img))
    
    response = model.generate_content(content)
    return json.loads(response.text.replace('```json', '').replace('```', '').strip())

st.title("📚 المفهرس العربي الذكي (LCC + RDA + MARC21)")
st.markdown("---")

uploaded_files = st.file_uploader("ارفع صور الكتاب (الغلاف، صفحة العنوان، الفهرس)", type=['jpg', 'png'], accept_multiple_files=True)

if uploaded_files and st.button("🚀 فهرسة الكتاب"):
    with st.spinner("جاري التحليل وفق معايير RDA..."):
        book_data = analyze_arabic_book(uploaded_files)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 البيانات الوصفية المستخرجة")
            st.write(f"**العنوان:** {book_data['title_statement']}")
            st.write(f"**التصنيف (LCC):** {book_data['lcc_suggested']}")
            st.write(f"**الموضوعات:** {', '.join(book_data['subjects'])}")
        
        with col2:
            st.subheader("💾 ملفات الفهرسة")
            marc_fields = build_rda_marc_record(book_data)
            iso_data = generate_marc_iso2709(marc_fields)
            st.download_button("تحميل سجل MARC21 (ISO)", iso_data, file_name="record.mrc")
            st.text_area("معاينة حقول مارك", "\n".join(marc_fields), height=300)
