class AdvancedNLMClassifier:
    def __init__(self):
        # قاموس مبسط للكلمات المفتاحية الطبية بالعربية
        self.keywords = {
            'QS': ['تشريح', 'أنسجة', 'أعضاء'],
            'QV': ['أدوية', 'صيدلة', 'علاج دوائي'],
            'WO': ['جراحة', 'عمليات', 'تخدير'],
            'WY': ['تمريض', 'رعاية'],
            'WA': ['صحة عامة', 'بيئة', 'وقاية']
        }

    def classify_with_confidence(self, title, summary=""):
        text = (title + " " + summary).lower()
        for code, keys in self.keywords.items():
            if any(key in text for key in keys):
                return {'nlm_code': f'{code} 100', 'confidence': 'High'}
        
        return {'nlm_code': 'W 1', 'confidence': 'Low'}
