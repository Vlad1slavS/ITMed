"""
Роутер анализа: тонкий маршрутизатор между HTTP и анализаторами.
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
import uuid
from datetime import datetime

import cv2
import numpy as np
import pydicom
from PIL import Image
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from backend.app.config import settings
from backend.core.base import AnalysisContext
from backend.core.registry import get_analyzer
from backend.db import models as db_models
from backend.db.database import SessionLocal, log_to_db
from backend.modules.hip_dysplasia.steps import (
    classify_acetabular_index,
    classify_ihdi,
)
from backend.schema.schemas import (
    AnalysisResponse,
    DiagnosisResult,
    HipDysplasiaMetric,
    HipDysplasiaResult,
    Modality,
)
from backend.service.dicom_age_service import (
    PatientAgeInfo,
    extract_patient_age_from_dicom,
    parse_patient_age_input,
)
from backend.service.report_service import generate_pdf_report

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "application/dicom",
    "application/octet-stream",
}

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024

# Кратковременный in-memory cache для генерации PDF
_results_cache: dict[str, dict] = {}


def is_dicom(data: bytes) -> bool:
    return len(data) > 132 and data[128:132] == b"DICM"


def open_any_image(contents: bytes) -> Image.Image:
    # Способ 1: проверяем magic bytes
    if is_dicom(contents):
        ds = pydicom.dcmread(io.BytesIO(contents))
        arr = ds.pixel_array.astype(np.float32)

        # Window center/width из метаданных
        wc = getattr(ds, "WindowCenter", None)
        ww = getattr(ds, "WindowWidth", None)
        if wc is not None and ww is not None:
            try:
                wc = float(wc) if not hasattr(wc, "__iter__") else float(list(wc)[0])
                ww = float(ww) if not hasattr(ww, "__iter__") else float(list(ww)[0])
                arr = np.clip(arr, wc - ww / 2, wc + ww / 2)
            except Exception:
                pass

        arr_min, arr_max = arr.min(), arr.max()
        if arr_max > arr_min:
            arr = (arr - arr_min) / (arr_max - arr_min) * 255.0
        arr = arr.astype(np.uint8)

        if arr.ndim == 2:
            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(arr)

    # Способ 2: пробуем PIL
    try:
        img = Image.open(io.BytesIO(contents))
        img.load()
        return img
    except Exception:
        pass

    # Способ 3: DICOM без префикса DICM
    try:
        ds = pydicom.dcmread(io.BytesIO(contents), force=True)
        arr = ds.pixel_array.astype(np.float32)

        # Window center/width из метаданных
        wc = getattr(ds, "WindowCenter", None)
        ww = getattr(ds, "WindowWidth", None)
        if wc is not None and ww is not None:
            try:
                wc = float(wc) if not hasattr(wc, "__iter__") else float(list(wc)[0])
                ww = float(ww) if not hasattr(ww, "__iter__") else float(list(ww)[0])
                arr = np.clip(arr, wc - ww / 2, wc + ww / 2)
            except Exception:
                pass

        arr_min, arr_max = arr.min(), arr.max()
        if arr_max > arr_min:
            arr = (arr - arr_min) / (arr_max - arr_min) * 255.0
        else:
            arr = np.zeros_like(arr)
        arr = arr.astype(np.uint8)

        if arr.ndim == 2:
            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(arr)
    except Exception:
        pass

    raise ValueError("Неподдерживаемый формат файла")


@router.post(
    "/",
    summary="Анализ медицинского снимка",
    description="Универсальный эндпоинт анализа. Выбор анализатора через analyzer_id.",
)
async def analyze(
        file: UploadFile = File(...),
        analyzer_id: str = Form(default="xray_pneumonia"),
        patient_age_value: str | None = Form(default=None),
        patient_age_unit: str | None = Form(default=None),
):
    logger.info(
        f"[Analysis] Новый запрос analyzer_id={analyzer_id}, file={file.filename}"
    )
    contents = await file.read()

    # Возраст: ручной ввод имеет приоритет над DICOM метаданными
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
        f"[Analysis] Возраст пациента: months={patient_age.age_months}, source={patient_age.source}"
    )

    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"[Analysis] Файл слишком большой: size={len(contents)}")
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимум: {settings.MAX_FILE_SIZE_MB} МБ",
        )

    try:
        image = open_any_image(contents)
    except ValueError as e:
        logger.warning(f"[Analysis] Неверный формат файла: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    try:
        analyzer = get_analyzer(analyzer_id)
    except KeyError as e:
        logger.warning(f"[Analysis] Не найден analyzer_id={analyzer_id}")
        raise HTTPException(status_code=400, detail=str(e))

    hash_payload = contents + f"|age={patient_age.age_months or 'na'}".encode("utf-8")
    image_hash = hashlib.md5(hash_payload).hexdigest()

    db = SessionLocal()
    try:
        existing = (
            db.query(db_models.Analysis)
            .filter(db_models.Analysis.image_hash == image_hash)
            .filter(db_models.Analysis.analyzer_id == analyzer_id)
            .first()
        )
        if existing:
            logger.info(
                f"[Analysis] Cache hit из БД analyzer_id={analyzer_id}, hash={image_hash}"
            )
            log_to_db("INFO", "/api/analysis/", f"cache_hit analyzer={analyzer_id}")
            return build_response_from_db(existing)
    finally:
        db.close()

    context = AnalysisContext(
        request_id=str(uuid.uuid4())[:8],
        modality=analyzer.modality,
        analyzer_id=analyzer_id,
        patient_age_months=patient_age.age_months,
        patient_age_source=patient_age.source,
    )

    modality = Modality(analyzer.modality) if analyzer.modality else Modality.xray

    t0 = time.time()
    try:
        result = await analyzer.analyze(
            image=image,
            context=context,
            modality=modality,
            dicom_contents=contents if is_dicom(contents) else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Analysis] Ошибка анализа analyzer={analyzer_id}: {e}")
        log_to_db("ERROR", "/api/analysis/", str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

    processing_ms = int((time.time() - t0) * 1000)

    # Сохраняем результат в БД
    db = None
    try:
        db = SessionLocal()
        record = db_models.Analysis(
            analyzer_id=result.analyzer_id,
            modality=result.modality.value,
            is_pathology=result.diagnosis.is_pathology,
            diagnosis_label=result.diagnosis.label,
            confidence=result.diagnosis.confidence,
            overlay_url=(
                    (result.gradcam and result.gradcam.overlay_url)
                    or (result.microscopy and result.microscopy.overlay_url)
                    or (result.hip_dysplasia and result.hip_dysplasia.overlay_url)
            ),
            image_hash=image_hash,
            file_size_bytes=len(contents),
            processing_ms=processing_ms,
            model_version=result.model_version,
        )
        db.add(record)
        db.flush()

        if (
                getattr(result, "hip_dysplasia", None)
                and result.hip_dysplasia.metrics
                and result.analyzer_id == "hip_dysplasia"
        ):
            metrics_map = {m.name: m.value for m in result.hip_dysplasia.metrics}
            hip = db_models.HipMetrics(
                analysis_id=record.id,
                ace_index_left=metrics_map.get("ace_index_left"),
                ace_index_right=metrics_map.get("ace_index_right"),
                ihdi_grade_left=metrics_map.get("ihdi_left"),
                ihdi_grade_right=metrics_map.get("ihdi_right"),
                h_left=metrics_map.get("h_left"),
                h_right=metrics_map.get("h_right"),
                d_left=metrics_map.get("d_left"),
                d_right=metrics_map.get("d_right"),
                overall_diagnosis=getattr(
                    result.hip_dysplasia, "overall_diagnosis", None
                ),
            )
            db.add(hip)

        db.commit()
        logger.info(
            f"[Analysis] Результат сохранен в БД analyzer_id={analyzer_id}, processing_ms={processing_ms}"
        )
        log_to_db(
            "INFO",
            "/api/analysis/",
            f"analyzer={analyzer_id} processing_ms={processing_ms}",
            processing_ms=processing_ms,
        )
    except Exception as e:  # pragma: no cover
        logger.exception(f"[Analysis] Ошибка записи результата в БД: {e}")
        log_to_db("ERROR", "/api/analysis/", str(e))
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

    return result


@router.get(
    "/results/{filename}",
    summary="Получить изображение результата",
    description="Возвращает overlay/heatmap из backend/overlays/",
)
async def get_result_image(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Недопустимое имя файла")

    file_path = settings.RESULTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    logger.info(f"[Analysis] Выдача result image: {filename}")
    return FileResponse(str(file_path), media_type="image/jpeg")


@router.get("/{request_id}/report", summary="Скачать PDF-отчёт")
async def get_report(request_id: str):
    logger.info(f"[Analysis] Запрос PDF отчета request_id={request_id}")
    data = _results_cache.get(request_id)
    if not data:
        logger.warning(
            f"[Analysis] PDF не найден в in-memory cache request_id={request_id}"
        )
        raise HTTPException(
            status_code=404,
            detail="Результат не найден. Возможно, сервер был перезапущен.",
        )

    pdf_buffer = generate_pdf_report(data)
    filename = f"ITMed_report_{request_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def build_response_from_db(record: db_models.Analysis) -> AnalysisResponse:
    """
    Восстанавливает AnalysisResponse из записей в БД.
    Используется для cache-hit по image_hash.
    """
    hip: db_models.HipMetrics | None = record.hip_metrics

    hip_result: HipDysplasiaResult | None = None
    if hip is not None and record.analyzer_id in {"hip_dysplasia", "hip_dysplasia_yolo"}:
        metrics: list[HipDysplasiaMetric] = []

        # Ацетабулярный индекс
        for field, label_ru, side in [
            ("ace_index_left", "Ацетабулярный индекс (лев)", "left"),
            ("ace_index_right", "Ацетабулярный индекс (пр)", "right"),
        ]:
            val = getattr(hip, field)
            if val is None:
                continue
            classification, color = classify_acetabular_index(float(val))
            metrics.append(HipDysplasiaMetric(
                name=field, name_ru=label_ru, value=float(val),
                side=side, classification=classification, color=color,
            ))

        # IHDI — строка "I"/"II"/... из БД
        for field, label_ru, side in [
            ("ihdi_grade_left", "IHDI (лев)", "left"),
            ("ihdi_grade_right", "IHDI (пр)", "right"),
        ]:
            val = getattr(hip, field)
            if val is None:
                continue
            classification, color = classify_ihdi(val)
            metrics.append(HipDysplasiaMetric(
                name=field, name_ru=label_ru, value=val,
                side=side, classification=classification, color=color,
            ))

        for field, label_ru, side in [
            ("h_left", "Верт. смещение головки (лев)", "left"),
            ("h_right", "Верт. смещение головки (пр)", "right"),
            ("d_left", "Гориз. смещение (лев)", "left"),
            ("d_right", "Гориз. смещение (пр)", "right"),
        ]:
            val = getattr(hip, field)
            if val is None:
                continue
            metrics.append(HipDysplasiaMetric(
                name=field, name_ru=label_ru, value=val,
                side=side, classification=None, color=None,
            ))

        hip_result = HipDysplasiaResult(
            overlay_url=record.overlay_url or "",
            heatmap_url=None,
            metrics=metrics,
            overall_diagnosis=hip.overall_diagnosis or "",
            educational_info=None,
        )

    raw_modality = record.modality or "xray"
    if "." in raw_modality:
        raw_modality = raw_modality.split(".")[-1]
    modality = Modality(raw_modality)

    response = AnalysisResponse(
        request_id=str(record.id),
        analyzer_id=record.analyzer_id,
        modality=modality,
        diagnosis=DiagnosisResult(
            predicted_class=1 if record.is_pathology else 0,
            label=record.diagnosis_label or "",
            confidence=float(record.confidence or 0.0),
            is_pathology=bool(record.is_pathology),
        ),
        gradcam=None,
        microscopy=None,
        hip_dysplasia=hip_result,
        model_version=record.model_version or "",
    )
    logger.info(f"[Analysis] Ответ восстановлен из БД analysis_id={record.id}")
    return response  # Добавляем возраст в extra для трассировки (если анализатор не заполнил сам)
