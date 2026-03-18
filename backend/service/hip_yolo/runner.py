"""
Публичный раннер YOLO-анализа ТБС.

Single Responsibility: запуск инференса, сборка метрик и overlay.
Все геометрические вычисления делегируются geometry.py.
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from backend.service.hip_yolo.constants import CONF_THRESHOLD
from backend.service.hip_yolo.geometry import (
    acetabular_index,
    compute_h_d,
    compute_ihdi,
    shenton_status,
)
from backend.service.hip_yolo.grouping import group_by_side
from backend.service.hip_yolo.overlay import build_overlay
from backend.service.hip_yolo.preprocess import preprocess_for_yolo

logger = logging.getLogger(__name__)


def run_yolo_hip_analysis(
        image: Image.Image,
        yolo_model,
        pixel_spacing: Optional[object] = None,
) -> dict:
    """
    Запускает YOLO pose-инференс на рентгенограмме ТБС.

    Parameters
    ----------
    image : PIL.Image
        Входной снимок (будет конвертирован в RGB).
    yolo_model : ultralytics.YOLO
        Загруженная YOLO pose-модель.
    pixel_spacing : PixelSpacingInfo | None
        Информация о физическом размере пикселя для h/d в мм.

    Returns
    -------
    dict:
        metrics   : dict — плоские метрики для API
        overlay   : np.ndarray (RGB) — снимок с разметкой
        sides     : dict — сырые точки/измерения по сторонам
        warnings  : list[str] — предупреждения раннера
    """
    logger.info("[YoloHipRunner] Старт анализа YOLO-модели ТБС")

    img_bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    img_preprocessed = preprocess_for_yolo(img_bgr)

    results = yolo_model(img_preprocessed, conf=CONF_THRESHOLD, verbose=False)[0]

    warnings: list[str] = []
    sides: dict[str, dict] = {}

    if results.boxes is None or len(results.boxes) == 0:
        logger.warning("[YoloHipRunner] Детекций не найдено")
        warnings.append("No detections")
    else:
        sides = group_by_side(results, yolo_model.names)
        if len(sides) == 0:
            warnings.append("No hips detected")
        elif len(sides) == 1:
            detected_side = list(sides.keys())[0]
            warnings.append(
                f"Only {detected_side} hip detected — image may be incomplete"
            )

    # ── Ацетабулярный индекс ──────────────────────────────────────────────────
    for side, det in sides.items():
        kp = det["kp"]
        m = det["measurements"]
        if "TCC" in kp and "ASM" in kp:
            m["acetabular_index_deg"] = acetabular_index(kp["TCC"], kp["ASM"])

    # ── h/d, Shenton, IHDI (требуют обеих сторон) ────────────────────────────
    if "left" in sides and "right" in sides:
        tcc_l = sides["left"]["kp"].get("TCC")
        tcc_r = sides["right"]["kp"].get("TCC")

        for side, det in sides.items():
            kp = det["kp"]
            m = det["measurements"]
            fhc = kp.get("FHC")
            mofm = kp.get("MOFM")

            # h и d
            tcc_side = sides[side]["kp"].get("TCC")
            if tcc_l and tcc_r and mofm and tcc_side:
                hd = compute_h_d(tcc_l, tcc_r, fhc, mofm, pixel_spacing=pixel_spacing)
                m["h"] = hd["h"]
                m["d"] = hd["d"]
                m["spacing_source"] = hd["spacing_source"]

            # Линия Шентона
            if fhc and mofm and kp.get("TCC"):
                status, dev = shenton_status(fhc, mofm, kp["TCC"])
                m["shenton"] = status
                m["shenton_deviation_px"] = dev

            # IHDI
            if tcc_l and tcc_r and fhc:
                asm = kp.get("ASM")
                roof_edge_x = asm[0] if asm else None
                m["ihdi"] = compute_ihdi(fhc, tcc_l, tcc_r, roof_edge_x=roof_edge_x)

    # ── Overlay ──────────────────────────────────────────────────────────────
    overlay_bgr = build_overlay(img_preprocessed, sides)
    overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)

    # ── Плоские метрики для API ──────────────────────────────────────────────
    metrics: dict[str, object] = {
        "ace_index_left": sides.get("left", {}).get("measurements", {}).get("acetabular_index_deg"),
        "ace_index_right": sides.get("right", {}).get("measurements", {}).get("acetabular_index_deg"),
        "ihdi_left": sides.get("left", {}).get("measurements", {}).get("ihdi"),
        "ihdi_right": sides.get("right", {}).get("measurements", {}).get("ihdi"),
        "h_left": sides.get("left", {}).get("measurements", {}).get("h"),
        "h_right": sides.get("right", {}).get("measurements", {}).get("h"),
        "d_left": sides.get("left", {}).get("measurements", {}).get("d"),
        "d_right": sides.get("right", {}).get("measurements", {}).get("d"),
        "shenton_left": sides.get("left", {}).get("measurements", {}).get("shenton"),
        "shenton_right": sides.get("right", {}).get("measurements", {}).get("shenton"),
    }

    logger.info(
        "[YoloHipRunner] Готово: ace_left=%s, ace_right=%s, warnings=%s",
        metrics["ace_index_left"],
        metrics["ace_index_right"],
        warnings,
    )

    return {
        "metrics": metrics,
        "overlay": overlay_rgb,
        "sides": sides,
        "warnings": warnings,
    }
