"""Общие вспомогательные функции для сервисов админки."""

from __future__ import annotations

from datetime import datetime


def fmt_date(dt: datetime) -> str:
    """Приводит datetime к ISO-8601 строке с суффиксом Z."""
    return dt.isoformat() + "Z"
