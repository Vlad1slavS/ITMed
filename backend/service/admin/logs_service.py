"""Сервис чтения системных логов для админ-панели."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.db.models import SystemLog
from backend.service.admin.common import fmt_date


logger = logging.getLogger(__name__)


def get_logs_list(
    db: Session,
    *,
    limit: int,
    level: Optional[str],
    endpoint: Optional[str],
) -> list[dict]:
    """Возвращает последние логи системы с фильтрацией."""
    logger.info(f"[Админ] Запрос логов: limit={limit}, level={level}, endpoint={endpoint}")

    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    if endpoint:
        query = query.filter(SystemLog.endpoint == endpoint)

    rows = query.order_by(SystemLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(row.id),
            "level": row.level,
            "endpoint": row.endpoint,
            "message": row.message,
            "processing_ms": row.processing_ms,
            "created_at": fmt_date(row.created_at),
        }
        for row in rows
    ]
