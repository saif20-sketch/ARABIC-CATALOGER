from __future__ import annotations
from app.models.schemas import ExtractedEntity, MarcOutput
from pymarc import Record, Field, XMLWriter
import io

def _clean(s: str | None) -> str | None:
    if not s:
        return None
    s2 = " ".join(s.split()).strip()
    return s2 or None

def build_marc(ent: ExtractedEntity) -> MarcOutput:
    record = Record(force_utf8=True)

    # Leader (مبدئي)
    record.leader = "00000nam a2200000 a 4500"

    # 040 Cataloging Source (مثال)
    record.add_field(Field(tag="040", indicators=[" ", " "], subfields=[
        "a", "AR-CAT",
        "b", "ara",
        "e", "rda"
    ]))

    # 020 ISBN
    if ent.isbn:
        record.add_field(Field(tag="020", indicators=[" ", " "], subfields=["a", ent.isbn]))

    # 100 Main Entry - Personal Name (إن توفر مؤلف واحد على الأقل)
    if ent.authors:
        record.add_field(Field(tag="100", indicators=["1", " "], subfields=["a", ent.authors[0]]))

    # 245 Title Statement
    title = _clean(ent.title) or "[عنوان غير محدد]"
    subfields = ["a", title]
    if _clean(ent.subtitle):
        subfields += ["b", _clean(ent.subtitle)]
    if _clean(ent.statement_of_responsibility):
        subfields += ["c", _clean(ent.statement_of_responsibility)]
    elif len(ent.authors) > 0:
        # إذا لم يحدد المسؤولية، نضعها من المؤلفين كحل عملي
        subfields += ["c", "؛ ".join(ent.authors)]

    record.add_field(Field(tag="245", indicators=["1", "0"], subfields=subfields))

    # 250 Edition Statement
    if _clean(ent.edition):
        record.add_field(Field(tag="250", indicators=[" ", " "], subfields=["a", _clean(ent.edition)]))

    # 264 Publication (RDA)
    pub_sub = []
    if _clean(ent.place_of_publication):
        pub_sub += ["a", _clean(ent.place_of_publication)]
    if _clean(ent.publisher):
        pub_sub += ["b", _clean(ent.publisher)]
    if _clean(ent.year):
        pub_sub += ["c", _clean(ent.year)]
    if pub_sub:
        record.add_field(Field(tag="264", indicators=[" ", "1"], subfields=pub_sub))

    # 300 Physical Description
    if _clean(ent.physical_description):
        record.add_field(Field(tag="300", indicators=[" ", " "], subfields=["a", _clean(ent.physical_description)]))

    # 500 Notes
    for n in ent.notes:
        n2 = _clean(n)
        if n2:
            record.add_field(Field(tag="500", indicators=[" ", " "], subfields=["a", n2]))

    # 041 Language Code (اختياري)
    if ent.language:
        record.add_field(Field(tag="041", indicators=["0", " "], subfields=["a", ent.language]))

    marc_text = record.as_marc21()

    # MARCXML
    buffer = io.BytesIO()
    writer = XMLWriter(buffer)
    writer.write(record)
    writer.close()
    marcxml = buffer.getvalue().decode("utf-8", errors="ignore")

    return MarcOutput(marc21_text=marc_text.decode("utf-8", errors="ignore"), marcxml=marcxml)
