import re
from typing import Dict, List, Optional

class AdvancedNLMClassifier:
    """نظام تصنيف NLM متقدم مع قاعدة بيانات كاملة وتحليل ذكي"""
    
    def __init__(self):
        self.load_nlm_database()
        self.initialize_keyword_database()
    
    def load_nlm_database(self):
        self.nlm_database = {
            'W 1': {'name': 'Reference Works', 'keywords': ['reference', 'handbook', 'manual', 'guide', 'encyclopedia', 'directory', 'bibliography', 'index', 'catalog'], 'description': 'General medical reference works'},
            'W 13': {'name': 'Dictionaries', 'keywords': ['dictionary', 'lexicon', 'terminology', 'nomenclature', 'vocabulary', 'glossary'], 'description': 'Medical dictionaries and terminology'},
            'W 15': {'name': 'Nomenclature', 'keywords': ['nomenclature', 'classification', 'taxonomy', 'coding', 'system', 'standardization'], 'description': 'Classification systems and nomenclature'},
            'W 18': {'name': 'Medical Education', 'keywords': ['textbook', 'student', 'education', 'learning', 'curriculum', 'teaching', 'instruction', 'course', 'study guide', 'exam'], 'description': 'Medical textbooks and teaching materials'},
            'W 20': {'name': 'Research', 'keywords': ['research', 'methodology', 'statistics', 'study design', 'investigation', 'scientific method', 'evidence'], 'description': 'Medical research methodology'},
            'W 20.5': {'name': 'Research Methodology', 'keywords': ['methodology', 'methods', 'techniques', 'protocol', 'experimental', 'clinical trial', 'study protocol'], 'description': 'Specific research methods and techniques'},
            'WB 100': {'name': 'Practice of Medicine', 'keywords': ['practice', 'clinical', 'diagnosis', 'treatment', 'therapy', 'management', 'care', 'clinical practice'], 'description': 'General clinical medicine'},
            'WB 105': {'name': 'Emergency Medicine', 'keywords': ['emergency', 'trauma', 'critical care', 'urgent', 'ER', 'emergency room', 'acute care'], 'description': 'Emergency and trauma medicine'},
            'WB 110': {'name': 'Family Medicine', 'keywords': ['family', 'primary care', 'general practice', 'community medicine', 'family practice'], 'description': 'Family and primary care medicine'},
            'WB 115': {'name': 'Diagnosis', 'keywords': ['diagnosis', 'diagnostic', 'assessment', 'evaluation', 'examination', 'clinical diagnosis'], 'description': 'Clinical diagnosis methods'},
            'WO 100': {'name': 'Surgery', 'keywords': ['surgery', 'surgical', 'operation', 'operative', 'procedure', 'surgical technique', 'operation'], 'description': 'General surgery'},
            'WO 162': {'name': 'Surgical Anatomy', 'keywords': ['surgical anatomy', 'operative anatomy', 'surgical landmarks', 'anatomical approach'], 'description': 'Anatomy for surgeons'},
            'WO 200': {'name': 'Anesthesiology', 'keywords': ['anesthesia', 'anesthesiology', 'pain management', 'analgesia', 'anesthetic', 'perioperative'], 'description': 'Anesthesia and pain management'},
            'WS 1': {'name': 'Pediatrics', 'keywords': ['pediatrics', 'pediatric', 'children', 'child', 'infant', 'neonate', 'adolescent', 'childhood'], 'description': 'General pediatrics'},
            'WS 200': {'name': 'Neonatology', 'keywords': ['neonatology', 'newborn', 'neonate', 'premature', 'perinatal', 'neonatal intensive care'], 'description': 'Newborn medicine'},
            'WG': {'name': 'Cardiology', 'keywords': ['cardiology', 'cardiac', 'heart', 'cardiovascular', 'ECG', 'echocardiography', 'heart disease', 'coronary'], 'description': 'Cardiovascular medicine'},
            'WL': {'name': 'Neurology', 'keywords': ['neurology', 'neurological', 'brain', 'nervous system', 'neuroscience', 'neuroanatomy', 'stroke', 'epilepsy'], 'description': 'Neurology and neurosciences'},
            'WI': {'name': 'Gastroenterology', 'keywords': ['gastroenterology', 'gastrointestinal', 'digestive', 'liver', 'stomach', 'intestine', 'colon', 'hepatology'], 'description': 'Gastrointestinal medicine'},
            'WK': {'name': 'Endocrinology', 'keywords': ['endocrinology', 'endocrine', 'hormones', 'diabetes', 'thyroid', 'metabolic', 'adrenal', 'pituitary'], 'description': 'Endocrine and metabolic disorders'},
            'QS 1': {'name': 'Anatomy', 'keywords': ['anatomy', 'anatomical', 'structure', 'dissection', 'gross anatomy', 'histology', 'embryology'], 'description': 'Human anatomy'},
            'QT 34': {'name': 'Physiology', 'keywords': ['physiology', 'physiological', 'function', 'homeostasis', 'organ systems', 'cellular physiology'], 'description': 'Human physiology'},
            'QU 34': {'name': 'Biochemistry', 'keywords': ['biochemistry', 'biochemical', 'molecular', 'metabolism', 'enzymes', 'proteins', 'DNA', 'RNA'], 'description': 'Biochemistry and molecular biology'},
            'QW 1': {'name': 'Microbiology', 'keywords': ['microbiology', 'microbial', 'bacteria', 'virus', 'mycology', 'parasitology', 'infection', 'pathogen'], 'description': 'Microbiology and infectious diseases'},
            'QZ 4': {'name': 'Pathology', 'keywords': ['pathology', 'pathological', 'disease process', 'histopathology', 'clinical pathology', 'autopsy'], 'description': 'General pathology'},
            'QV 1': {'name': 'Pharmacology', 'keywords': ['pharmacology', 'pharmaceutical', 'drugs', 'medications', 'pharmacy', 'pharmacokinetics', 'drug therapy'], 'description': 'General pharmacology'},
            'WY 100': {'name': 'Nursing', 'keywords': ['nursing', 'nurse', 'patient care', 'nursing care', 'nursing practice', 'clinical nursing'], 'description': 'Nursing practice'},
            'WA 1': {'name': 'Public Health', 'keywords': ['public health', 'community health', 'epidemiology', 'preventive medicine', 'health promotion', 'global health'], 'description': 'Public health and preventive medicine'},
            'WM 1': {'name': 'Psychiatry', 'keywords': ['psychiatry', 'psychiatric', 'mental health', 'psychology', 'behavioral', 'mental disorders', 'therapy'], 'description': 'Psychiatry and mental health'}
        }
    
    def initialize_keyword_database(self):
        self.specialized_keywords = {
            'textbook': {'weight': 5, 'codes': ['W 18']},
            'student': {'weight': 3, 'codes': ['W 18']},
            'education': {'weight': 3, 'codes': ['W 18']},
            'learning': {'weight': 2, 'codes': ['W 18']},
            'curriculum': {'weight': 4, 'codes': ['W 18']},
            'reference': {'weight': 5, 'codes': ['W 1']},
            'handbook': {'weight': 4, 'codes': ['W 1', 'W 18']},
            'manual': {'weight': 4, 'codes': ['W 1', 'W 18']},
            'guide': {'weight': 3, 'codes': ['W 1', 'W 18']},
            'encyclopedia': {'weight': 5, 'codes': ['W 1']},
            'clinical': {'weight': 4, 'codes': ['WB 100', 'WB 115']},
            'practice': {'weight': 3, 'codes': ['WB 100']},
            'diagnosis': {'weight': 5, 'codes': ['WB 115']},
            'treatment': {'weight': 4, 'codes': ['WB 100']},
            'therapy': {'weight': 4, 'codes': ['WB 100']},
            'surgery': {'weight': 6, 'codes': ['WO 100']},
            'surgical': {'weight': 5, 'codes': ['WO 100']},
            'operation': {'weight': 4, 'codes': ['WO 100']},
            'anesthesia': {'weight': 5, 'codes': ['WO 200']},
            'operative': {'weight': 4, 'codes': ['WO 100']},
            'cardiology': {'weight': 7, 'codes': ['WG']},
            'neurology': {'weight': 7, 'codes': ['WL']},
            'pediatrics': {'weight': 7, 'codes': ['WS 1']},
            'obstetrics': {'weight': 7, 'codes': ['WQ 1']},
            'gynecology': {'weight': 7, 'codes': ['WP 1']},
            'radiology': {'weight': 7, 'codes': ['WN 1']},
            'pathology': {'weight': 7, 'codes': ['QZ 4']},
            'pharmacology': {'weight': 7, 'codes': ['QV 1']},
            'dermatology': {'weight': 7, 'codes': ['WR']},
            'ophthalmology': {'weight': 7, 'codes': ['WW']},
            'orthopedics': {'weight': 7, 'codes': ['WE']},
            'urology': {'weight': 7, 'codes': ['WJ']},
            'psychiatry': {'weight': 7, 'codes': ['WM 1']},
            'emergency': {'weight': 6, 'codes': ['WB 105']},
            'family': {'weight': 6, 'codes': ['WB 110']},
            'geriatrics': {'weight': 6, 'codes': ['WT']},
            'anatomy': {'weight': 7, 'codes': ['QS 1']},
            'physiology': {'weight': 7, 'codes': ['QT 34']},
            'biochemistry': {'weight': 7, 'codes': ['QU 34']},
            'microbiology': {'weight': 7, 'codes': ['QW 1']},
            'genetics': {'weight': 6, 'codes': ['QH 426']},
            'immunology': {'weight': 6, 'codes': ['QW 500']},
            'nursing': {'weight': 5, 'codes': ['WY 100']},
            'public health': {'weight': 5, 'codes': ['WA 1']},
            'ethics': {'weight': 3, 'codes': ['W 50']},
            'research': {'weight': 4, 'codes': ['W 20']},
            'statistics': {'weight': 4, 'codes': ['W 20']},
            'history': {'weight': 3, 'codes': ['WZ']}
        }
    
    def classify_with_confidence(self, title: str, summary: str = "", categories: List[str] = None) -> Dict:
        text_to_analyze = f"{title.lower()} {summary.lower()}"
        if categories:
            text_to_analyze += " " + " ".join(categories).lower()
        results = {}
        
        for keyword, data in self.specialized_keywords.items():
            if self._keyword_in_text(keyword, text_to_analyze):
                for code in data['codes']:
                    if code not in results:
                        results[code] = 0
                    results[code] += data['weight']
        
        for code, data in self.nlm_database.items():
            for keyword in data['keywords']:
                if self._keyword_in_text(keyword, text_to_analyze):
                    if code not in results:
                        results[code] = 0
                    results[code] += 3
        
        if not results:
            return self.get_default_classification(title, summary)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        best_code, best_score = sorted_results[0]
        confidence = self.calculate_confidence(best_score, len(sorted_results))
        
        if len(sorted_results) > 1:
            second_code, second_score = sorted_results[1]
            if best_score - second_score < 2:
                confidence['level'] = 'Medium'
                confidence['note'] = f"Close match with {second_code} (score: {second_score})"
        
        return {
            'nlm_code': best_code,
            'nlm_name': self.nlm_database.get(best_code, {}).get('name', 'Unknown'),
            'nlm_description': self.nlm_database.get(best_code, {}).get('description', ''),
            'confidence_score': best_score,
            'confidence_level': confidence['level'],
            'confidence_reason': confidence['note'],
            'alternative_codes': [{'code': code, 'score': score} for code, score in sorted_results[1:4]],
            'analysis_details': {
                'keywords_found': self.extract_found_keywords(text_to_analyze),
                'text_analyzed': text_to_analyze[:200] + "...",
                'total_matches': len(results)
            }
        }
    
    def _keyword_in_text(self, keyword: str, text: str) -> bool:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        return bool(re.search(pattern, text.lower()))
    
    def calculate_confidence(self, score: int, alternatives_count: int) -> Dict:
        if score >= 15:
            level = "High"
            note = "Very strong keyword matches found"
        elif score >= 8:
            level = "Medium-High"
            note = "Strong keyword matches"
        elif score >= 4:
            level = "Medium"
            note = "Moderate keyword matches"
        elif score >= 2:
            level = "Low-Medium"
            note = "Some keyword matches"
        else:
            level = "Low"
            note = "Weak or generic matches"
        
        if alternatives_count > 2:
            note += f", {alternatives_count} alternatives considered"
        return {'level': level, 'note': note}
    
    def extract_found_keywords(self, text: str) -> List[Dict]:
        found = []
        for keyword, data in self.specialized_keywords.items():
            if self._keyword_in_text(keyword, text):
                found.append({'keyword': keyword, 'weight': data['weight'], 'type': 'specialized'})
        for code, data in self.nlm_database.items():
            for keyword in data['keywords']:
                if self._keyword_in_text(keyword, text):
                    if not any(f['keyword'] == keyword for f in found):
                        found.append({'keyword': keyword, 'weight': 3, 'type': 'general'})
        found.sort(key=lambda x: x['weight'], reverse=True)
        return found[:10]
    
    def get_default_classification(self, title: str, summary: str) -> Dict:
        text = f"{title} {summary}".lower()
        if any(word in text for word in ['textbook', 'student', 'education', 'learning']):
            code = 'W 18'
            reason = 'Educational material detected'
        elif any(word in text for word in ['clinical', 'practice', 'diagnosis', 'treatment']):
            code = 'WB 100'
            reason = 'Clinical practice content'
        elif any(word in text for word in ['surgery', 'surgical', 'operation']):
            code = 'WO 100'
            reason = 'Surgical content detected'
        elif any(word in text for word in ['anatomy', 'structure', 'dissection']):
            code = 'QS 1'
            reason = 'Anatomical content'
        elif any(word in text for word in ['pharmacology', 'drugs', 'medications']):
            code = 'QV 1'
            reason = 'Pharmacology content'
        elif any(word in text for word in ['research', 'study', 'methodology']):
            code = 'W 20'
            reason = 'Research content'
        else:
            code = 'W 1'
            reason = 'General medical reference'
        
        return {
            'nlm_code': code,
            'nlm_name': self.nlm_database.get(code, {}).get('name', 'General Medicine'),
            'nlm_description': self.nlm_database.get(code, {}).get('description', ''),
            'confidence_score': 1,
            'confidence_level': 'Low',
            'confidence_reason': f'Default classification: {reason}',
            'alternative_codes': [],
            'analysis_details': {
                'keywords_found': [],
                'text_analyzed': text[:200] + "...",
                'total_matches': 0
            }
        }