"""
Сервис извлечения Pixel Spacing из DICOM-метаданных.

Single Responsibility: только чтение и нормализация PixelSpacing/ImagerPixelSpacing.
Конвертация пиксельных расстояний в мм — здесь же.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import pydicom

logger = logging.getLogger(__name__)


@dataclass
class PixelSpacingInfo:
    """
    Физический размер пикселя в мм.
    row — вертикальный (высота пикселя)
    col — горизонтальный (ширина пикселя)
    В большинстве рентгенограмм таза row == col, но не всегда.
    """
    row_mm: float
    col_mm: float
    source: str  # откуда взято: "PixelSpacing" | "ImagerPixelSpacing" | "fallback"

    @property
    def is_isotropic(self) -> bool:
        return abs(self.row_mm - self.col_mm) < 0.01

    def px_to_mm_vertical(self, px: float) -> float:
        """Вертикальное расстояние (h) пиксели → мм."""
        return round(px * self.row_mm, 2)

    def px_to_mm_horizontal(self, px: float) -> float:
        """Горизонтальное расстояние (d) пиксели → мм."""
        return round(px * self.col_mm, 2)


def extract_pixel_spacing(contents: bytes) -> PixelSpacingInfo | None:
    """
    Извлекает Pixel Spacing из DICOM.

    Порядок приоритетов тегов:
      1. PixelSpacing (0028,0030)        — реальный размер пикселя на детекторе
      2. ImagerPixelSpacing (0018,1164)  — геометрический размер (может отличаться
                                           из-за увеличения, но лучше чем ничего)
      3. NominalScannedPixelSpacing      — редко, CR/DR снимки

    Возвращает None если DICOM не читается или теги отсутствуют.
    Не возвращает fallback — решение о нём принимает вызывающий код.
    """
    try:
        ds = pydicom.dcmread(
            io.BytesIO(contents),
            force=True,
            stop_before_pixels=True,
        )
    except Exception as exc:
        logger.debug(f"[PixelSpacing] Не DICOM или ошибка чтения: {exc}")
        return None

    # 1. PixelSpacing
    ps = getattr(ds, "PixelSpacing", None)
    if ps is not None:
        try:
            row, col = float(ps[0]), float(ps[1])
            if row > 0 and col > 0:
                logger.info(f"[PixelSpacing] PixelSpacing: {row}×{col} мм/пкс")
                return PixelSpacingInfo(row_mm=row, col_mm=col, source="PixelSpacing")
        except Exception:
            pass

    # 2. ImagerPixelSpacings
    ips = getattr(ds, "ImagerPixelSpacing", None)
    if ips is not None:
        try:
            row, col = float(ips[0]), float(ips[1])
            if row > 0 and col > 0:
                logger.info(f"[PixelSpacing] ImagerPixelSpacing: {row}×{col} мм/пкс")
                return PixelSpacingInfo(row_mm=row, col_mm=col, source="ImagerPixelSpacing")
        except Exception:
            pass

    # 3. NominalScannedPixelSpacing
    nsps = getattr(ds, "NominalScannedPixelSpacing", None)
    if nsps is not None:
        try:
            row, col = float(nsps[0]), float(nsps[1])
            if row > 0 and col > 0:
                logger.info(f"[PixelSpacing] NominalScannedPixelSpacing: {row}×{col} мм/пкс")
                return PixelSpacingInfo(row_mm=row, col_mm=col, source="NominalScannedPixelSpacing")
        except Exception:
            pass

    logger.info("[PixelSpacing] Теги Pixel Spacing в DICOM не найдены")
    return None
