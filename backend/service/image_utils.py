"""
Утилиты для работы с медицинскими изображениями.

Загрузка, сохранение и конвертация изображений.
"""

from __future__ import annotations

import base64
import io
import pydicom
import cv2
import numpy as np
from PIL import Image

from backend.app.config import settings


def save_overlay(image_np: np.ndarray, filename: str) -> str:
    """
    Сохраняет numpy RGB-изображение в overlays/ и возвращает относительный URL.
    """
    path = settings.RESULTS_DIR / filename
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), image_bgr)
    return f"/api/analysis/results/{filename}"


def image_to_base64(image: Image.Image, fmt: str = "JPEG") -> str:
    """Конвертирует PIL Image в base64-строку (data-uri ready)."""
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def load_dicom(file_path: str) -> tuple[np.ndarray, str]:
    """
    Загружает DICOM-файл и возвращает (BGR numpy array, info string).
    Применяет windowing при наличии WindowCenter/WindowWidth.
    """

    dcm = pydicom.dcmread(file_path)
    arr = dcm.pixel_array.astype(np.float32)

    if hasattr(dcm, "WindowCenter") and hasattr(dcm, "WindowWidth"):
        wc = (
            float(dcm.WindowCenter)
            if not isinstance(dcm.WindowCenter, pydicom.multival.MultiValue)
            else float(dcm.WindowCenter[0])
        )
        ww = (
            float(dcm.WindowWidth)
            if not isinstance(dcm.WindowWidth, pydicom.multival.MultiValue)
            else float(dcm.WindowWidth[0])
        )
        lo, hi = wc - ww / 2, wc + ww / 2
        arr = np.clip(arr, lo, hi)

    arr = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255).astype(np.uint8)
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

    patient = getattr(dcm, "PatientName", "N/A")
    info = f"DICOM | Пациент: {patient} | Размер: {arr.shape[1]}×{arr.shape[0]}"
    return arr, info
