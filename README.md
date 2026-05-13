# Arabic Cataloger (OCR → MARC21/RDA)

منصة لفهرسة الكتب العربية عبر:
- رفع صور صفحة العنوان/البيانات
- OCR عربي
- استخراج البيانات
- توليد MARC21 (RDA-friendly)
- اقتراحات LCC و LCSH (قابلة للتطوير)

## التشغيل عبر Docker
1) انسخ backend/.env.example إلى backend/.env واملأ القيم إن رغبت بالـ LLM.
2) شغّل:
```bash
docker compose up --build
