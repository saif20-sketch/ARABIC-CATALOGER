import streamlit as st
import json
import os
import requests
import re
import time
from datetime import datetime
from ddgs import DDGS
import isbnlib
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from huggingface_hub import InferenceClient

load_dotenv()

# استيراد الملفات المحلية
try:
    from nlm_classifier import AdvancedNLMClassifier
    from metadata_fetcher import EnhancedMetadataFetcher
    from cover_fetcher import EnhancedCoverFetcher
    from marc_generator import (
        build_marc_record,
        generate_marc_iso2709,
        generate_marcxml
    )
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    # واجهات افتراضية في حال فشل التحميل
    class AdvancedNLMClassifier:
        def classify_with_confidence(self, title, summary="", categories=None):
            return {'nlm_code': 'W 1', 'confidence_level': 'Low'}
    class EnhancedMetadataFetcher:
        def fetch_metadata(self, isbn):
            return {'title': 'Unknown', 'published_date': '', 'publisher': ''}
    class EnhancedCoverFetcher:
        def get_cover(self, isbn, title=None):
            return {'url': f"https://placehold.co/400x600?text=ISBN:{isbn}", 'status': 'fallback'}
    def build_marc_record(data, isbn):
        return ["001 ## $a ISBN" + isbn]
    def generate_marc_iso2709(marc_fields, isbn):
        return {'iso2709': '', 'human_readable': '', 'fields_count': 0, 'record_length': 0}
    def generate_marcxml(marc_fields, isbn):
        return "<?xml version='1.0'?>"

# --- 1. SETUP & AUTHENTICATION ---
hf_token = os.getenv("HF_TOKEN")
USE_AI = os.getenv("USE_AI", "true").lower() == "true"

st.set_page_config(
    page_title="Medical AI Librarian",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="collapsed"
)

# تهيئة عميل Hugging Face بنموذج مجاني
if hf_token and USE_AI:
    try:
        client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=hf_token)
        st.sidebar.success("✅ تم الاتصال بخدمة الذكاء الاصطناعي بنجاح.")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Hugging Face client error: {str(e)}. باستخدام التصنيف المحلي فقط.")
        client = None
else:
    if not hf_token:
        st.sidebar.info("🔑 لم يتم العثور على HF_TOKEN. يعمل النظام بالتصنيف المحلي فقط.")
    client = None

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Source+Serif+Pro:wght@400;600&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
    .modern-card { 
        background: rgba(255, 255, 255, 0.95); 
        backdrop-filter: blur(10px); 
        border-radius: 20px; 
        padding: 25px; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); 
        border: 1px solid rgba(255, 255, 255, 0.2); 
        margin-bottom: 20px; 
        transition: all 0.3s ease; 
    }
    .modern-card:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.12); 
    }
    .main-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 40px; 
        border-radius: 20px; 
        color: white; 
        margin-bottom: 30px; 
        text-align: center; 
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3); 
    }
    .main-title { 
        font-size: 2.8rem; 
        font-weight: 800; 
        margin-bottom: 10px; 
        letter-spacing: -0.5px; 
    }
    .main-subtitle { 
        font-size: 1.1rem; 
        opacity: 0.9; 
        font-weight: 300; 
    }
    .status-pill { 
        display: inline-block; 
        padding: 6px 16px; 
        border-radius: 50px; 
        font-size: 0.85rem; 
        font-weight: 600; 
        margin-right: 10px; 
        margin-bottom: 10px; 
    }
    .status-high { 
        background: linear-gradient(135deg, #34D399, #10B981); 
        color: white; 
    }
    .status-medium { 
        background: linear-gradient(135deg, #FBBF24, #F59E0B); 
        color: white; 
    }
    .status-low { 
        background: linear-gradient(135deg, #F87171, #EF4444); 
        color: white; 
    }
    .tag { 
        display: inline-block; 
        background: linear-gradient(135deg, #E0E7FF, #C7D2FE); 
        color: #3730A3; 
        padding: 6px 12px; 
        border-radius: 20px; 
        font-size: 0.85rem; 
        font-weight: 500; 
        margin: 5px 5px 5px 0; 
    }
    .metric-value { 
        font-size: 2.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #667eea, #764ba2); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin-bottom: 5px; 
    }
    .metric-label { 
        font-size: 0.9rem; 
        color: #666; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }
    .footer { 
        text-align: center; 
        margin-top: 50px; 
        padding: 20px; 
        color: #666; 
        font-size: 0.9rem; 
        border-top: 1px solid rgba(0, 0, 0, 0.1); 
    }
    .nlm-code { 
        font-family: 'Courier New', monospace; 
        font-size: 1.2rem; 
        font-weight: bold; 
        color: #2563eb; 
        background: #f0f9ff; 
        padding: 10px 15px; 
        border-radius: 8px; 
        border-left: 4px solid #2563eb; 
    }
    .confidence-high { color: #059669; font-weight: 600; }
    .confidence-medium { color: #d97706; font-weight: 600; }
    .confidence-low { color: #dc2626; font-weight: 600; }
    .book-cover-container {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    .book-cover-container:hover {
        transform: scale(1.02);
    }
    .source-badge {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS ---

def clean_isbn(isbn_str):
    """تنظيف وتصحيح ISBN"""
    cleaned = re.sub(r'[^0-9X]', '', isbn_str.upper())
    try:
        if len(cleaned) == 10:
            if not isbnlib.is_isbn10(cleaned):
                return None
        elif len(cleaned) == 13:
            if not isbnlib.is_isbn13(cleaned):
                return None
        else:
            return None
    except:
        pass
    return cleaned

def search_web_context(isbn, title=None):
    """بحث في الويب باستخدام ddgs"""
    queries = []
    if title:
        queries.extend([
            f"{title} medical book publication date edition",
            f"{title} review summary table of contents",
            f"{title} medical textbook target audience"
        ])
    queries.extend([
        f"ISBN {isbn} publication details",
        f"{isbn} medical book specifications",
        f"medical library catalog {isbn}"
    ])
    all_results = []
    try:
        with DDGS() as ddgs:
            for query in queries[:4]:
                results = list(ddgs.text(query, max_results=3))
                for result in results:
                    all_results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('body', ''),
                        'url': result.get('href', '')
                    })
    except Exception as e:
        st.sidebar.warning(f"Web search limited: {str(e)}")
    return all_results if all_results else []

def enhanced_ai_librarian_analysis(isbn, meta_data, web_context):
    """تحليل محسن مع دقة عالية"""
    if not client or not USE_AI:
        st.info("ℹ️ يعمل النظام حاليًا بوضع **التصنيف المحلي المتقدم** (بدون ذكاء اصطناعي). تتوفر جميع البيانات الأساسية.")
        return fallback_local_classification(isbn, meta_data, web_context)
    
    metadata_fetcher = EnhancedMetadataFetcher()
    enhanced_meta = metadata_fetcher.fetch_metadata(isbn)
    
    api_title = enhanced_meta.get('title', '')
    summary_context = enhanced_meta.get('description', '')
    categories = enhanced_meta.get('categories', [])
    web_context_text = " ".join([r.get('snippet', '') for r in web_context[:3]])
    
    nlm_classifier = AdvancedNLMClassifier()
    nlm_result = nlm_classifier.classify_with_confidence(
        api_title, 
        f"{summary_context} {web_context_text}",
        categories
    )
    
    system_prompt = """You are a Senior Medical Cataloging Expert with specialization in NLM classification.

IMPORTANT GUIDELINES:
1. Analyze the book's PRIMARY subject focus, not secondary topics
2. Consider the intended audience and purpose
3. For medical textbooks, use W 18-W 20 range
4. For clinical guides, use appropriate WB-WZ codes
5. For basic sciences, use QS-QZ series
6. Provide specific, not generic, classifications
7. Include detailed reasoning for your choice

ALWAYS verify the classification matches the book's main content."""

    user_prompt = f"""Please provide precise cataloging information for this medical book:

ISBN: {isbn}
Title: {api_title}
Publication Year: {enhanced_meta.get('published_date', 'Unknown')}
Publisher: {enhanced_meta.get('publisher', 'Unknown')}
Subjects/Categories: {', '.join(categories) if categories else 'None'}
Description: {summary_context[:300]}
Additional Context: {web_context_text[:300]}

NLM Classification Analysis from our system:
- Suggested Code: {nlm_result['nlm_code']}
- Confidence: {nlm_result['confidence_level']}
- Reason: {nlm_result['confidence_reason']}

Please provide your professional assessment in this JSON format:

{{
    "title": "Complete title",
    "sub_title": "Subtitle if available",
    "authors": ["Author list"],
    "edition": "Edition information",
    "publisher": "Publisher name",
    "pub_year": "YYYY (extracted accurately)",
    "pages": "Number of pages",
    "isbn_10": "ISBN-10",
    "isbn_13": "ISBN-13",
    "summary": "Comprehensive 200-word summary",
    "contents_note": "Detailed table of contents",
    "audience_category": "Specific audience description",
    "audience_reason": "Justification",
    "mesh_subjects": ["Relevant MeSH terms"],
    "nlm_class": "YOUR PROFESSIONAL NLM CLASSIFICATION",
    "nlm_class_reason": "Detailed reasoning based on content analysis",
    "nlm_class_confidence": "High/Medium/Low",
    "acquisition_decision": "Highly Recommended/Recommended/Optional/Not Recommended",
    "acquisition_reason": "Collection development reasoning",
    "quality_score": "1-10 based on authority and relevance",
    "data_accuracy": "High/Medium/Low based on available information"
}}

CRITICAL: The NLM classification must be accurate and specific to the main subject."""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = client.chat_completion(
            messages,
            max_tokens=2500,
            temperature=0.1,
            top_p=0.9
        )
        content = response.choices[0].message.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        
        # دمج نتائج NLM المحلية
        data['nlm_class'] = nlm_result['nlm_code']
        data['nlm_class_ai_reason'] = data.get('nlm_class_reason', '')
        data['nlm_class_local_reason'] = nlm_result['confidence_reason']
        data['nlm_class_confidence'] = nlm_result['confidence_level']
        data['nlm_class_score'] = nlm_result['confidence_score']
        data['nlm_alternatives'] = nlm_result.get('alternative_codes', [])
        data['metadata_source'] = enhanced_meta.get('source', 'Multiple')
        data['metadata_confidence'] = enhanced_meta.get('confidence', 'Unknown')
        
        if enhanced_meta.get('published_date'):
            data['pub_year'] = enhanced_meta['published_date']
            data['pub_year_source'] = enhanced_meta.get('source', 'API')
            data['pub_year_confidence'] = enhanced_meta.get('confidence', 'Unknown')
        
        if not isinstance(data.get('authors'), list):
            if enhanced_meta and enhanced_meta.get('authors'):
                data['authors'] = enhanced_meta['authors']
            else:
                data['authors'] = []
        
        data['illustrations_note'] = 'illustrations (chiefly color), portraits'
        data['series'] = 'Medical education series' if 'textbook' in data.get('title', '').lower() else ''
        data['institution'] = enhanced_meta.get('institution', '')
        
        if not data.get('pages') and enhanced_meta.get('page_count'):
            page_count = enhanced_meta['page_count']
            if isinstance(page_count, int):
                if page_count > 100:
                    data['pages'] = f"xvi, {page_count}"
                else:
                    data['pages'] = str(page_count)
        
        return data
        
    except HTTPError as e:
        if e.response.status_code == 402:
            st.warning("⚠️ خدمة الذكاء الاصطناعي تحتاج إلى اشتراك مدفوع. يتم استخدام التصنيف المحلي بدلاً من ذلك.")
        else:
            st.error(f"❌ خطأ في خدمة الذكاء الاصطناعي: {e}")
        return fallback_local_classification(isbn, enhanced_meta, web_context)
    except Exception as e:
        st.error(f"❌ خطأ غير متوقع في تحليل الذكاء الاصطناعي: {str(e)}")
        return fallback_local_classification(isbn, enhanced_meta, web_context)

def fallback_local_classification(isbn, enhanced_meta, web_context):
    """تصنيف محلي متقدم مع بيانات افتراضية ذكية"""
    nlm_classifier = AdvancedNLMClassifier()
    nlm_result = nlm_classifier.classify_with_confidence(
        enhanced_meta.get('title', ''), 
        enhanced_meta.get('description', ''),
        enhanced_meta.get('categories', [])
    )
    
    title = enhanced_meta.get('title', 'Unknown Title')
    description = enhanced_meta.get('description', '')
    authors = enhanced_meta.get('authors', [])
    publisher = enhanced_meta.get('publisher', 'Unknown')
    pub_year = enhanced_meta.get('published_date', '')
    
    # توليد ملخص ذكي
    if description and len(description) > 20:
        summary = description[:500] + ('...' if len(description) > 500 else '')
    else:
        summary = f"This book, '{title}', is a medical publication focusing on {nlm_result['nlm_name']}. " \
                  f"It is intended for healthcare professionals and students. " \
                  f"Published by {publisher} in {pub_year if pub_year else 'unknown year'}. " \
                  f"The work covers key concepts in {nlm_result['nlm_description'].lower() if nlm_result['nlm_description'] else 'medicine'}."
    
    # توليد محتويات افتراضية بناءً على التصنيف
    main_topic = nlm_result.get('nlm_name', 'Medicine')
    contents_templates = {
        'Textbook': [
            "1. Introduction to the field",
            "2. Fundamental principles",
            "3. Clinical applications",
            "4. Diagnostic approaches",
            "5. Therapeutic interventions",
            "6. Case studies",
            "7. Emerging trends",
            "8. Review questions"
        ],
        'Surgery': [
            "1. Preoperative assessment",
            "2. Surgical anatomy",
            "3. Operative techniques",
            "4. Postoperative care",
            "5. Complications and management",
            "6. Minimally invasive surgery",
            "7. Surgical outcomes"
        ],
        'Cardiology': [
            "1. Cardiac anatomy and physiology",
            "2. Diagnostic imaging",
            "3. Ischemic heart disease",
            "4. Heart failure",
            "5. Arrhythmias",
            "6. Valvular disorders",
            "7. Pharmacotherapy",
            "8. Interventional cardiology"
        ],
        'Neurology': [
            "1. Neuroanatomy",
            "2. Neurological examination",
            "3. Stroke and cerebrovascular disease",
            "4. Epilepsy",
            "5. Neurodegenerative disorders",
            "6. Headache and pain",
            "7. Neuromuscular disorders"
        ],
        'Pediatrics': [
            "1. Growth and development",
            "2. Neonatal care",
            "3. Pediatric infectious diseases",
            "4. Childhood immunizations",
            "5. Pediatric emergencies",
            "6. Adolescent medicine"
        ]
    }
    
    contents_note = []
    for key, template in contents_templates.items():
        if key.lower() in main_topic.lower():
            contents_note = template
            break
    if not contents_note:
        contents_note = [
            "1. Introduction",
            "2. Core concepts",
            "3. Clinical relevance",
            "4. Diagnostic methods",
            "5. Treatment strategies",
            "6. Patient management",
            "7. Future directions",
            "8. Review and self-assessment"
        ]
    
    # توليد موضوعات MeSH افتراضية
    mesh_mapping = {
        'W 18': ['Education, Medical', 'Textbooks as Topic', 'Curriculum'],
        'WB 100': ['Clinical Medicine', 'Diagnosis', 'Therapeutics'],
        'WB 105': ['Emergency Medicine', 'Traumatology', 'Critical Care'],
        'WO 100': ['General Surgery', 'Surgical Procedures, Operative'],
        'WS 1': ['Pediatrics', 'Child Development', 'Adolescent Medicine'],
        'WG': ['Cardiology', 'Cardiovascular Diseases', 'Heart Diseases'],
        'WL': ['Neurology', 'Nervous System Diseases', 'Brain'],
        'QS 1': ['Anatomy', 'Dissection', 'Embryology'],
        'QV 1': ['Pharmacology', 'Pharmaceutical Preparations', 'Drug Therapy'],
        'QZ 4': ['Pathology', 'Disease', 'Clinical Pathology'],
        'WY 100': ['Nursing Care', 'Nursing Process', 'Clinical Nursing Research'],
        'WA 1': ['Public Health', 'Preventive Medicine', 'Epidemiology'],
        'WM 1': ['Psychiatry', 'Mental Disorders', 'Psychotherapy']
    }
    
    nlm_code = nlm_result['nlm_code']
    mesh_subjects = []
    for code_prefix, subjects in mesh_mapping.items():
        if nlm_code.startswith(code_prefix) or code_prefix in nlm_code:
            mesh_subjects = subjects
            break
    if not mesh_subjects:
        mesh_subjects = ['Medicine', 'Medical Sciences', 'Health Occupations']
    
    # تحديد الجمهور المستهدف
    audience_category = "Medical Students and Healthcare Professionals"
    audience_reason = "Based on medical content and typical audience for this subject area."
    if 'Textbook' in nlm_result.get('nlm_name', ''):
        audience_category = "Medical Students (Undergraduate)"
        audience_reason = "Introductory textbook format indicates undergraduate medical education."
    elif 'Education' in nlm_result.get('nlm_name', ''):
        audience_category = "Medical Educators and Students"
        audience_reason = "Focus on educational methods and curriculum."
    elif 'Surgery' in nlm_result.get('nlm_name', ''):
        audience_category = "Surgical Residents and Practicing Surgeons"
        audience_reason = "Specialized surgical content for advanced trainees and clinicians."
    
    # قرار الشراء
    score = nlm_result['confidence_score']
    if score >= 8:
        acquisition_decision = "Highly Recommended"
        acquisition_reason = "Strong alignment with collection development policy and high relevance."
    elif score >= 4:
        acquisition_decision = "Recommended"
        acquisition_reason = "Good fit for the collection; moderate relevance."
    else:
        acquisition_decision = "Review Required"
        acquisition_reason = "Limited information; further evaluation recommended."
    
    return {
        'title': title,
        'sub_title': '',
        'authors': authors,
        'edition': enhanced_meta.get('edition', ''),
        'publisher': publisher,
        'pub_year': pub_year,
        'pages': enhanced_meta.get('page_count', 'xii, 500'),
        'isbn_10': enhanced_meta.get('isbn_10', ''),
        'isbn_13': enhanced_meta.get('isbn_13', isbn),
        'summary': summary,
        'contents_note': contents_note,
        'audience_category': audience_category,
        'audience_reason': audience_reason,
        'mesh_subjects': mesh_subjects,
        'nlm_class': nlm_code,
        'nlm_class_reason': f"Local classification: {nlm_result['confidence_reason']}",
        'nlm_class_confidence': nlm_result['confidence_level'],
        'nlm_class_score': score,
        'acquisition_decision': acquisition_decision,
        'acquisition_reason': acquisition_reason,
        'quality_score': score // 2 if score > 0 else 5,
        'data_accuracy': 'Medium',
        'illustrations_note': 'illustrations',
        'metadata_source': enhanced_meta.get('source', 'Local'),
        'metadata_confidence': enhanced_meta.get('confidence', 'Medium')
    }

# --- 4. MAIN UI ---
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">🏥 Medical AI Librarian</div>
    <div class="main-subtitle">Enhanced Cataloging • Accurate NLM Classification • Multi-Source Data</div>
</div>
""", unsafe_allow_html=True)

# --- MAIN INPUT AREA ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("### 📚 Enter ISBN for Analysis")
    isbn_input = st.text_input(
        label="ISBN",
        placeholder="Enter 10 or 13 digit ISBN (e.g., 9780323083737)",
        label_visibility="collapsed",
        key="isbn_input"
    )
with col2:
    st.markdown("### &nbsp;")
    analyze_btn = st.button(
        "🔍 Analyze Book",
        width='stretch',
        type="primary",
        key="analyze_btn"
    )
with col3:
    st.markdown("### &nbsp;")
    if st.button(
        "📊 View Statistics", 
        width='stretch',
        key="stats_btn"
    ):
        st.switch_page("pages/statistics.py")

# --- PROCESSING ---
if analyze_btn and isbn_input:
    isbn_clean = clean_isbn(isbn_input)
    if not isbn_clean:
        st.error("❌ Invalid ISBN format. Please enter a valid 10 or 13 digit ISBN.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        with st.spinner("🔄 Initializing enhanced analysis..."):
            status_text.text("📥 Fetching enhanced metadata...")
            metadata_fetcher = EnhancedMetadataFetcher()
            metadata = metadata_fetcher.fetch_metadata(isbn_clean)
            progress_bar.progress(25)
            time.sleep(0.5)
            
            status_text.text("🖼️ Retrieving book cover from multiple sources...")
            cover_fetcher = EnhancedCoverFetcher()
            cover_result = cover_fetcher.get_cover(isbn_clean, metadata.get('title'))
            progress_bar.progress(40)
            time.sleep(0.5)
            
            status_text.text("🌐 Searching for additional context...")
            web_context = search_web_context(isbn_clean, metadata.get('title'))
            progress_bar.progress(60)
            time.sleep(0.5)
            
            status_text.text("🧠 Enhanced AI analysis with NLM classification...")
            ai_result = enhanced_ai_librarian_analysis(isbn_clean, metadata, web_context)
            progress_bar.progress(85)
            time.sleep(0.5)
            
            if ai_result:
                st.session_state.analysis_data = {
                    'metadata': metadata,
                    'cover_result': cover_result,
                    'web_context': web_context,
                    'ai_analysis': ai_result,
                    'isbn': isbn_clean,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.search_history.append({
                    'isbn': isbn_clean,
                    'title': ai_result.get('title', 'Unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'nlm_class': ai_result.get('nlm_class', '')
                })
                progress_bar.progress(100)
                status_text.text("✅ Enhanced analysis complete!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Analysis failed. Please try again.")
                progress_bar.empty()
                status_text.empty()

# --- DISPLAY RESULTS ---
if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    if 'progress_bar' in locals():
        progress_bar.empty()
        status_text.empty()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Overview", "🔍 Details", "🏷️ Cataloging", "📊 AI Insights"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown('<div class="book-cover-container">', unsafe_allow_html=True)
            # ✅ استخدام width='stretch' بدلاً من use_container_width=True
            st.image(data['cover_result']['url'], width='stretch')
            st.markdown('</div>', unsafe_allow_html=True)
            if data['cover_result'].get('source'):
                st.caption(f"Cover source: {data['cover_result']['source']}")
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Quick Stats")
            cols = st.columns(3)
            with cols[0]:
                authors_count = len(data['ai_analysis'].get('authors', []))
                st.markdown(f'<div class="metric-value">{authors_count}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Authors</div>', unsafe_allow_html=True)
            with cols[1]:
                quality = data['ai_analysis'].get('quality_score', 5)
                st.markdown(f'<div class="metric-value">{quality}/10</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Quality</div>', unsafe_allow_html=True)
            with cols[2]:
                year = data['ai_analysis'].get('pub_year', 'N/A')
                st.markdown(f'<div class="metric-value">{year}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Year</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            ai = data['ai_analysis']
            st.markdown(f"# {ai.get('title', 'Unknown Title')}")
            if ai.get('sub_title'):
                st.markdown(f"### *{ai['sub_title']}*")
            authors = ai.get('authors', [])
            if authors:
                st.markdown(f"**👥 Authors:** {', '.join(authors)}")
            pub_info = []
            if ai.get('publisher'):
                pub_info.append(ai['publisher'])
            if ai.get('pub_year'):
                pub_info.append(ai['pub_year'])
                if ai.get('pub_year_source'):
                    pub_info.append(f"({ai['pub_year_source']})")
            if ai.get('edition'):
                pub_info.append(ai['edition'])
            if pub_info:
                st.markdown(f"**🏢 Publisher:** {' • '.join(pub_info)}")
            isbns = []
            if ai.get('isbn_13'):
                isbns.append(f"ISBN-13: `{ai['isbn_13']}`")
            if ai.get('isbn_10'):
                isbns.append(f"ISBN-10: `{ai['isbn_10']}`")
            if isbns:
                st.markdown(f"**📋 Identifiers:** {' | '.join(isbns)}")
            st.markdown("---")
            decision = ai.get('acquisition_decision', 'Optional')
            if "Highly" in decision:
                pill_class = "status-high"
            elif "Not" in decision:
                pill_class = "status-low"
            else:
                pill_class = "status-medium"
            st.markdown(f"### 📋 Acquisition Decision")
            st.markdown(f'<div class="{pill_class} status-pill">{decision}</div>', unsafe_allow_html=True)
            st.caption(ai.get('acquisition_reason', ''))
            st.markdown("### 🎯 Target Audience")
            audience = ai.get('audience_category', 'Not specified')
            st.markdown(f'<div class="tag">{audience}</div>', unsafe_allow_html=True)
            st.caption(ai.get('audience_reason', ''))
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 📝 Summary")
            st.write(ai.get('summary', 'No summary available.'))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 📑 Table of Contents")
            contents = ai.get('contents_note', 'Not available.')
            if isinstance(contents, list):
                for item in contents:
                    st.write(f"• {item}")
            else:
                st.write(contents)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 🏷️ MeSH Subjects")
            mesh_terms = ai.get('mesh_subjects', [])
            if mesh_terms:
                for term in mesh_terms[:8]:
                    st.markdown(f'<div class="tag">{term}</div>', unsafe_allow_html=True)
            else:
                st.write("No MeSH terms identified.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 📚 NLM Classification (060)")
            nlm_code = ai.get('nlm_class', 'W 1')
            st.markdown(f'<div class="nlm-code">{nlm_code}</div>', unsafe_allow_html=True)
            confidence = ai.get('nlm_class_confidence', 'Medium')
            if confidence == 'High':
                st.success(f"✅ Confidence: {confidence} (Score: {ai.get('nlm_class_score', 0)})")
            elif confidence == 'Medium':
                st.warning(f"⚠️ Confidence: {confidence} (Score: {ai.get('nlm_class_score', 0)})")
            else:
                st.error(f"❌ Confidence: {confidence} (Score: {ai.get('nlm_class_score', 0)})")
            if ai.get('nlm_class_explanation'):
                st.info(f"💡 {ai['nlm_class_explanation']}")
            if ai.get('nlm_class_reason'):
                with st.expander("📖 Classification Reasoning"):
                    st.write(ai['nlm_class_reason'])
            if ai.get('nlm_alternatives'):
                with st.expander("🔀 Alternative Classifications"):
                    for alt in ai['nlm_alternatives'][:3]:
                        st.code(alt, language="text")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("### 💻 MARC21 Record - Complete Edition")
        marc_lines = build_marc_record(ai, data['isbn'])
        marc_text = "\n".join(marc_lines)
        iso_record = generate_marc_iso2709(marc_lines, data['isbn'])
        col1, col2 = st.columns(2)
        with col1:
            # ✅ استخدام language="text" بدلاً من "marc"
            st.code(marc_text, language="text")
        with col2:
            st.code(iso_record['iso2709'], language="text")
            st.caption(f"ISO 2709 Record - {iso_record['record_length']} bytes")
        marcxml_text = generate_marcxml(marc_lines, data['isbn'])
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button(
                label="📥 MARC21 (.mrc)",
                data=marc_text,
                file_name=f"{data['isbn']}.mrc",
                mime="text/plain",
                width='stretch'
            )
        with col2:
            st.download_button(
                label="📊 ISO 2709 (.iso)",
                data=iso_record['iso2709'].encode('utf-8'),
                file_name=f"{data['isbn']}_iso2709.iso",
                mime="application/octet-stream",
                width='stretch'
            )
        with col3:
            st.download_button(
                label="📋 JSON Metadata",
                data=json.dumps(data, indent=2, ensure_ascii=False),
                file_name=f"{data['isbn']}_complete.json",
                mime="application/json",
                width='stretch'
            )
        with col4:
            st.download_button(
                label="📑 XML/MARCXML",
                data=marcxml_text,
                file_name=f"{data['isbn']}.xml",
                mime="application/xml",
                width='stretch'
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 🤖 AI Analysis Details")
            st.metric("Confidence Level", ai.get('confidence_level', 'Medium'))
            st.metric("Quality Score", ai.get('quality_score', 'N/A'))
            st.metric("Data Sources", len(data['web_context']) + (1 if data['metadata'] else 0))
            if ai.get('metadata_source'):
                st.caption(f"Metadata source: {ai['metadata_source']} ({ai.get('metadata_confidence', 'Unknown')})")
            st.markdown("---")
            st.markdown("#### NLM Classification Analysis")
            classifier = AdvancedNLMClassifier()
            nlm_analysis = classifier.classify_with_confidence(
                ai.get('title', ''), 
                ai.get('summary', '')
            )
            st.metric("Classification Confidence", nlm_analysis['confidence_level'])
            st.caption(f"Code: {nlm_analysis['nlm_code']}")
            st.caption(f"Reason: {nlm_analysis['confidence_reason']}")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 🔍 Web Context Sources")
            if data['web_context']:
                for i, source in enumerate(data['web_context'][:3], 1):
                    with st.expander(f"Source {i}: {source.get('title', 'Unknown')}"):
                        st.write(source.get('snippet', 'No content available'))
                        if source.get('url'):
                            st.caption(f"URL: {source['url']}")
            else:
                st.info("No web context available.")
            st.markdown('</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔍 Recent Searches")
    if st.session_state.search_history:
        for item in reversed(st.session_state.search_history[-5:]):
            st.caption(f"• {item['isbn']} - {item['title'][:30]}...")
            if item.get('nlm_class'):
                st.caption(f"  NLM: `{item['nlm_class']}`")
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    if st.button("🔄 Clear History", key="clear_btn"):
        st.session_state.search_history = []
        st.session_state.analysis_data = None
        st.rerun()
    st.markdown("---")
    st.markdown("### 📊 NLM Quick Guide")
    with st.expander("Common NLM Classifications"):
        st.markdown("""
        **Medical Textbooks:** W 18-20
        **Clinical Medicine:** WB-WZ series
        **Basic Sciences:** QS-QZ series
        **Health Professions:** WY, WA, WM
        **Common Examples:**
        - Anatomy: QS 1
        - Pharmacology: QV 1
        - Surgery: WO 100
        - Pediatrics: WS 1
        - Radiology: WN 1
        """)
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Total Analyses", len(st.session_state.search_history))
    if st.session_state.analysis_data:
        st.metric("Current ISBN", st.session_state.analysis_data['isbn'])
    else:
        st.metric("Current ISBN", "None")

# --- FOOTER ---
st.markdown("""
<div class="footer">
    <p>Medical AI Librarian v3.0 • Enhanced Accuracy • Multi-Source Data</p>
    <p>Powered by Hugging Face & Streamlit • Transforming Medical Library Management</p>
</div>
""", unsafe_allow_html=True)