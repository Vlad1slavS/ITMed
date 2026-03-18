"""Сервис редактируемых конфигов админки: чтение, обновление, сброс."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.config import Settings, settings
from backend.db.database import log_to_db
from backend.db.models import ConfigEntry


logger = logging.getLogger(__name__)
default_settings = Settings()


EDITABLE_CONFIGS = {
    "HIP_CONFIDENCE_PATHOLOGY": {
        "label_ru": "Уверенность при патологии (ТБС)",
        "description": "Значение confidence когда модель определяет патологию. 0.0 - 1.0",
        "value_type": "float",
        "min": 0.5,
        "max": 1.0,
    },
    "HIP_CONFIDENCE_NORMAL": {
        "label_ru": "Уверенность при норме (ТБС)",
        "description": "Значение confidence когда патологий не обнаружено. 0.0 - 1.0",
        "value_type": "float",
        "min": 0.5,
        "max": 1.0,
    },
    "XRAY_ADVANCED_THRESHOLD": {
        "label_ru": "Порог обнаружения патологии (DenseNet)",
        "description": "Минимальная вероятность для считывания как патология. 0.0 - 1.0",
        "value_type": "float",
        "min": 0.3,
        "max": 0.9,
    },
    "EDU_POINTS_EXCELLENT_PX": {
        "label_ru": "Порог отличной точности (пикселей)",
        "description": "Расстояние в пикселях для оценки Отлично",
        "value_type": "int",
        "min": 5,
        "max": 50,
    },
    "EDU_POINTS_GOOD_PX": {
        "label_ru": "Порог хорошей точности (пикселей)",
        "description": "Расстояние в пикселях для оценки Хорошо",
        "value_type": "int",
        "min": 20,
        "max": 100,
    },
    "EDU_WEIGHT_POINTS": {
        "label_ru": "Вес компонента точек (%)",
        "description": "Доля баллов за расстановку точек в итоговом балле",
        "value_type": "float",
        "min": 0.1,
        "max": 0.8,
    },
    "EDU_WEIGHT_QUAL": {
        "label_ru": "Вес качественных признаков (%)",
        "description": "Доля баллов за качественные признаки",
        "value_type": "float",
        "min": 0.1,
        "max": 0.8,
    },
    "EDU_WEIGHT_DIAGNOSIS": {
        "label_ru": "Вес диагноза (%)",
        "description": "Доля баллов за правильный диагноз",
        "value_type": "float",
        "min": 0.1,
        "max": 0.8,
    },
    "MAX_FILE_SIZE_MB": {
        "label_ru": "Максимальный размер файла (МБ)",
        "description": "Максимальный размер загружаемого снимка",
        "value_type": "int",
        "min": 5,
        "max": 100,
    },
    "IMAGE_SIZE": {
        "label_ru": "Размер изображения для модели (пикселей)",
        "description": "Изображение будет масштабировано до этого размера",
        "value_type": "int",
        "min": 128,
        "max": 512,
    },
}


def parse_typed_value(raw_value: Any, value_type: str) -> Any:
    """Преобразует входное значение к требуемому типу."""
    if value_type == "float":
        return float(raw_value)
    if value_type == "int":
        return int(raw_value)
    if value_type == "bool":
        if isinstance(raw_value, bool):
            return raw_value
        return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}
    return str(raw_value)


def get_config_entries(db: Session) -> list[dict]:
    """Возвращает список редактируемых конфигов с текущими значениями."""
    logger.info("[Админ] Запрос списка редактируемых конфигов")
    saved_entries = db.query(ConfigEntry).all()
    saved_by_key = {entry.key: entry for entry in saved_entries}

    result: list[dict] = []
    for key, meta in EDITABLE_CONFIGS.items():
        if key in saved_by_key:
            entry = saved_by_key[key]
            current_value = parse_typed_value(entry.value, entry.value_type)
        else:
            current_value = getattr(settings, key)

        result.append(
            {
                "key": key,
                "label_ru": meta["label_ru"],
                "description": meta["description"],
                "value_type": meta["value_type"],
                "min": meta["min"],
                "max": meta["max"],
                "current_value": current_value,
            }
        )
    return result


def update_config_entry(db: Session, key: str, raw_value: Any) -> dict:
    """Обновляет значение конфига в БД и runtime settings."""
    logger.info(f"[Админ] Запрос обновления конфига key={key}, value={raw_value}")
    if key not in EDITABLE_CONFIGS:
        raise KeyError(f"Ключ {key} не входит в редактируемые")

    meta = EDITABLE_CONFIGS[key]
    value_type = meta["value_type"]

    try:
        typed_value = parse_typed_value(raw_value, value_type)
    except Exception as e:
        raise ValueError(f"Не удалось привести значение к типу {value_type}") from e

    if value_type in {"float", "int"}:
        min_v = float(meta["min"])
        max_v = float(meta["max"])
        current = float(typed_value)
        if current < min_v or current > max_v:
            raise ValueError(f"Значение вне диапазона [{meta['min']}, {meta['max']}]")

    entry = db.query(ConfigEntry).filter(ConfigEntry.key == key).first()
    if entry is None:
        entry = ConfigEntry(
            key=key,
            value=str(typed_value),
            value_type=value_type,
            label_ru=meta["label_ru"],
            description=meta["description"],
        )
        db.add(entry)
    else:
        entry.value = str(typed_value)
        entry.value_type = value_type
        entry.label_ru = meta["label_ru"]
        entry.description = meta["description"]
        entry.updated_at = datetime.utcnow()

    setattr(settings, key, typed_value)
    db.commit()
    log_to_db("INFO", "/api/admin/config", f"config_update key={key} value={typed_value}")
    return {"status": "ok", "key": key, "current_value": typed_value}


def reset_config_entry(db: Session, key: str) -> dict:
    """Сбрасывает конфиг к значению по умолчанию из Settings."""
    logger.info(f"[Админ] Запрос сброса конфига key={key}")
    if key not in EDITABLE_CONFIGS:
        raise KeyError(f"Ключ {key} не входит в редактируемые")

    db.query(ConfigEntry).filter(ConfigEntry.key == key).delete()
    default_value = getattr(default_settings, key)
    setattr(settings, key, default_value)
    db.commit()
    log_to_db("INFO", "/api/admin/config/reset", f"config_reset key={key}")
    return {"status": "ok", "key": key, "current_value": default_value}
