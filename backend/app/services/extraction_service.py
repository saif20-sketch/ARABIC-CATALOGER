from __future__ import annotations
from app.models.schemas import ExtractedEntity
from app.core.config import settings
import re
import json
import structlog
import httpx

logger = structlog.get_logger()

AR_ISBN = re.compile(r"(97[89][-\s]?)?\d{9}[\dXx]")
YEAR_RE = re.compile(r"(19|20)\d{2}")

def _heuristic_extract(text: str) -> ExtractedEntity:
    # هذه قواعد ابتدائية قابلة للتحسين لاحقًا
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    joined = " ".join(lines)

    isbn = None
    m = AR_ISBN.search(joined)
    if m:
        isbn = m.group(0).replace(" ", "").replace("-", "")

    year = None
    ym = YEAR_RE.search(joined)
    if ym:
        year = ym.group(0)

    # عنوان تقريبي: أول سطر طويل غالبًا (صفحة العنوان)
    title = None
    if lines:
        title = max(lines[:5], key=lambda s: len(s)) if len(lines) > 1 else lines[0]

    # مؤلف تقريبي: كلمات بعد "تأليف" أو "إعداد"
    authors = []
    for kw in ["تأليف", "إعداد", "بقلم", "تحرير"]:
        m2 = re.search(rf"{kw}\s*[:\-]?\s*(.+)", joined)
        if m2:
            cand = m2.group(1)
            cand = cand.split("،")[0].split("/")[0].strip()
            if cand:
                authors.append(cand)

    # ناشر/مكان نشر تقريبي
    place = None
    publisher = None
    # مثال: "مسقط : دار المعرفة"
    pub_m = re.search(r"([اأإآء-ي\s]+)\s*:\s*([اأإآء-ي\s]+)", joined)
    if pub_m:
        place = pub_m.group(1).strip()
        publisher = pub_m.group(2).strip()

    return ExtractedEntity(
        title=title,
        authors=list(dict.fromkeys(authors)),
        place_of_publication=place,
        publisher=publisher,
        year=year,
        isbn=isbn,
        notes=[],
        language="ara",
    )

async def _llm_extract(text: str) -> ExtractedEntity:
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment):
        logger.warn("llm_not_configured_fallback")
        return _heuristic_extract(text)

    system = (
        "أنت أخصائي فهرسة محترف. استخرج البيانات الببليوجرافية بدقة من نص OCR عربي."
        " أعد النتيجة JSON فقط وفق المفاتيح المحددة."
    )
    user = f"""
استخرج من النص التالي الحقول:
title, subtitle, statement_of_responsibility, authors (قائمة), edition,
place_of_publication, publisher, year, isbn, physical_description, notes (قائمة).
إن لم يتوفر حقل ضع null أو قائمة فارغة.
النص:
{text}
"""

    url = f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_deployment}/chat/completions?api-version={settings.azure_openai_api_version}"
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.1,
        "max_tokens": 800
    }
    headers = {
        "api-key": settings.azure_openai_api_key,
        "content-type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    content = data["choices"][0]["message"]["content"].strip()
    # حماية: قد يضيف النموذج نصًا حول JSON، فنحاول قصّه
    content_json = _extract_json_block(content)
    obj = json.loads(content_json)
    return ExtractedEntity.model_validate(obj)

def _extract_json_block(s: str) -> str:
    # يحاول استخراج أول JSON object من النص
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
    return s

async def extract_entities(text: str) -> ExtractedEntity:
    if settings.enable_llm:
        try:
            ent = await _llm_extract(text)
            logger.info("extraction_llm_ok")
            return ent
        except Exception as e:
            logger.exception("extraction_llm_failed_fallback", err=str(e))
            return _heuristic_extract(text)
    return _heuristic_extract(text)
