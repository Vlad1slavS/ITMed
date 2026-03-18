"""
Роутер образовательного режима: оценка знаний студентов.
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.core.base import AnalysisContext, LandmarkPoint
from backend.core.registry import get_analyzer
from backend.db import models as db_models
from backend.db.database import SessionLocal, log_to_db
from backend.modules.hip_dysplasia.steps import classify_all_metrics
from backend.routers.routers_analysis import open_any_image
from backend.schema.schemas import Modality
from backend.service.dicom_age_service import (
    PatientAgeInfo,
    extract_patient_age_from_dicom,
    parse_patient_age_input,
)
from backend.service.educational_service import (
    compute_total_score,
    convert_floats,
    evaluate_points,
    evaluate_qualitative,
    simplify_diagnosis,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _landmarks_from_result_extra(result) -> dict[str, LandmarkPoint]:
    extra = getattr(result, "extra", None) or {}
    raw = extra.get("landmarks") if isinstance(extra, dict) else None
    if not isinstance(raw, dict):
        return {}

    parsed: dict[str, LandmarkPoint] = {}
    for key, data in raw.items():
        if not isinstance(data, dict):
            continue
        try:
            parsed[key] = LandmarkPoint(
                x_px=float(data["x_px"]),
                y_px=float(data["y_px"]),
                x_norm=float(data["x_norm"]),
                y_norm=float(data["y_norm"]),
                name=str(data.get("name", key)),
                label_ru=str(data.get("label_ru", key)),
            )
        except Exception:
            continue
    return parsed


@router.post("/evaluate", summary="Оценка образовательного задания")
async def evaluate(
    file: UploadFile = File(...),
    analyzer_id: str = Form(default="hip_dysplasia"),
    student_points: str = Form(...),
    student_qualitative: str = Form(...),
    student_diagnosis: str = Form(...),
    duration_seconds: int | None = Form(default=None),
    patient_age_value: str | None = Form(default=None),
    patient_age_unit: str | None = Form(default=None),
):
    logger.info(f"[Educational] Старт оценки задания analyzer_id={analyzer_id}")

    # 1. Загрузка изображения
    contents = await file.read()

    age_from_manual = PatientAgeInfo(age_months=None, display=None, source=None)
    age_from_dicom = PatientAgeInfo(age_months=None, display=None, source=None)
    try:
        age_from_manual = parse_patient_age_input(patient_age_value, patient_age_unit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if age_from_manual.age_months is None:
        age_from_dicom = extract_patient_age_from_dicom(contents)
    patient_age = (
        age_from_manual if age_from_manual.age_months is not None else age_from_dicom
    )
    logger.info(
        f"[Educational] Возраст пациента: months={patient_age.age_months}, source={patient_age.source}"
    )
    try:
        image = open_any_image(contents)
    except ValueError as e:
        logger.warning(f"[Educational] Ошибка открытия изображения: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Анализатор из registry
    try:
        analyzer = get_analyzer(analyzer_id)
    except KeyError as e:
        logger.warning(f"[Educational] Неизвестный analyzer_id={analyzer_id}")
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Запуск анализа (один раз) для метрик + overlay + landmarks (через extra)
    context = AnalysisContext(
        request_id=str(uuid.uuid4())[:8],
        modality=analyzer.modality,
        analyzer_id=analyzer_id,
        patient_age_months=patient_age.age_months,
        patient_age_source=patient_age.source,
    )
    modality = Modality(analyzer.modality or "xray")

    try:
        result = await analyzer.analyze(image=image, context=context, modality=modality)
    except Exception as e:
        logger.exception(f"[Educational] Ошибка analyze: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

    # 4. Пытаемся взять точки из результата, иначе fallback через get_landmarks
    correct_points = _landmarks_from_result_extra(result)
    if not correct_points:
        logger.info(
            "[Educational] Landmarks в extra не найдены, вызываем get_landmarks"
        )
        correct_points = await analyzer.get_landmarks(image)

    if not correct_points:
        raise HTTPException(
            status_code=400,
            detail=f"Анализатор {analyzer_id} не поддерживает образовательный режим",
        )

    # 5. Парсинг ответов студента
    try:
        student_pts = json.loads(student_points)
        student_qual = json.loads(student_qualitative)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка JSON: {str(e)}")

    # 6. Метрики из результата
    metrics_dict = {}
    if hasattr(result, "hip_dysplasia") and result.hip_dysplasia:
        for metric in result.hip_dysplasia.metrics:
            metrics_dict[metric.name] = metric.value

    # 7. Оценка трёх компонентов
    width, height = image.size

    pts_result = evaluate_points(correct_points, student_pts, width, height)
    qual_feedback = evaluate_qualitative(student_qual, metrics_dict, correct_points)
    overall = (
        result.hip_dysplasia.overall_diagnosis
        if (hasattr(result, "hip_dysplasia") and result.hip_dysplasia)
        else classify_all_metrics(metrics_dict, age_months=patient_age.age_months)
    )
    correct_diag = simplify_diagnosis(overall)
    diag_correct = student_diagnosis.lower() == correct_diag.lower()
    total = compute_total_score(pts_result["score"], qual_feedback, diag_correct)

    # 8. Сохраняем сессию в БД
    db = None
    try:
        db = SessionLocal()
        worst = [k for k, v in pts_result["points"].items() if v.get("grade") == "poor"]
        db.add(
            db_models.EduSession(
                analyzer_id=analyzer_id,
                total_score=total,
                points_score=pts_result["score"],
                qual_score=int(
                    round(
                        (
                            sum(1 for q in qual_feedback if q["is_correct"])
                            / len(qual_feedback)
                            * 100
                        )
                    )
                )
                if qual_feedback
                else None,
                diagnosis_correct=diag_correct,
                worst_points=worst,
                duration_seconds=duration_seconds or None,
            )
        )
        db.commit()
        log_to_db(
            "INFO",
            "/api/educational/evaluate",
            f"score={total} diagnosis_correct={diag_correct}",
        )
        logger.info(
            f"[Educational] Сессия сохранена: total={total}, points={pts_result['score']}, "
            f"diag_correct={diag_correct}"
        )
    except Exception as e:  # pragma: no cover
        logger.exception(f"[Educational] Ошибка записи сессии: {e}")
        log_to_db("ERROR", "/api/educational/evaluate", str(e))
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    # 9. Ответ
    logger.info(f"[Educational] Оценка завершена: total_score={total}")
    return convert_floats(
        {
            "total_score": total,
            "points_accuracy": pts_result,
            "qual_feedback": qual_feedback,
            "diagnosis": {
                "student": student_diagnosis,
                "is_correct": diag_correct,
                "full_description": overall,
            },
            "correct_metrics": metrics_dict,
            "correct_points": {
                k: {"x": float(v.x_norm), "y": float(v.y_norm), "label": v.label_ru}
                for k, v in correct_points.items()
            },
            "overlay_url": result.hip_dysplasia.overlay_url
            if (hasattr(result, "hip_dysplasia") and result.hip_dysplasia)
            else None,
            "patient_age": {
                "months": patient_age.age_months,
                "display": patient_age.display,
                "source": patient_age.source,
            },
        }
    )
