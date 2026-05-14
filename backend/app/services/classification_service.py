from __future__ import annotations
from app.models.schemas import ExtractedEntity, ClassificationSuggestion
from rapidfuzz import fuzz

# خرائط محلية كبداية (LCC top-level)
_LCC_LOCAL = [
    {"classmark": "QM", "label": "Human anatomy", "ar": ["التشريح", "علم التشريح"]},
    {"classmark": "R", "label": "Medicine (General)", "ar": ["الطب"]},
    {"classmark": "Z", "label": "Bibliography. Library science", "ar": ["المكتبات", "فهرسة", "علم المكتبات"]},
]

def suggest_lcc(ent: ExtractedEntity, ocr_text: str) -> listhay = f"{ent.title or ''} {ent.subtitle or ''} {ocr_text}"

    out: list[ClassificationSuggestion] = []
    for item in _LCC_LOCAL:
        best = 0
        for ar_kw in item["ar"]:
            best = max(best, fuzz.partial_ratio(ar_kw, hay))
        if best >= 78:
            out.append(ClassificationSuggestion(classmark=item["classmark"], confidence=best / 100.0))
    out.sort(key=lambda x: x.confidence, reverse=True)
    return out[:3]
