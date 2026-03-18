"""Сервис истории анализов и фильтрации для админ-панели."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.db.models import Analysis, HipMetrics
from backend.service.admin.common import fmt_date


logger = logging.getLogger(__name__)


def get_analyses_list(
    db: Session,
    *,
    limit: int,
    analyzer_id: Optional[str],
    is_pathology: Optional[bool],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> list[dict]:
    """Возвращает историю анализов с фильтрами."""
    logger.info(
        f"[Админ] Запрос анализов: limit={limit}, analyzer_id={analyzer_id}, "
        f"is_pathology={is_pathology}, date_from={date_from}, date_to={date_to}"
    )

    query = db.query(Analysis, HipMetrics).outerjoin(HipMetrics, HipMetrics.analysis_id == Analysis.id)
    if analyzer_id:
        query = query.filter(Analysis.analyzer_id == analyzer_id)
    if is_pathology is not None:
        query = query.filter(Analysis.is_pathology.is_(is_pathology))
    if date_from:
        query = query.filter(Analysis.created_at >= date_from)
    if date_to:
        query = query.filter(Analysis.created_at <= date_to)

    rows = query.order_by(Analysis.created_at.desc()).limit(limit).all()

    result: list[dict] = []
    for analysis, hip in rows:
        item = {
            "id": str(analysis.id),
            "created_at": fmt_date(analysis.created_at),
            "analyzer_id": analysis.analyzer_id,
            "modality": analysis.modality,
            "is_pathology": analysis.is_pathology,
            "diagnosis_label": analysis.diagnosis_label,
            "confidence": analysis.confidence,
            "processing_ms": analysis.processing_ms,
            "overlay_url": analysis.overlay_url,
            "model_version": analysis.model_version,
        }
        if hip:
            item["hip_metrics"] = {
                "ace_index_left": hip.ace_index_left,
                "ace_index_right": hip.ace_index_right,
                "wiberg_index_left": hip.wiberg_index_left,
                "wiberg_index_right": hip.wiberg_index_right,
                "ihdi_grade_left": hip.ihdi_grade_left,
                "ihdi_grade_right": hip.ihdi_grade_right,
                "tonnis_grade_left": hip.tonnis_grade_left,
                "tonnis_grade_right": hip.tonnis_grade_right,
                "overall_diagnosis": hip.overall_diagnosis,
            }
        result.append(item)

    return result
