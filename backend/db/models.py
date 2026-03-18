from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


def _uuid_str() -> str:
    return str(uuid4())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    analyzer_id = Column(String(50), nullable=False, index=True)
    modality = Column(String(20))
    is_pathology = Column(Boolean)
    diagnosis_label = Column(Text)
    confidence = Column(Float)
    overlay_url = Column(Text)  # путь к файлу на диске
    image_hash = Column(String(32), index=True)  # md5 для поиска дубликатов
    file_size_bytes = Column(Integer)
    processing_ms = Column(Integer)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    hip_metrics = relationship("HipMetrics", back_populates="analysis", uselist=False)


class HipMetrics(Base):
    __tablename__ = "hip_metrics"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), index=True)
    ace_index_left = Column(Float)
    ace_index_right = Column(Float)
    ihdi_grade_left = Column(String(3))
    h_left = Column(String(20))
    h_right = Column(String(20))
    d_left = Column(String(20))
    d_right = Column(String(20))
    ihdi_grade_right = Column(String(3))
    overall_diagnosis = Column(Text)

    analysis = relationship("Analysis", back_populates="hip_metrics")


class EduSession(Base):
    __tablename__ = "edu_sessions"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    analyzer_id = Column(String(50))
    total_score = Column(Integer)
    points_score = Column(Integer)
    qual_score = Column(Integer)
    diagnosis_correct = Column(Boolean)
    worst_points = Column(JSON)  # список ключей точек, где grade == "poor"
    duration_seconds = Column(Integer)  # сколько студент тратил
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    level = Column(String(10))  
    endpoint = Column(String(100))
    message = Column(Text)
    processing_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ConfigEntry(Base):
    __tablename__ = "config_entries"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(10), default="float")  # float/int/str/bool
    label_ru = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
