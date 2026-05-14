from __future__ import annotations
from app.models.schemas import ExtractedEntity, SubjectSuggestion
from rapidfuzz import fuzz
import json
from pathlib import Path

# قاموس محلي بسيط كبداية (يمكن استبداله بقاعدة بيانات/ API)
_LCSH_LOCAL = [
    {"heading": "Anatomy", "ar": ["التشريح", "علم التشريح"]},
    {"heading": "Medicine", "ar": ["الطب", "علوم طبية"]},
    {"heading": "Libraries", "ar": ["المكتبات", "علم المكتبات"]},
]

def suggest_subjects(ent: ExtractedEntity, ocr_text: str) -> listhay = f"{ent.title or ''} {ent.subtitle or ''} {ocr_text}"
    hay = hay.strip()

    suggestions: list[SubjectSuggestion] = []
    for item in _LCSH_LOCAL:
        best = 0
        for ar_kw in item["ar"]:
            best = max(best, fuzz.partial_ratio(ar_kw, hay))
        if best >= 80:
            suggestions.append(SubjectSuggestion(heading=item["heading"], confidence=best / 100.0))

    # ترتيب
    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions[:6]
