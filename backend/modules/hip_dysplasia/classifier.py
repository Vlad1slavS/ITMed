"""
EfficientNet-B3 для бинарной классификации дисплазии ТБС.

Single Responsibility: предобработка снимка и запуск ONNX-сессии.
Решение «патология / норма» принимается по откалиброванному порогу из JSON.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class EfficientNetConfig:
    """Параметры модели из JSON-файла с .onnx весами."""

    model_name: str
    img_size: int
    threshold: float
    classes: list[str]
    imagenet_mean: list[float]
    imagenet_std: list[float]

    @classmethod
    def from_json(cls, path: Path) -> "EfficientNetConfig":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            model_name=data["model_name"],
            img_size=data["img_size"],
            threshold=data["threshold"],
            classes=data["classes"],
            imagenet_mean=data["imagenet_mean"],
            imagenet_std=data["imagenet_std"],
        )


class EfficientNetOnnxRunner:
    """
    Обёртка над ONNX-сессией EfficientNet-B3.

    Загружается один раз в model_manager, переиспользуется для каждого снимка.
    """

    def __init__(self, onnx_path: Path, config_path: Path) -> None:
        self.config = EfficientNetConfig.from_json(config_path)
        self.session = ort.InferenceSession(
            str(onnx_path),
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        logger.info(
            "[EfficientNetOnnx] Загружен: %s, img_size=%d, threshold=%.4f, classes=%s",
            onnx_path.name,
            self.config.img_size,
            self.config.threshold,
            self.config.classes,
        )

    # Предобработка (идентична обучению) 
    def _preprocess(self, image: Image.Image) -> np.ndarray:
        # 1. PIL → BGR для CLAHE
        img_bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)

        # 2. Авто-гамма + CLAHE
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        median = max(1.0, float(np.median(gray)))
        gamma = float(
            np.clip(np.log(127 / 255.0) / np.log(median / 255.0), 0.4, 3.0)
        )
        lut = np.array(
            [min(255, int((i / 255.0) ** (1.0 / gamma) * 255)) for i in range(256)],
            dtype=np.uint8,
        )
        brightened = cv2.LUT(gray, lut)
        enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(brightened)
        img_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # 3. BGR → RGB, resize
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        size = self.config.img_size
        img_resized = cv2.resize(img_rgb, (size, size), interpolation=cv2.INTER_LINEAR)

        # 4. ImageNet нормализация
        arr = img_resized.astype(np.float32) / 255.0
        mean = np.array(self.config.imagenet_mean, dtype=np.float32)
        std = np.array(self.config.imagenet_std, dtype=np.float32)
        arr = (arr - mean) / std

        # 5. HWC → CHW → batch
        arr = arr.transpose(2, 0, 1)
        return arr[np.newaxis, ...].astype(np.float32)

    # Инференс
    def run(self, image: Image.Image) -> dict:
        """
        Запускает классификацию.

        Returns
        -------
        dict:
            label        : str   — "normal" | "pathology"
            confidence   : float — уверенность в предсказанном классе
            probs        : dict  — {class_name: prob}
            is_pathology : bool
            threshold    : float — порог из конфига
        """
        tensor = self._preprocess(image)
        outputs = self.session.run(None, {self.input_name: tensor})

        raw = outputs[0][0]
        # Если logits — применяем softmax
        if raw.min() < 0 or raw.max() > 1 or abs(raw.sum() - 1.0) > 0.01:
            exp = np.exp(raw - raw.max())
            probs = exp / exp.sum()
        else:
            probs = raw

        classes = self.config.classes
        threshold = self.config.threshold

        pathology_idx = next((i for i, c in enumerate(classes) if c != "normal"), 1)
        prob_pathology = float(probs[pathology_idx])

        is_pathology = prob_pathology >= threshold
        predicted_idx = pathology_idx if is_pathology else 0
        label = classes[predicted_idx]
        confidence = float(probs[predicted_idx])

        probs_dict = {cls: round(float(p), 4) for cls, p in zip(classes, probs)}

        logger.info(
            "[EfficientNetOnnx] label=%s, p_pathology=%.3f, threshold=%.4f, is_pathology=%s",
            label,
            prob_pathology,
            threshold,
            is_pathology,
        )

        return {
            "label": label,
            "confidence": confidence,
            "probs": probs_dict,
            "is_pathology": is_pathology,
            "threshold": threshold,
        }


def run_efficientnet_hip_analysis(
    image: Image.Image,
    runner: EfficientNetOnnxRunner,
) -> dict:
    """Публичный API — запуск классификации через EfficientNet."""
    return runner.run(image)
