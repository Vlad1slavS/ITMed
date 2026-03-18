"""Сервис агрегированной статистики для админ-панели."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.db.models import Analysis, EduSession, HipMetrics
from backend.service.educational_service import simplify_diagnosis


logger = logging.getLogger(__name__)


def get_aggregated_stats(db: Session) -> dict:
    """Собирает агрегированную статистику по анализам и образовательному режиму."""
    logger.info("[Админ] Запрошена агрегированная статистика")

    total = db.query(func.count(Analysis.id)).scalar() or 0
    today = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.created_at >= datetime.utcnow().date())
        .scalar()
        or 0
    )
    week = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.created_at >= datetime.utcnow() - timedelta(days=7))
        .scalar()
        or 0
    )

    pathology_count = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.is_pathology.is_(True))
        .scalar()
        or 0
    )
    pathology_rate = (pathology_count * 100.0 / total) if total else 0.0
    avg_processing_ms = db.query(func.avg(Analysis.processing_ms)).scalar() or 0.0

    by_analyzer_rows = (
        db.query(
            Analysis.analyzer_id,
            func.count(Analysis.id).label("count"),
            func.avg(Analysis.confidence).label("avg_confidence"),
            func.avg(Analysis.processing_ms).label("avg_processing_ms"),
            (
                func.sum(case((Analysis.is_pathology.is_(True), 1), else_=0))
                * 100.0
                / func.count(Analysis.id)
            ).label("pathology_rate"),
        )
        .group_by(Analysis.analyzer_id)
        .all()
    )
    by_analyzer = [
        {
            "analyzer_id": row.analyzer_id,
            "count": int(row.count or 0),
            "avg_confidence": float(row.avg_confidence or 0.0),
            "avg_processing_ms": float(row.avg_processing_ms or 0.0),
            "pathology_rate": float(row.pathology_rate or 0.0),
        }
        for row in by_analyzer_rows
    ]

    hip_avg = db.query(func.avg(HipMetrics.ace_index_left), func.avg(HipMetrics.ace_index_right)).first()
    hip_avg_ace_left = float(hip_avg[0] or 0.0) if hip_avg else 0.0
    hip_avg_ace_right = float(hip_avg[1] or 0.0) if hip_avg else 0.0

    hip_diag_rows = (
        db.query(HipMetrics.overall_diagnosis)
        .filter(HipMetrics.overall_diagnosis.isnot(None))
        .all()
    )
    hip_diag_counts = {"норма": 0, "предвывих": 0, "подвывих": 0, "вывих": 0}
    for (text,) in hip_diag_rows:
        label = simplify_diagnosis(text or "")
        if label in hip_diag_counts:
            hip_diag_counts[label] += 1

    edu_total = db.query(func.count(EduSession.id)).scalar() or 0
    edu_today = (
        db.query(func.count(EduSession.id))
        .filter(EduSession.created_at >= datetime.utcnow().date())
        .scalar()
        or 0
    )
    edu_avg = db.query(func.avg(EduSession.total_score)).scalar() or 0.0
    edu_best = db.query(func.max(EduSession.total_score)).scalar() or 0
    edu_diag = (
        db.query(
            func.avg(
                case(
                    (EduSession.diagnosis_correct.is_(True), 100),
                    else_=0,
                )
            )
        ).scalar()
        or 0.0
    )

    counter: Counter[str] = Counter()
    sessions = (
        db.query(EduSession.worst_points)
        .filter(EduSession.worst_points.isnot(None))
        .all()
    )
    for (points,) in sessions:
        if isinstance(points, list):
            for point in points:
                if isinstance(point, str):
                    counter[point] += 1
    edu_worst_points = [point for point, _ in counter.most_common(3)]

    return {
        "total_analyses": int(total),
        "analyses_today": int(today),
        "analyses_week": int(week),
        "pathology_rate": float(pathology_rate),
        "by_analyzer": by_analyzer,
        "hip_diagnoses": hip_diag_counts,
        "hip_avg_ace_left": hip_avg_ace_left,
        "hip_avg_ace_right": hip_avg_ace_right,
        "edu_sessions_total": int(edu_total),
        "edu_sessions_today": int(edu_today),
        "edu_avg_score": float(edu_avg),
        "edu_best_score": int(edu_best or 0),
        "edu_worst_points": edu_worst_points,
        "edu_diagnosis_accuracy": float(edu_diag),
        "avg_processing_ms": float(avg_processing_ms),
    }
