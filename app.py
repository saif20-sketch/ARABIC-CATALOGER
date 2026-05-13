import streamlit as st
import os
import json
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

# استيراد المحركات المحلية
from marc_generator import build_rda_marc_record, generate_marc_iso2709
from lcc_classifier import LCCClassifier

load_dotenv()

# إعداد Gemini 1.5 Flash (الموديل الأسرع)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="المفهرس العربي الذكي | سرعة فائقة", layout="wide")

# --- دالة تسريع المعالجة (ضغط الصور) ---
def prepare_image(uploaded_file):
    """تصغير حجم الصورة وضغطها لتقليل وقت الرفع والتحليل"""
    img = Image.open(uploaded_file)
    
    # تحويل لـ RGB إذا كانت الصورة بصيغة مختلفة لضمان التوافق
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # تصغير الأبعاد (1000px كافية جداً للذكاء الاصطناعي لقراءة النص العربي)
    img.thumbnail((1000, 1000))
    
    # حفظ في ذاكرة مؤقتة بجودة JPEG مضغوطة
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70) # جودة 70 توفر توازناً ممتازاً بين الحجم والوضوح
    return Image.open(buffer)

def analyze_arabic_book_fast(processed_images):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # برومبت مختصر جداً لتقليل وقت التوليد
    prompt = """
    Act as an Arabic RDA Cataloger. Analyze images and output ONLY JSON:
    {
        "title_statement": "Full Title",
        "author_primary": "Main Author",
        "publication": {"place": "City", "publisher": "Name", "year": "YYYY"},
        "physical_desc": {"pages": "Number", "illus": true/false},
        "subjects": ["Subject1", "Subject2"],
        "lcc_suggested": "LCC Code",
        "isbn": "ISBN",
        "language": "ara"
    }
    No talk, just JSON.
    """
    
    response = model.generate_content([prompt] + processed_images)
    # تنظيف الرد للحصول على JSON نقي
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json)

# --- واجهة المستخدم ---
st.title("📚 المفهرس العربي الذكي (نسخة الأداء السريع)")
st.markdown("تم تفعيل ضغط الصور التلقائي واستخدام موديل Gemini Flash للنتائج اللحظية.")

uploaded_files = st.file_uploader("ارفع صور الكتاب (أسرع من قبل!)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

if uploaded_files and st.button("🚀 بدء الفهرسة الفورية"):
    with st.spinner("جاري الضغط والتحليل..."):
        try:
            # الخطوة 1: تجهيز الصور بسرعة
            ready_images = [prepare_image(f) for f in uploaded_files]
            
            # الخطوة 2: التحليل عبر الذكاء الاصطناعي
            book_data = analyze_arabic_book_fast(ready_images)
            
            # عرض النتائج
            c1, c2 = st.columns(2)
            with c1:
                st.success("✅ اكتمل التحليل")
                st.json(book_data) # عرض البيانات المستخرجة
            
            with c2:
                st.subheader("🛠️ سجل MARC21")
                marc_fields = build_rda_marc_record(book_data)
                st.text_area("معاينة الحقول", "\n".join(marc_fields), height=250)
                
                iso_data = generate_marc_iso2709(marc_fields)
                st.download_button("تحميل سجل .mrc", iso_data, file_name="fast_record.mrc")
                
        except Exception as e:
            st.error(f"حدث خطأ في المعالجة: {e}")
