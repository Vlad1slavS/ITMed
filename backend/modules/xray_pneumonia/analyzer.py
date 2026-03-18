"""
Модуль: Рентген лёгких — классификация пневмонии.

Архитектура: EfficientNet-B3 + Grad-CAM.
Single Responsibility: только классификация рентгенограмм грудной клетки.
"""

from __future__ import annotations

import uuid
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from backend.core.base import AnalysisContext, BaseAnalyzer
from backend.core.registry import register
from backend.ml.model_manager import model_manager
from backend.ml.models import XRayModel
from backend.schema.schemas import (
    ActivationPoint,
    AnalysisResponse,
    BoundingBox,
    DiagnosisResult,
    GradCamResult,
    Modality,
    PathologyZone,
)
from backend.service.image_utils import save_overlay


# Вспомогательные функции (приватные для модуля) 


def _compute_severity(mean_activation: float) -> str:
    """Тяжесть зоны по средней активации Grad-CAM."""
    if mean_activation < 0.4:
        return "low"
    if mean_activation < 0.7:
        return "medium"
    return "high"


def _extract_zones(cam: np.ndarray, contours: list) -> list[PathologyZone]:
    """Извлекает зоны патологий из контуров Grad-CAM."""
    total_area = cam.shape[0] * cam.shape[1]
    zones: list[PathologyZone] = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 50:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        mask = np.zeros(cam.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, (255,), -1)
        mean_val = float(cam[mask == 255].mean()) if mask.sum() > 0 else 0.0
        zones.append(
            PathologyZone(
                zone_id=i + 1,
                area_px=int(area),
                area_percent=round(area / total_area * 100, 2),
                bounding_box=BoundingBox(x=x, y=y, width=w, height=h),
                severity=_compute_severity(mean_val),
            )
        )
    zones.sort(key=lambda z: z.area_px, reverse=True)
    return zones


# Анализатор 


@register("xray_pneumonia")
class XRayPneumoniaAnalyzer(BaseAnalyzer):
    """
    Классификация пневмонии на рентгенограммах грудной клетки.

    Возвращает: AnalysisResponse с GradCamResult (тепловая карта, зоны).
    """

    NAME = "Рентген лёгких — Пневмония"

    def __init__(self, **_: Any) -> None:
        super().__init__(id="xray_pneumonia", name=self.NAME, modality="xray")

    async def analyze(
        self,
        image: Image.Image,
        *,
        context: AnalysisContext,
        **_: Any,
    ) -> AnalysisResponse:
        request_id = context.request_id or str(uuid.uuid4())[:8]

        # Препроцессинг
        tensor, original_np = model_manager.preprocess(image)

        # GradCAM
        gradcam = model_manager.get_gradcam(Modality.xray)
        if gradcam is None:
            raise RuntimeError("GradCAM для рентгена не инициализирован")

        model = model_manager.get_model(Modality.xray)
        if model is None:
            raise RuntimeError("Рентген модель не загружена")

        class_names = model_manager.get_class_names(Modality.xray)

        with torch.enable_grad():
            gradcam_output = gradcam.process(
                input_tensor=tensor, original_image=original_np, threshold=0.6
            )

        with torch.no_grad():
            output = model(tensor)
            probs = torch.softmax(output, dim=1)[0].cpu().numpy()

        predicted_class = int(probs.argmax())
        confidence = float(probs[predicted_class])

        # Сохранение визуализаций
        heatmap_url = save_overlay(gradcam_output.heatmap, f"{request_id}_heatmap.jpg")
        overlay_url = save_overlay(gradcam_output.overlay, f"{request_id}_overlay.jpg")
        zones = (
            _extract_zones(gradcam_output.cam, list(gradcam_output.contours))
            if predicted_class != 0
            else []
        )

        return AnalysisResponse(
            request_id=request_id,
            analyzer_id="xray_pneumonia",
            modality=Modality.xray,
            diagnosis=DiagnosisResult(
                predicted_class=predicted_class,
                label=class_names[predicted_class],
                confidence=round(confidence, 4),
                is_pathology=predicted_class != 0,
            ),
            gradcam=GradCamResult(
                heatmap_url=heatmap_url,
                overlay_url=overlay_url,
                main_activation_point=ActivationPoint(
                    x=int(gradcam_output.main_point[1]),
                    y=int(gradcam_output.main_point[0]),
                ),
                pathology_zones=zones,
                zones_count=len(zones),
            ),
            microscopy=None,
            model_version=XRayModel.VERSION,
        )
