"""
Модуль: Микроскопия крови — детекция и подсчет клеток.

Архитектура: Cellpose сегментация + EfficientNet-B0 классификатор.
Single Responsibility: только анализ мазков крови.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Any, cast

import cv2
import numpy as np
from PIL import Image

from backend.core.base import AnalysisContext, BaseAnalyzer
from backend.core.registry import register
from backend.ml.model_manager import model_manager
from backend.ml.models import MicroscopyModel
from backend.schema.schemas import (
    AnalysisResponse,
    BoundingBox,
    CellCount,
    CellDetection,
    DiagnosisResult,
    MicroscopyResult,
    Modality,
)
from backend.service.image_utils import save_overlay

logger = logging.getLogger(__name__)


def _make_clinical_note(counts: CellCount) -> str:
    """Клиническая интерпретация по подсчету клеток."""
    notes: list[str] = []

    if counts.WBC == 0 and counts.RBC == 0:
        return "Клетки не обнаружены. Проверьте качество снимка."

    if counts.RBC > 0 and counts.WBC > 0 and counts.RBC / counts.WBC < 100:
        notes.append(
            "Повышенное относительное количество лейкоцитов — возможен воспалительный процесс."
        )

    if counts.Platelets == 0 and counts.RBC > 0:
        notes.append("Тромбоциты не обнаружены — требуется внимание.")

    return " ".join(notes) if notes else "Показатели в пределах нормы."


def _build_microscopy_summary(
    counts: CellCount,
    total_cells: int,
) -> list[dict[str, str | bool]]:
    """Формирует сводку показателей (что в норме и что требует внимания)."""
    summary: list[dict[str, str | bool]] = []

    summary.append(
        {
            "key": "cells_detected",
            "label": "Клетки на изображении",
            "value": str(total_cells),
            "status": "normal" if total_cells > 0 else "abnormal",
            "details": "Клетки обнаружены" if total_cells > 0 else "Клетки не обнаружены",
            "status_text": "В норме" if total_cells > 0 else "Вне нормы",
            "affects_diagnosis": False,
        }
    )

    if counts.WBC > 0 and counts.RBC > 0:
        ratio = counts.RBC / counts.WBC
        ratio_normal = ratio >= 100
        summary.append(
            {
                "key": "wbc_rbc_ratio",
                "label": "Соотношение RBC/WBC",
                "value": f"{ratio:.1f}:1",
                "status": "normal" if ratio_normal else "abnormal",
                "details": (
                    "Лейкоциты не повышены относительно эритроцитов"
                    if ratio_normal
                    else "Относительно много лейкоцитов, требуется внимание"
                ),
                "status_text": "В норме" if ratio_normal else "Вне нормы",
                "affects_diagnosis": True,
            }
        )
    elif counts.WBC == 0 and counts.RBC > 0:
        summary.append(
            {
                "key": "wbc_rbc_ratio",
                "label": "Соотношение RBC/WBC",
                "value": "WBC не обнаружены",
                "status": "abnormal",
                "details": "Лейкоциты не определены, оценка соотношения ограничена",
                "status_text": "Вне нормы",
                "affects_diagnosis": True,
            }
        )
    elif counts.RBC == 0 and counts.WBC > 0:
        summary.append(
            {
                "key": "wbc_rbc_ratio",
                "label": "Соотношение RBC/WBC",
                "value": "RBC не обнаружены",
                "status": "abnormal",
                "details": "Эритроциты не определены, оценка соотношения ограничена",
                "status_text": "Вне нормы",
                "affects_diagnosis": True,
            }
        )
    else:
        summary.append(
            {
                "key": "wbc_rbc_ratio",
                "label": "Соотношение RBC/WBC",
                "value": "Нет данных",
                "status": "abnormal",
                "details": "Недостаточно клеток для расчета соотношения",
                "status_text": "Вне нормы",
                "affects_diagnosis": False,
            }
        )

    platelets_ok = counts.Platelets > 0
    summary.append(
        {
            "key": "platelets",
            "label": "Тромбоциты",
            "value": str(counts.Platelets),
            "status": "normal" if platelets_ok else "abnormal",
            "details": (
                "Тромбоциты определены"
                if platelets_ok
                else "Тромбоциты не обнаружены, проверьте качество снимка"
            ),
            "status_text": "В норме" if platelets_ok else "Вне нормы",
            "affects_diagnosis": True,
        }
    )

    return summary


@register("blood_cells")
class BloodCellsAnalyzer(BaseAnalyzer):
    """
    Детекция и классификация клеток крови на микроскопическом снимке.

    Возвращает AnalysisResponse с MicroscopyResult (подсчет клеток, bbox).
    """

    NAME = "Микроскопия — Клетки крови"

    def __init__(self, **_: Any) -> None:
        super().__init__(id="blood_cells", name=self.NAME, modality="microscopy")

    async def analyze(
        self,
        image: Image.Image,
        *,
        context: AnalysisContext,
        **_: Any,
    ) -> AnalysisResponse:
        request_id = context.request_id or str(uuid.uuid4())[:8]
        logger.info("[BloodAnalyzer] Старт анализа крови, request_id=%s", request_id)
        image_np = model_manager.preprocess_microscopy(image)

        raw_model = model_manager.get_model(Modality.microscopy)
        if raw_model is None:
            raise RuntimeError("Модель микроскопии не загружена")
        model = cast(MicroscopyModel, raw_model)

        _masks, cell_results = model.predict(image_np)

        overlay = image_np.copy()
        counts = CellCount()
        detections: list[CellDetection] = []
        confidences: list[float] = []

        for result_item in cell_results:
            cls_name = result_item["class"]
            conf = result_item["confidence"]
            slc = result_item["slice"]

            current = getattr(counts, cls_name, 0)
            setattr(counts, cls_name, current + 1)
            confidences.append(conf)

            y0, y1 = slc[0].start, slc[0].stop
            x0, x1 = slc[1].start, slc[1].stop

            detections.append(
                CellDetection(
                    cell_id=result_item["cell_id"],
                    class_name=cls_name,
                    confidence=conf,
                    bounding_box=BoundingBox(
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                        height=y1 - y0,
                    ),
                )
            )

            color = model.COLORS.get(cls_name, (200, 200, 200))
            cv2.rectangle(overlay, (x0, y0), (x1, y1), color, 2)
            label = f"{cls_name[:3]} {conf:.0%}"
            (text_w, text_h), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1,
            )
            cv2.rectangle(
                overlay,
                (x0, y0 - text_h - 6),
                (x0 + text_w + 4, y0),
                color,
                -1,
            )
            cv2.putText(
                overlay,
                label,
                (x0 + 2, y0 - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
            )

        class_counts = Counter(item["class"] for item in cell_results)
        legend_y = 20
        for cls_name, count in sorted(class_counts.items(), key=lambda item: -item[1]):
            color = model.COLORS.get(cls_name, (200, 200, 200))
            cv2.rectangle(overlay, (8, legend_y - 12), (22, legend_y + 2), color, -1)
            cv2.putText(
                overlay,
                f"{cls_name}: {count}",
                (28, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            legend_y += 22

        overlay_url = save_overlay(overlay, f"{request_id}_overlay.jpg")
        total_cells = len(cell_results)
        summary = _build_microscopy_summary(counts, total_cells)

        if counts.RBC > 0 and counts.WBC > 0:
            ratio_str = f"1:{counts.RBC // counts.WBC}"
        elif counts.WBC == 0:
            ratio_str = "WBC не обнаружены"
        else:
            ratio_str = "RBC не обнаружены"

        clinical_note = _make_clinical_note(counts)
        is_pathology = any(
            item.get("affects_diagnosis") and item.get("status") == "abnormal"
            for item in summary
        )
        avg_conf = round(float(np.mean(confidences)) if confidences else 0.0, 4)
        diagnosis_label = (
            "Недостаточно данных"
            if total_cells == 0
            else ("Отклонение выявлено" if is_pathology else "В пределах нормы")
        )
        logger.info(
            "[BloodAnalyzer] Итог request_id=%s: total=%s, RBC=%s, WBC=%s, Platelets=%s, pathology=%s",
            request_id,
            total_cells,
            counts.RBC,
            counts.WBC,
            counts.Platelets,
            is_pathology,
        )

        return AnalysisResponse(
            request_id=request_id,
            analyzer_id="blood_cells",
            modality=Modality.microscopy,
            diagnosis=DiagnosisResult(
                predicted_class=1 if is_pathology else 0,
                label=diagnosis_label,
                confidence=avg_conf,
                is_pathology=is_pathology,
            ),
            gradcam=None,
            microscopy=MicroscopyResult(
                overlay_url=overlay_url,
                cell_counts=counts,
                cell_detections=detections,
                total_cells=total_cells,
                wbc_rbc_ratio=ratio_str,
                clinical_note=clinical_note,
            ),
            extra={"microscopy_summary": summary},
            model_version=MicroscopyModel.VERSION,
        )
