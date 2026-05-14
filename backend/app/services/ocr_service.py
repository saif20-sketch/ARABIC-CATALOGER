from __future__ import annotations
from PIL import Image
from typing import List
import structlog

from app.utils.image_utils import preprocess_image

logger = structlog.get_logger()

class OCRService:
    def __init__(self) -> None:
        self._ocr = None

    def _lazy_init(self) -> None:
        if self._ocr is not None:
            return
        # PaddleOCR أفضل للعربية غالبًا
        from paddleocr import PaddleOCR
        self._ocr = PaddleOCR(use_angle_cls=True, lang="ar")
        logger.info("ocr_initialized", engine="PaddleOCR", lang="ar")

    def extract_text(self, images: List[Image.Image]) -> str:
        self._lazy_init()
        texts: list[str] = []

        for idx, img in enumerate(images):
            processed = preprocess_image(img)
            result = self._ocr.ocr(
                np_to_bgr(processed), cls=True
            )
            page_text = []
            for line in result[0] if result and result[0] else []:
                page_text.append(line[1][0])
            joined = "\n".join(page_text).strip()
            logger.info("ocr_page_done", page=idx, chars=len(joined))
            texts.append(joined)

        return "\n\n".join([t for t in texts if t])

def np_to_bgr(pil_img: Image.Image):
    import numpy as np
    import cv2
    arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
