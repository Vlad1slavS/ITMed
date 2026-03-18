"""
Построение LandmarkPoint.

Single Responsibility: конвертация сырых keypoints в унифицированный
формат LandmarkPoint для образовательного режима.
"""

from __future__ import annotations

from typing import Any, Dict

from PIL import Image

from backend.core.base import LandmarkPoint

# Человекочитаемые названия ключевых точек
_KP_LABEL_MAP: dict[str, str] = {
    "ASM": "ASM: верхний край крыши вертлужной впадины",
    "TCC": "TCC: центр Y-хряща (тройной хрящ)",
    "FHC": "FHC: центр головки бедренной кости",
    "MOFM": "MOFM: медиальный контур метафиза",
}


def build_landmarks_from_yolo(
    image: Image.Image,
    sides: dict,
) -> dict[str, LandmarkPoint]:
    """
    Конвертирует YOLO keypoints в LandmarkPoint.

    Parameters
    ----------
    image : PIL.Image — для получения размеров снимка
    sides : dict — результат group_by_side (из runner)
    """
    width, height = image.size
    result: dict[str, LandmarkPoint] = {}

    for side, det in sides.items():
        for kp_name, (x_px, y_px) in det["kp"].items():
            key = f"{kp_name.lower()}_{side}"
            label = f"{_KP_LABEL_MAP.get(kp_name, kp_name)} ({side})"
            result[key] = LandmarkPoint(
                x_px=x_px,
                y_px=y_px,
                x_norm=x_px / width,
                y_norm=y_px / height,
                name=key,
                label_ru=label,
            )

    return result


def build_landmarks_from_retuve(
    image: Image.Image,
    retuve_result: dict,
) -> dict[str, LandmarkPoint]:
    """
    Конвертирует landmarks из Retuve HipDataXray в LandmarkPoint.

    Используется как дополнение / fallback к YOLO landmarks.
    """
    hip_data = retuve_result.get("hip_data")
    if hip_data is None:
        return {}

    landmarks = getattr(hip_data, "landmarks", None)
    if landmarks is None:
        return {}

    width, height = image.size
    result: Dict[str, LandmarkPoint] = {}

    mapping: Dict[str, tuple[Any, str]] = {
        "tcc_left": (getattr(landmarks, "pel_l_i", None), "A - TCC: центр Y-хряща (лев)"),
        "tcc_right": (getattr(landmarks, "pel_r_i", None), "A - TCC: центр Y-хряща (прав)"),
        "asm_left": (getattr(landmarks, "pel_l_o", None), "B - ASM: верхний край крыши (лев)"),
        "asm_right": (getattr(landmarks, "pel_r_o", None), "B - ASM: верхний край крыши (прав)"),
        "fhc_left": (getattr(landmarks, "fem_l", None), "C - FHC: центр головки бедра (лев)"),
        "fhc_right": (getattr(landmarks, "fem_r", None), "C - FHC: центр головки бедра (прав)"),
        "mofm_left": (getattr(landmarks, "h_point_l", None), "H - MOFM: медиальный контур метафиза (лев)"),
        "mofm_right": (getattr(landmarks, "h_point_r", None), "H - MOFM: медиальный контур метафиза (прав)"),
    }

    for key, (pt, label_ru) in mapping.items():
        if pt is None:
            continue
        x_px, y_px = float(pt[0]), float(pt[1])
        result[key] = LandmarkPoint(
            x_px=x_px,
            y_px=y_px,
            x_norm=x_px / width,
            y_norm=y_px / height,
            name=key,
            label_ru=label_ru,
        )

    return result


def landmarks_to_payload(landmarks: dict[str, LandmarkPoint]) -> dict:
    """Сериализует LandmarkPoints в словарь для JSON-ответа."""
    return {
        key: {
            "x_px": p.x_px,
            "y_px": p.y_px,
            "x_norm": p.x_norm,
            "y_norm": p.y_norm,
            "name": p.name,
            "label_ru": p.label_ru,
        }
        for key, p in landmarks.items()
    }
