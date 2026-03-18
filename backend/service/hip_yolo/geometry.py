"""Геометрические вычисления для метрик дисплазии ТБС."""

from __future__ import annotations

import math
from typing import Optional


def acetabular_index(tcc: tuple[float, float], asm: tuple[float, float]) -> float:
    """
    Ацетабулярный угол между горизонталью и линией TCC -> ASM.
    """
    dx = asm[0] - tcc[0]
    dy = asm[1] - tcc[1]

    if abs(dx) < 1e-6:
        return 90.0

    return round(math.degrees(math.atan2(abs(dy), abs(dx))), 1)


def compute_h_d(
    tcc_l: tuple[float, float],
    tcc_r: tuple[float, float],
    tcc_side: tuple,
    mofm: tuple[float, float],
    pixel_spacing: Optional[object] = None,
) -> dict:
    """
    Вычисляет h и d в старом совместимом формате.

    h:
      вертикальное расстояние от линии Хильгенрейнера до MOFM

    d:
      горизонтальное расстояние от вертикали через TCC данной стороны до MOFM

    Возвращает значения в том же формате, что и раньше:
      {
        "h": "12.4 mm",
        "d": "8.1 mm",
        "spacing_source": ...
      }

    ВАЖНО:
    Это совместимая реализация под старые вызовы.
    """
    hl_y = (tcc_l[1] + tcc_r[1]) / 2.0

    h_px = abs(mofm[1] - hl_y)
    d_px = abs(mofm[0] - tcc_side[0])

    if pixel_spacing is not None:
        h_val = round(pixel_spacing.px_to_mm_vertical(h_px), 2)
        d_val = round(pixel_spacing.px_to_mm_horizontal(d_px), 2)
        unit = "mm"
    else:
        h_val = round(h_px, 2)
        d_val = round(d_px, 2)
        unit = "px"

    return {
        "h": f"{h_val} {unit}",
        "d": f"{d_val} {unit}",
        "spacing_source": getattr(pixel_spacing, "source", None),
    }


def compute_ihdi(
    fhc: tuple[float, float],
    tcc_l: tuple[float, float],
    tcc_r: tuple[float, float],
    roof_edge_x: Optional[float] = None,
) -> str:
    """
    Совместимая версия IHDI без изменения сигнатуры.

    ОЖИДАНИЕ:
    - roof_edge_x должен передаваться для конкретной стороны:
      * для правой ТБС -> x наружного края правой крыши
      * для левой ТБС  -> x наружного края левой крыши

    ЛОГИКА:
    - определяем сторону автоматически по близости FHC к TCC_l / TCC_r
    - строим линию Хильгенрейнера
    - используем vertical line через roof_edge_x как линию Перкина

    Если roof_edge_x не передан, возвращаем "I" как безопасный дефолт,
    чтобы не лепить ложный II/III/IV.
    """
    hl_y = (tcc_l[1] + tcc_r[1]) / 2.0
    fx, fy = fhc

    if roof_edge_x is None:
        # Без линии Перкина корректно IHDI не посчитать.
        # Безопаснее вернуть I, чем делать ложный II.
        return "I"

    # Автоопределение стороны по близости центра головки к соответствующему TCC
    dist_to_left = abs(fx - tcc_l[0])
    dist_to_right = abs(fx - tcc_r[0])

    # ВАЖНО:
    # tcc_l / tcc_r обычно названы по анатомической стороне пациента,
    # а не по стороне на изображении.
    # Но для квадрантов нам важна именно геометрия:
    # если FHC ближе к tcc_l -> считаем, что это "левая" анатомическая сторона
    # в терминах твоих landmarks.
    side = "left" if dist_to_left <= dist_to_right else "right"

    below_h = fy > hl_y

    if side == "left":
        # для анатомически левой стороны на AP-снимке
        # медиально = x < roof_edge_x
        medial_to_perkin = fx < roof_edge_x
    else:
        # для анатомически правой стороны
        # медиально = x > roof_edge_x
        medial_to_perkin = fx > roof_edge_x

    if medial_to_perkin and below_h:
        return "I"
    elif (not medial_to_perkin) and below_h:
        return "II"
    elif medial_to_perkin and (not below_h):
        return "III"
    else:
        return "IV"


def shenton_status(
    fhc: tuple[float, float],
    mofm: tuple[float, float],
    tcc: tuple[float, float],
) -> tuple[str, float]:
    """
    Совместимая суррогатная оценка непрерывности дуги.

    Это НЕ настоящая линия Шентона, а эвристика по 3 точкам.
    Возвращает:
      ("норма" | "прерывается" | "unknown", deviation_px)
    """
    dx = tcc[0] - mofm[0]
    dy = tcc[1] - mofm[1]
    length = math.hypot(dx, dy)

    if length < 1e-6:
        return "unknown", 0.0

    nx, ny = -dy / length, dx / length
    deviation = abs((fhc[0] - mofm[0]) * nx + (fhc[1] - mofm[1]) * ny)

    # Делаем порог чуть мягче, чтобы снизить ложные "прерывается"
    threshold = length * 0.18
    status = "normal" if deviation <= threshold else "disrupted"

    return status, round(deviation, 1)