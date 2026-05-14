from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ExtractedEntity(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    statement_of_responsibility: Optional[str] = None  # بيانات المسؤولية
    authors: List[str] = Field(default_factory=list)
    edition: Optional[str] = None
    place_of_publication: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[str] = None
    isbn: Optional[str] = None
    language: str = "ara"
    notes: List[str] = Field(default_factory=list)
    physical_description: Optional[str] = None  # مثال: "250 صفحة : إيض. ; 24 سم"

class SubjectSuggestion(BaseModel):
    scheme: str = "LCSH"
    heading: str
    confidence: float = 0.0

class ClassificationSuggestion(BaseModel):
    scheme: str = "LCC"
    classmark: str
    confidence: float = 0.0

class MarcOutput(BaseModel):
    marc21_text: str
    marcxml: str

class IngestResponse(BaseModel):
    ocr_text: str
    extracted: ExtractedEntity
    subjects: List[SubjectSuggestion] = Field(default_factory=list)
    classifications: List[ClassificationSuggestion] = Field(default_factory=list)
    marc: MarcOutput
    debug: Dict[str, str] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str = "ok"
