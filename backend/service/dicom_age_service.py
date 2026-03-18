"""
Сервис извлечения и нормализации возраста пациента.

- парсинг возраста из DICOM-метаданных;
- нормализация возраста из формы (годы/месяцы);
- единый формат возраста в месяцах для аналитики.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime

import pydicom

logger = logging.getLogger(__name__)


@dataclass
class PatientAgeInfo:
    """Нормализованный возраст пациента."""

    age_months: int | None
    display: str | None
    source: str | None


def _format_age(age_months: int) -> str:
    years = age_months // 12
    months = age_months % 12
    if years > 0 and months > 0:
        return f"{years} г {months} мес"
    if years > 0:
        return f"{years} г"
    return f"{months} мес"


def _as_to_months(raw_age: str | None) -> int | None:
    """
    DICOM PatientAge (0010,1010), формат AS: nnnD/W/M/Y.
    Примеры: 006M, 002Y.
    """
    if not raw_age:
        return None

    val = str(raw_age).strip().upper()
    match = re.fullmatch(r"(\d{1,3})([DWMY])", val)
    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    if unit == "D":
        return max(0, round(number / 30))
    if unit == "W":
        return max(0, round(number / 4.345))
    if unit == "M":
        return number
    return number * 12


def _date_str_to_date(raw_date: str | None) -> datetime | None:
    if not raw_date:
        return None
    try:
        # DICOM DA формат YYYYMMDD
        return datetime.strptime(str(raw_date), "%Y%m%d")
    except Exception:
        return None


def _calc_months_from_dates(birth_date: str | None, study_date: str | None) -> int | None:
    birth = _date_str_to_date(birth_date)
    study = _date_str_to_date(study_date)
    if birth is None or study is None or study < birth:
        return None

    months = (study.year - birth.year) * 12 + (study.month - birth.month)
    if study.day < birth.day:
        months -= 1
    return max(0, months)


def extract_patient_age_from_dicom(contents: bytes) -> PatientAgeInfo:
    """
    Извлекает возраст из DICOM:
    1) PatientAge (0010,1010)
    2) fallback: PatientBirthDate + StudyDate/SeriesDate/AcquisitionDate/ContentDate
    """
    try:
        ds = pydicom.dcmread(io.BytesIO(contents), force=True, stop_before_pixels=True)
    except Exception as exc:
        logger.debug(f"[DicomAge] Не DICOM или ошибка чтения метаданных: {exc}")
        return PatientAgeInfo(age_months=None, display=None, source=None)

    # 1) PatientAge
    age_months = _as_to_months(getattr(ds, "PatientAge", None))
    if age_months is not None:
        display = _format_age(age_months)
        logger.info(f"[DicomAge] Возраст прочитан из PatientAge: {display}")
        return PatientAgeInfo(
            age_months=age_months,
            display=display,
            source="PatientAge",
        )

    # 2) PatientBirthDate + date исследования
    study_date = (
        getattr(ds, "StudyDate", None)
        or getattr(ds, "SeriesDate", None)
        or getattr(ds, "AcquisitionDate", None)
        or getattr(ds, "ContentDate", None)
    )
    age_months = _calc_months_from_dates(
        getattr(ds, "PatientBirthDate", None),
        study_date,
    )
    if age_months is not None:
        display = _format_age(age_months)
        logger.info(f"[DicomAge] Возраст вычислен по датам DICOM: {display}")
        return PatientAgeInfo(
            age_months=age_months,
            display=display,
            source="PatientBirthDate+StudyDate",
        )

    logger.info("[DicomAge] Возраст пациента в DICOM не найден")
    return PatientAgeInfo(age_months=None, display=None, source=None)


def parse_patient_age_input(age_value: str | None, age_unit: str | None) -> PatientAgeInfo:
    """
    Нормализует ручной ввод возраста врача.
    Поддерживает возраст в годах и месяцах.
    """
    if age_value is None:
        return PatientAgeInfo(age_months=None, display=None, source=None)

    raw = str(age_value).strip().replace(",", ".")
    if raw == "":
        return PatientAgeInfo(age_months=None, display=None, source=None)

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("Возраст должен быть числом") from exc

    if value < 0:
        raise ValueError("Возраст не может быть отрицательным")

    unit = (age_unit or "years").strip().lower()
    if unit in {"years", "year", "y", "годы", "год", "лет"}:
        age_months = int(round(value * 12))
        source = "manual_years"
    elif unit in {"months", "month", "m", "месяцы", "месяц", "мес"}:
        age_months = int(round(value))
        source = "manual_months"
    else:
        raise ValueError("Единица возраста должна быть years или months")

    return PatientAgeInfo(
        age_months=age_months,
        display=_format_age(age_months),
        source=source,
    )
