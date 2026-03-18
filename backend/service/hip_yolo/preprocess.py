"""Предобработка рентген-снимка для устойчивого YOLO-инференса."""

from __future__ import annotations

import cv2
import numpy as np


def preprocess_for_yolo(img_bgr: np.ndarray) -> np.ndarray:
    """Применяет авто-гамму и CLAHE, возвращает BGR-изображение."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    median = max(1.0, float(np.median(gray)))
    gamma = float(np.clip(np.log(127 / 255.0) / np.log(median / 255.0), 0.4, 3.0))
    lut = np.array(
        [min(255, int((i / 255.0) ** (1.0 / gamma) * 255)) for i in range(256)],
        dtype=np.uint8,
    )
    brightened = cv2.LUT(gray, lut)
    enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(brightened)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
