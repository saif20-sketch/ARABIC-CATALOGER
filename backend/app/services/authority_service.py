from __future__ import annotations
from typing import List

def normalize_authors(authors: List[str]) -> List# مبدئيًا: تنظيف بسيط. لاحقًا: ربط VIAF/LOC/NACO أو ملف محلي.
    cleaned = []
    for a in authors:
        a2 = " ".join(a.split()).strip().strip("،.")
        if a2:
            cleaned.append(a2)
    # إزالة التكرار مع الحفاظ على الترتيب
    seen = set()
    out = []
    for a in cleaned:
        if a not in seen:
            out.append(a)
            seen.add(a)
    return out 
