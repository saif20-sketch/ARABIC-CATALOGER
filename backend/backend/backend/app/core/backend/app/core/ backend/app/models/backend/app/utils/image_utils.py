from PIL import Image
import numpy as np
import cv2

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """
    تحسين الصورة لرفع دقة OCR:
    - تحويل إلى رمادي
    - إزالة ضوضاء خفيفة
    - تحسين التباين/العتبة
    """
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 11
    )
    return Image.fromarray(th)
