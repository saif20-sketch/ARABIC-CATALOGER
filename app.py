import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from PIL import Image

# استيراد الوظائف المحلية
from marc_generator import build_marc_record, generate_marc_iso2709
from nlm_classifier import AdvancedNLMClassifier

load_dotenv()

# إعداد Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="المفهرس العربي الذكي", layout="wide")

def analyze_with_gemini(images):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    أنت خبير فهرسة مكتبات محترف. حلل الصور المرفقة لكتاب (غلاف، صفحة عنوان، محتويات) واستخرج البيانات التالية باللغة العربية:
    1. العنوان الرئيسي والفرعي.
    2. المؤلفون والمسؤولية.
    3. بيانات النشر (المدينة، الناشر، سنة النشر).
    4. الترقيم الدولي (ISBN).
    5. ملخص محتوى الكتاب (لتحديد التصنيف الطبي).
    6. عدد الصفحات (إن وجد).
    
    أعطني النتيجة بتنسيق JSON حصراً كالتالي:
    {
        "title": "", "authors": [], "publisher": "", "pub_location": "", 
        "pub_year": "", "isbn": "", "description": "", "pages": ""
    }
    """
    
    content = [prompt]
    for img in images:
        content.append(Image.open(img))
    
    response = model.generate_content(content)
    # تنظيف المخرجات للحصول على JSON فقط
    json_str = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(json_str)

st.title("🏥 نظام الفهرسة العربي الذكي (MARC21 + NLM)")
st.info("ارفع صور بيانات الكتاب (الغلاف، صفحة العنوان، قائمة المحتويات) ليقوم الذكاء الاصطناعي بفهرستها.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_files = st.file_uploader("اختر صور الكتاب...", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    if uploaded_files and st.button("🚀 بدء التحليل والفهرسة"):
        try:
            with st.spinner("جاري قراءة الصور وتحليل النصوص العربية..."):
                book_data = analyze_with_gemini(uploaded_files)
                st.session_state.book_data = book_data
                
                # التصنيف التلقائي NLM
                classifier = AdvancedNLMClassifier()
                nlm_info = classifier.classify_with_confidence(book_data['title'], book_data['description'])
                st.session_state.nlm_info = nlm_info
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحليل: {e}")

with col2:
    if 'book_data' in st.session_state:
        data = st.session_state.book_data
        st.success("✅ تم استخراج البيانات بنجاح")
        st.write(f"**العنوان:** {data['title']}")
        st.write(f"**المؤلف:** {', '.join(data['authors'])}")
        st.write(f"**التصنيف المقترح (NLM):** {st.session_state.nlm_info['nlm_code']}")
        
        # توليد MARC21
        marc_fields = build_marc_record(data, data['isbn'])
        iso_data = generate_marc_iso2709(marc_fields, data['isbn'])
        
        st.download_button("تحميل سجل MARC (ISO 2709)", iso_data['iso2709'], file_name="record.mrc")
