from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings


logger = logging.getLogger(__name__)

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine_kwargs = {
    "pool_pre_ping": True,
}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_to_db(level: str, endpoint: str, message: str, processing_ms: int = 0):
    """
    Неблокирующее логирование в таблицу SystemLog.
    Ошибки записи в лог не должны ломать основной запрос.
    """
    db = None
    try:
        from backend.db.models import SystemLog

        db = SessionLocal()
        db.add(
            SystemLog(
                level=level,
                endpoint=endpoint,
                message=message,
                processing_ms=processing_ms,
            )
        )
        db.commit()
    except Exception as e:
        logger.warning(
            f"[БД-логгер] Не удалось записать лог в БД: level={level}, endpoint={endpoint}, error={e}"
        )
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
