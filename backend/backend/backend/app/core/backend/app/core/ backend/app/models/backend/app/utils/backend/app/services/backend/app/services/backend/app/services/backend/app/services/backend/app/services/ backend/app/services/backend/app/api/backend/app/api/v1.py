from fastapi import APIRouter, UploadFile, File
from typing import List
from PIL import Image
import io

from app.models.schemas import IngestResponse, HealthResponse
from app.services.ocr_service import OCRService
from app.services.extraction_service import extract_entities
from app.services.marc_service import build_marc
from app.services.subjects_service import suggest_subjects
from app.services.classification_service import suggest_lcc
from app.services.authority_service import normalize_authors

router = APIRouter(prefix="/api/v1")

ocr_service = OCRService()

@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")

@router.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    images: list[Image.Image] = []
    for f in files:
        content = await f.read()
        img = Image.open(io.BytesIO(content))
        images.append(img)

    ocr_text = ocr_service.extract_text(images)
    extracted = await extract_entities(ocr_text)

    extracted.authors = normalize_authors(extracted.authors)

    subjects = suggest_subjects(extracted, ocr_text)
    classifications = suggest_lcc(extracted, ocr_text)

    marc = build_marc(extracted)

    return IngestResponse(
        ocr_text=ocr_text,
       
