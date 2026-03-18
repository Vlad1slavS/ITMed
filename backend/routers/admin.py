from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db, log_to_db
from backend.service.admin.analyses_service import get_analyses_list
from backend.service.admin.config_service import get_config_entries, reset_config_entry, update_config_entry
from backend.service.admin.logs_service import get_logs_list
from backend.service.admin.plugin_service import get_plugins_snapshot, remove_plugin_by_id, upload_plugin_file
from backend.service.admin.stats_service import get_aggregated_stats
from backend.service.admin.weights_service import get_weights_status, upload_and_reload_weights


router = APIRouter()
logger = logging.getLogger(__name__)


class ConfigUpdateRequest(BaseModel):
    value: str | int | float | bool


@router.get("/config")
def get_config(db: Session = Depends(get_db)) -> list[dict]:
    return get_config_entries(db)


@router.put("/config/{key}")
def update_config(
    key: str,
    payload: ConfigUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return update_config_entry(db, key, payload.value)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0] if e.args else str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/reset/{key}")
def reset_config(key: str, db: Session = Depends(get_db)) -> dict:
    try:
        return reset_config_entry(db, key)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0] if e.args else str(e))


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    return get_aggregated_stats(db)


@router.get("/logs")
def get_logs(
    limit: int = Query(50, ge=1, le=500),
    level: Optional[str] = Query(None),
    endpoint: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_logs_list(db, limit=limit, level=level, endpoint=endpoint)


@router.get("/analyses")
def get_analyses(
    limit: int = Query(20, ge=1, le=200),
    analyzer_id: Optional[str] = Query(None),
    is_pathology: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_analyses_list(
        db,
        limit=limit,
        analyzer_id=analyzer_id,
        is_pathology=is_pathology,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/plugins")
async def list_plugins() -> dict:
    logger.info("[Админ] Запрос списка плагинов")
    return get_plugins_snapshot()


@router.post("/plugins/upload")
async def upload_plugin(file: UploadFile = File(...)) -> dict:
    file_name = file.filename or "plugin.py"
    logger.info(f"[Админ] Загрузка плагина: {file_name}")
    content = await file.read()
    try:
        registered, all_analyzers = upload_plugin_file(file_name, content)
    except ValueError as e:
        logger.warning(f"[Админ] Некорректный файл плагина {file_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.warning(f"[Админ] Ошибка регистрации плагина {file_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Админ] Ошибка загрузки плагина {file_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка загрузки: {e}")

    log_to_db("INFO", "/api/admin/plugins/upload", f"plugin={file_name} registered={registered}")
    return {"status": "ok", "registered": registered, "all_analyzers": all_analyzers}


@router.delete("/plugins/{analyzer_id}")
async def remove_plugin(analyzer_id: str) -> dict:
    logger.info(f"[Админ] Отключение плагина analyzer_id={analyzer_id}")
    removed = remove_plugin_by_id(analyzer_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Анализатор {analyzer_id} не найден")
    log_to_db("INFO", "/api/admin/plugins", f"removed={analyzer_id}")
    return {"status": "ok", "removed": analyzer_id}


@router.post("/weights/upload")
async def upload_weights(
    file: UploadFile = File(...),
    model_type: str = Form(...),
) -> dict:
    file_name = file.filename or "weights.pth"
    logger.info(f"[Админ] Загрузка весов: model_type={model_type}, file={file_name}")
    content = await file.read()
    try:
        result = upload_and_reload_weights(file_name, content, model_type)
    except ValueError as e:
        logger.warning(f"[Админ] Некорректная загрузка весов: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Админ] Ошибка перезагрузки модели после загрузки весов: {e}")
        log_to_db("ERROR", "/api/admin/weights/upload", str(e))
        raise HTTPException(status_code=500, detail=f"Веса сохранены но модель не перезагрузилась: {e}")

    log_to_db(
        "INFO",
        "/api/admin/weights/upload",
        f"model_type={model_type} file={file_name} size={len(content)}",
    )
    return result


@router.get("/weights/status")
async def weights_status() -> dict:
    logger.info("[Админ] Запрос статуса весов")
    return get_weights_status()
