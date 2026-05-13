class LCCClassifier:
    def __init__(self):
        # أمثلة لرموز مكتبة الكونجرس للكتب العربية
        self.lcc_map = {
            'PJ': 'Arabic Literature',
            'BP': 'Islam',
            'DS': 'History of Asia (Middle East)',
            'R': 'Medicine (General)'
        }

    def verify_lcc(self, code):
        prefix = ''.join([i for i in code if not i.isdigit()]).strip()
        return self.lcc_map.get(prefix, "General Classification")
