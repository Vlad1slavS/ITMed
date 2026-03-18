"""Построение наглядного overlay с линиями, точками и подписями."""

from __future__ import annotations

import math

import cv2
import numpy as np

from backend.service.hip_yolo.constants import KP_COLORS_BGR, SIDE_COLORS_BGR


def _draw_label(
        img: np.ndarray,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font_scale: float = 0.5,
) -> None:
    # Подписи сейчас отключены по дизайну, но хук сохранен для быстрой активации.
    _ = (img, text, x, y, color, font_scale)


def _draw_crosshair(
        img: np.ndarray,
        px: int,
        py: int,
        radius: int,
        line_width: int,
        color: tuple[int, int, int],
) -> None:
    cv2.line(img, (px - radius, py), (px + radius, py), (0, 0, 0), line_width + 2, cv2.LINE_AA)
    cv2.line(img, (px, py - radius), (px, py + radius), (0, 0, 0), line_width + 2, cv2.LINE_AA)
    cv2.line(img, (px - radius, py), (px + radius, py), color, line_width, cv2.LINE_AA)
    cv2.line(img, (px, py - radius), (px, py + radius), color, line_width, cv2.LINE_AA)
    cv2.circle(img, (px, py), max(2, line_width - 1), color, -1)


def _draw_dashed_line(
        img: np.ndarray, p1: tuple, p2: tuple, color: tuple, thickness: int = 1,
        dash_len: int = 8, gap_len: int = 5,
) -> None:
    x1, y1 = int(p1[0]), int(p1[1])
    x2, y2 = int(p2[0]), int(p2[1])
    dx = x2 - x1
    dy = y2 - y1
    length = max(1, int(math.sqrt(dx * dx + dy * dy)))
    step = dash_len + gap_len
    for i in range(0, length, step):
        start_ratio = i / length
        end_ratio = min((i + dash_len) / length, 1.0)
        sx = int(x1 + dx * start_ratio)
        sy = int(y1 + dy * start_ratio)
        ex = int(x1 + dx * end_ratio)
        ey = int(y1 + dy * end_ratio)
        cv2.line(img, (sx, sy), (ex, ey), color, thickness, cv2.LINE_AA)


def _draw_extended_line(
        img: np.ndarray,
        p1: tuple[float, float],
        p2: tuple[float, float],
        color: tuple[int, int, int],
        thickness: int = 1,
) -> None:
    h, w = img.shape[:2]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return
    if abs(dy) < 1e-6:
        cv2.line(img, (0, int(p1[1])), (w, int(p1[1])), color, thickness, cv2.LINE_AA)
        return
    if abs(dx) < 1e-6:
        cv2.line(img, (int(p1[0]), 0), (int(p1[0]), h), color, thickness, cv2.LINE_AA)
        return
    t0 = (0 - p1[1]) / dy
    t1 = (h - p1[1]) / dy
    tl = (0 - p1[0]) / dx
    tr = (w - p1[0]) / dx
    t_start, t_end = sorted([t0, t1, tl, tr])[1:3]
    cv2.line(
        img,
        (int(p1[0] + t_start * dx), int(p1[1] + t_start * dy)),
        (int(p1[0] + t_end * dx), int(p1[1] + t_end * dy)),
        color,
        thickness,
        cv2.LINE_AA,
    )


def build_overlay(img_bgr: np.ndarray, sides: dict) -> np.ndarray:
    """Рисует линии, точки и рамки поверх предобработанного снимка."""
    vis = img_bgr.copy()
    img_h, img_w = vis.shape[:2]
    scale = max(img_w, img_h) / 800
    line_width = max(2, int(3 * scale))
    radius = max(3, int(4 * scale))
    keypoint_width = max(1, int(2 * scale))
    font_scale = max(0.5, 0.55 * scale)

    tcc_l = sides.get("left", {}).get("kp", {}).get("TCC")
    tcc_r = sides.get("right", {}).get("kp", {}).get("TCC")
    if tcc_l and tcc_r:
        _draw_extended_line(vis, tcc_l, tcc_r, (200, 200, 200), 1)
        hl_y = int((tcc_l[1] + tcc_r[1]) / 2)
        _draw_label(vis, "Hilgenreiner", 6, hl_y - 6, (200, 200, 200), font_scale * 0.8)

    for side, det in sides.items():
        color = SIDE_COLORS_BGR.get(side, (200, 200, 200))
        x1, y1, x2, y2 = det["bbox"]
        kp = det["kp"]
        measurements = det["measurements"]

        _draw_label(vis, f"{side} {det['conf']:.2f}", x1, y1 - 6, color, font_scale)

        if "ASM" in kp:
            asm_x = int(kp["ASM"][0])
            cv2.line(vis, (asm_x, 0), (asm_x, img_h), color, 1, cv2.LINE_AA)
            _draw_label(vis, "Perkin", asm_x + 4, 16, color, font_scale * 0.75)

        for p_from, p_to in [("TCC", "ASM")]:
            if p_from in kp and p_to in kp:
                cv2.line(
                    vis,
                    (int(kp[p_from][0]), int(kp[p_from][1])),
                    (int(kp[p_to][0]), int(kp[p_to][1])),
                    color,
                    max(1, line_width - 1),
                    cv2.LINE_AA,
                )

        # Визуализация h и d
        if "MOFM" in kp and tcc_l and tcc_r:
            mofm = kp["MOFM"]
            hl_y = int((tcc_l[1] + tcc_r[1]) / 2)
            mofm_x = int(mofm[0])
            mofm_y = int(mofm[1])

            _draw_dashed_line(vis, (mofm_x, mofm_y), (mofm_x, hl_y), color, 1)

        for name, (px, py) in kp.items():
            point_color = KP_COLORS_BGR.get(name, color)
            _draw_crosshair(vis, int(px), int(py), radius, keypoint_width, point_color)
            _draw_label(vis, name, int(px) + radius + 4, int(py) - 4, point_color, font_scale * 0.85)

        lines = []
        if "acetabular_index_deg" in measurements:
            lines.append(f"AI: {measurements['acetabular_index_deg']} deg")
        if "shenton" in measurements:
            lines.append(f"Shenton: {measurements['shenton']}")
        for idx, text in enumerate(lines):
            _draw_label(vis, text, x1, y2 + 18 + idx * 20, color, font_scale * 0.85)

    return vis
