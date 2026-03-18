"""
Модуль: Дисплазия тазобедренного сустава — единый анализатор.

Объединяет два источника данных:
  1. EfficientNet-B3 (ONNX) — бинарная классификация «норма / патология»
  2. YOLO pose — ключевые точки и геометрические метрики

Режимы:
  - Врач: диагностика (классификатор + метрики), overlay с построениями
  - Образовательный: landmarks для расстановки точек студентом

Новый источник метрик добавляется без изменения ядра.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import numpy as np
from PIL import Image

from backend.app.config import settings
from backend.core.base import AnalysisContext, BaseAnalyzer, LandmarkPoint
from backend.core.registry import register
from backend.ml.model_manager import model_manager
from backend.modules.hip_dysplasia.classifier import run_efficientnet_hip_analysis
from backend.modules.hip_dysplasia.landmarks import (
    build_landmarks_from_yolo,
    landmarks_to_payload,
)
from backend.modules.hip_dysplasia.steps import (
    classify_acetabular_index,
    classify_ihdi,
    classify_shenton, classify_by_table,
)
from backend.schema.schemas import (
    AnalysisResponse,
    DiagnosisResult,
    HipDysplasiaMetric,
    HipDysplasiaResult,
    Modality,
)
from backend.service.dicom_pixel_spacing_service import extract_pixel_spacing
from backend.service.hip_yolo import run_yolo_hip_analysis
from backend.service.image_utils import save_overlay

logger = logging.getLogger(__name__)


def _parse_mm(val: str | None) -> float | None:
    if val and val.endswith(" mm"):
        try:
            return float(val.replace(" mm", ""))
        except ValueError:
            pass
    return None


def _try_retuve_shenton(image: Image.Image) -> dict:
    """
    Пытается получить метрики Retuve для дополнительных данных
    (линия Шентона, индекс Виберга и т.д.).

    Возвращает словарь метрик или пустой словарь при ошибке.
    """
    try:
        from backend.service.retuve_runner import run_retuve_analysis
        retuve_result = run_retuve_analysis(image)
        return retuve_result.get("metrics", {})
    except Exception as exc:
        logger.warning("[HipAnalyzer] Retuve недоступен: %s", exc)
        return {}


@register("hip_dysplasia")
class HipDysplasiaAnalyzer(BaseAnalyzer):
    """
    Единый анализатор дисплазии ТБС.

    Доступен через analyzer_id='hip_dysplasia'.
    Объединяет EfficientNet (классификация) + YOLO (метрики)
    """

    NAME = "Дисплазия ТБС"

    def __init__(self, **_: Any) -> None:
        super().__init__(id="hip_dysplasia", name=self.NAME, modality="xray")

    # Доступ к моделям 

    def _get_yolo_model(self):
        """Получает YOLO pose-модель из model_manager."""
        yolo = model_manager.hip_yolo_model
        if yolo is None:
            raise RuntimeError(
                "YOLO-модель для ТБС не загружена. "
                f"Проверьте наличие весов: {settings.DISPLASIYA_YOLO_PATH}"
            )
        return yolo

    def _get_efficientnet_runner(self):
        """Получает EfficientNet ONNX runner из model_manager."""
        runner = model_manager.hip_efficientnet_runner
        if runner is None:
            raise RuntimeError(
                "EfficientNet-B3 ONNX не загружен. "
                f"Проверьте наличие весов: {settings.HIP_EFFICIENTNET_ONNX_PATH}"
            )
        return runner

    # Основной анализ (режим врача) 

    async def analyze(
            self,
            image: Image.Image,
            *,
            context: AnalysisContext,
            modality: Modality = Modality.xray,
            **kwargs: Any,
    ) -> AnalysisResponse:
        modality = Modality(context.modality or "xray")
        request_id = context.request_id or str(uuid.uuid4())[:8]
        patient_age_months = context.patient_age_months

        # Pixel spacing из DICOM (если доступен)
        dicom_contents: bytes | None = kwargs.get("dicom_contents")
        pixel_spacing = extract_pixel_spacing(dicom_contents) if dicom_contents else None
        pixel_spacing_warning: list[str] = []
        if pixel_spacing is None:
            pixel_spacing_warning = [
                "Pixel Spacing недоступен — расстояния h/d только в пикселях. "
                "Для метрик в мм загрузите DICOM с тегом PixelSpacing."
            ]

        logger.info("[HipAnalyzer] Старт анализа request_id=%s", request_id)

        # 1. EfficientNet — бинарная классификация 
        efficientnet_runner = self._get_efficientnet_runner()
        en_result = run_efficientnet_hip_analysis(image, efficientnet_runner)

        # 2. YOLO — ключевые точки и геометрические метрики 
        yolo_model = self._get_yolo_model()
        yolo_result = run_yolo_hip_analysis(
            image, yolo_model, pixel_spacing=pixel_spacing
        )
        metrics_raw: dict = yolo_result["metrics"]
        overlay_np: np.ndarray = yolo_result["overlay"]
        sides: dict = yolo_result["sides"]
        warnings: list[str] = yolo_result["warnings"] + pixel_spacing_warning

        # 3. Дополнительные метрики (Шентон и др.) 
        yolo_has_shenton = (
                metrics_raw.get("shenton_left") is not None
                or metrics_raw.get("shenton_right") is not None
        )
        retuve_metrics: dict = {}
        if not yolo_has_shenton:
            retuve_metrics = _try_retuve_shenton(image)

        if warnings:
            logger.warning("[HipAnalyzer] Предупреждения: %s", warnings)

        # 4. Сохраняем overlay и оригинал 
        original_np = np.array(image.convert("RGB"))
        heatmap_url = save_overlay(original_np, f"{request_id}_hip_original.jpg")
        overlay_url = save_overlay(overlay_np, f"{request_id}_hip_overlay.jpg")

        # 5. Формируем список метрик с классификацией 
        metrics_list: list[HipDysplasiaMetric] = []

        # Ацетабулярный индекс (из YOLO)
        for key, name_ru, side in [
            ("ace_index_left", "Ацетабулярный индекс (лев)", "left"),
            ("ace_index_right", "Ацетабулярный индекс (пр)", "right"),
        ]:
            val = metrics_raw.get(key)
            if val is None:
                continue
            classification, color = classify_acetabular_index(
                float(val), age_months=patient_age_months
            )
            metrics_list.append(
                HipDysplasiaMetric(
                    name=key, name_ru=name_ru,
                    value=round(float(val), 1),
                    side=side,
                    classification=classification, color=color,
                )
            )

        # IHDI (из YOLO)
        for key, name_ru, side in [
            ("ihdi_left", "IHDI (лев)", "left"),
            ("ihdi_right", "IHDI (пр)", "right"),
        ]:
            val = metrics_raw.get(key)
            if val is None:
                continue
            grade = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(str(val), 0)
            classification, color = classify_ihdi(grade)
            metrics_list.append(
                HipDysplasiaMetric(
                    name=key, name_ru=name_ru,
                    value=val,
                    side=side,
                    classification=classification, color=color,
                )
            )

        # h/d смещения (из YOLO)
        for key, name_ru, side in [
            ("h_left", "Верт. смещение головки (лев)", "left"),
            ("h_right", "Верт. смещение головки (пр)", "right"),
            ("d_left", "Гориз. смещение (лев)", "left"),
            ("d_right", "Гориз. смещение (пр)", "right"),
        ]:
            val = metrics_raw.get(key)
            if val is None:
                continue
            metrics_list.append(
                HipDysplasiaMetric(
                    name=key, name_ru=name_ru,
                    value=val,
                    side=side,
                    classification=None, color=None,
                )
            )

        # Линия Шентона 
        for key, name_ru, side in [
            ("shenton_left", "Линия Шентона (лев)", "left"),
            ("shenton_right", "Линия Шентона (пр)", "right"),
        ]:
            val = metrics_raw.get(key)
            if val is None:
                retuve_key = f"shenton{key.replace('shenton', '')}"
                val = retuve_metrics.get(retuve_key)
            if val is None:
                continue
            classification, color = classify_shenton(str(val))
            metrics_list.append(
                HipDysplasiaMetric(
                    name=key,
                    name_ru=name_ru,
                    value=classification,
                    side=side,
                    classification=None,
                    color=color,
                )
            )

        # 6. Landmarks для образовательного режима 
        landmarks = build_landmarks_from_yolo(image, sides)
        landmarks_payload = landmarks_to_payload(landmarks)

        # 7. Общий диагноз 

        table_results: dict[str, tuple[str, str, list[str]]] = {}
        for side_key in ("left", "right"):
            ace = metrics_raw.get(f"ace_index_{side_key}")
            d_mm = _parse_mm(metrics_raw.get(f"d_{side_key}"))
            h_mm = _parse_mm(metrics_raw.get(f"h_{side_key}"))

            verdict, color, reasons = classify_by_table(
                ace_deg=float(ace) if ace is not None else None,
                d_mm=d_mm,
                h_mm=h_mm,
                age_months=patient_age_months,
            )
            table_results[side_key] = (verdict, color, reasons)
            logger.info("[HipAnalyzer] Таблица %s: %s | %s", side_key, verdict, reasons)

        verdict_left, _, reasons_left = table_results.get("left", ("нет данных", "gray", []))
        verdict_right, _, reasons_right = table_results.get("right", ("нет данных", "gray", []))

        en_label = en_result.get("label", "unknown")
        en_confidence = float(en_result.get("confidence", 0.0))
        en_is_pathology = bool(en_result.get("is_pathology", False))

        table_is_pathology = any(
            "ст." in table_results.get(s, ("",))[0]
            for s in ("left", "right")
        )

        is_pathology = en_is_pathology or table_is_pathology

        confidence = _combined_confidence(
            en_confidence=en_confidence,
            en_is_pathology=en_is_pathology,
            table_is_pathology=table_is_pathology,
            table_results=table_results,
        )

        overall_diagnosis = (
            f"По таблице (лев): {verdict_left} | {', '.join(reasons_left)}\n"
            f"По таблице (пр):  {verdict_right} | {', '.join(reasons_right)}\n"
            f"EfficientNet: {en_label} (уверенность {en_confidence:.0%})"
        )

        logger.info(
            "[HipAnalyzer] Завершено request_id=%s, метрик=%d, landmarks=%d, "
            "патология=%s, возраст_мес=%s",
            request_id, len(metrics_list), len(landmarks),
            is_pathology, patient_age_months,
        )

        return AnalysisResponse(
            request_id=request_id,
            analyzer_id="hip_dysplasia",
            modality=modality,
            diagnosis=DiagnosisResult(
                predicted_class=1 if is_pathology else 0,
                label="Дисплазия обнаружена" if is_pathology else "Признаков дисплазии не обнаружено",
                confidence=confidence,
                is_pathology=is_pathology,
            ),
            gradcam=None,
            microscopy=None,
            hip_dysplasia=HipDysplasiaResult(
                overlay_url=overlay_url,
                heatmap_url=heatmap_url,
                metrics=metrics_list,
                overall_diagnosis=overall_diagnosis,
                educational_info=None,
            ),
            extra={
                "landmarks": landmarks_payload,
                "yolo_warnings": warnings,
                "sides_raw": {
                    side: {
                        "measurements": det["measurements"],
                        "keypoints": {
                            k: {"x": round(v[0], 1), "y": round(v[1], 1)}
                            for k, v in det["kp"].items()
                        },
                    }
                    for side, det in sides.items()
                },
                "patient_age_months": patient_age_months,
                "patient_age_source": context.patient_age_source,
                "classifier": {
                    "label": en_result.get("label"),
                    "confidence": en_result.get("confidence"),
                    "is_pathology": is_pathology,
                    "threshold": en_result.get("threshold"),
                },
            },
            model_version="hip-yolo-efficientnet-1.0",
        )

    # Landmarks для образовательного режима 

    async def get_landmarks(
            self,
            image: Image.Image,
    ) -> dict[str, LandmarkPoint]:
        """Извлекает ключевые точки YOLO для образовательного режима."""
        logger.info("[HipAnalyzer] Запрос landmarks через get_landmarks")
        yolo_model = self._get_yolo_model()
        yolo_result = run_yolo_hip_analysis(image, yolo_model)
        return build_landmarks_from_yolo(image, yolo_result["sides"])


def _combined_confidence(
        en_confidence: float,
        en_is_pathology: bool,
        table_is_pathology: bool,
        table_results: dict,
) -> float:
    """
    Комбинированная уверенность из двух источников.

    Веса: EfficientNet 0.6, таблица 0.4
    Согласие источников даёт бонус +0.05, конфликт — штраф -0.10.
    """
    EN_WEIGHT = 0.6
    TABLE_WEIGHT = 0.4
    AGREE_BONUS = 0.05
    CONFLICT_PEN = 0.10

    # "Уверенность" таблицы — считаем сколько сторон дали патологию
    pathology_sides = sum(
        1 for s in ("left", "right")
        if "ст." in table_results.get(s, ("",))[0]
    )
    # 0 сторон → 0.15, 1 сторона → 0.65, 2 стороны → 0.90
    table_confidence = {0: 0.15, 1: 0.65, 2: 0.90}.get(pathology_sides, 0.15)
    if not table_is_pathology:
        table_confidence = 1.0 - table_confidence  # инвертируем для нормы

    combined = EN_WEIGHT * en_confidence + TABLE_WEIGHT * table_confidence
    print(combined)

    # Бонус/штраф за согласие/конфликт
    if en_is_pathology == table_is_pathology:
        combined = min(1.0, combined + AGREE_BONUS)
    else:
        combined = max(0.0, combined - CONFLICT_PEN)

    print(combined)

    return round(combined, 2)
