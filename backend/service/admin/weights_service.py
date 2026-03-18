"""Сервис загрузки и runtime-перезагрузки весов моделей."""

from __future__ import annotations

import logging
from pathlib import Path

import torch

from backend.app.config import settings
from backend.ml.model_manager import model_manager
from backend.ml.models import MicroscopyModel


logger = logging.getLogger(__name__)
ALLOWED_MODEL_TYPES = {"xray", "microscopy"}
ALLOWED_WEIGHT_EXTENSIONS = {".pth", ".pt"}


def resolve_weights_target_path(model_type: str) -> Path:
    """Возвращает путь весов для выбранного типа модели."""
    if model_type not in ALLOWED_MODEL_TYPES:
        raise ValueError(f"model_type должен быть одним из: {sorted(ALLOWED_MODEL_TYPES)}")
    return settings.XRAY_MODEL_PATH if model_type == "xray" else settings.MICROSCOPY_MODEL_PATH


def validate_weights_file(filename: str, model_type: str) -> Path:
    """Проверяет расширение файла и возвращает целевой путь сохранения."""
    target_path = resolve_weights_target_path(model_type)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_WEIGHT_EXTENSIONS:
        raise ValueError("Только .pth или .pt файлы")
    return target_path


def backup_weights_if_exists(target_path: Path, uploaded_ext: str) -> Path | None:
    """Создает backup существующих весов перед заменой."""
    if not target_path.exists():
        return None
    backup_path = target_path.with_suffix(f".backup{uploaded_ext}")
    target_path.rename(backup_path)
    logger.info(f"[Weights] Старые веса сохранены как {backup_path.name}")
    return backup_path


def reload_model_by_type(model_type: str, target_path: Path) -> None:
    """Перезагружает модель в памяти после обновления весов."""
    if model_type == "xray":
        if model_manager.xray_model is None:
            raise RuntimeError("Рентген модель не инициализирована")
        state = torch.load(target_path, map_location=model_manager.device)
        model_manager.xray_model.load_state_dict(state)
        model_manager.xray_model.eval()
        model_manager.xray_weights_loaded = True
        model_manager._init_xray_gradcam()
        logger.info("[Weights] Рентген модель перезагружена успешно")
        return

    model_manager.microscopy_model = MicroscopyModel(str(target_path))
    model_manager.microscopy_weights_loaded = True
    logger.info("[Weights] Микроскопия модель перезагружена успешно")


def upload_and_reload_weights(file_name: str, content: bytes, model_type: str) -> dict:
    """Сохраняет веса и перезагружает модель, возвращая результат операции."""
    target_path = validate_weights_file(file_name, model_type)
    ext = Path(file_name).suffix.lower()
    backup_weights_if_exists(target_path, ext)
    target_path.write_bytes(content)
    logger.info(f"[Weights] Загружены новые веса: {target_path}, size={len(content)}")
    reload_model_by_type(model_type, target_path)
    return {
        "status": "ok",
        "model_type": model_type,
        "filename": file_name,
        "size_mb": round(len(content) / 1024 / 1024, 2),
        "reloaded": True,
    }


def get_weights_status() -> dict:
    """Возвращает состояние весов и загрузки моделей."""
    xray_backup = settings.XRAY_MODEL_PATH.with_suffix(".backup.pth")
    micro_backup = settings.MICROSCOPY_MODEL_PATH.with_suffix(".backup.pt")
    return {
        "xray": {
            "loaded": bool(model_manager.xray_weights_loaded),
            "path": str(settings.XRAY_MODEL_PATH),
            "exists": settings.XRAY_MODEL_PATH.exists(),
            "size_mb": (
                round(settings.XRAY_MODEL_PATH.stat().st_size / 1024 / 1024, 2)
                if settings.XRAY_MODEL_PATH.exists()
                else 0
            ),
            "backup_exists": xray_backup.exists(),
        },
        "microscopy": {
            "loaded": bool(model_manager.microscopy_weights_loaded),
            "path": str(settings.MICROSCOPY_MODEL_PATH),
            "exists": settings.MICROSCOPY_MODEL_PATH.exists(),
            "size_mb": (
                round(settings.MICROSCOPY_MODEL_PATH.stat().st_size / 1024 / 1024, 2)
                if settings.MICROSCOPY_MODEL_PATH.exists()
                else 0
            ),
            "backup_exists": micro_backup.exists(),
        },
    }
