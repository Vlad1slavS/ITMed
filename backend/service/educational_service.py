"""
Сервис оценки образовательных заданий по дисплазии ТБС.

Оценка расстановки точек, качественных признаков
и итогового диагноза студента.
"""

from __future__ import annotations

import math
from typing import Any, Dict

from backend.app.config import settings


def simplify_diagnosis(overall_diagnosis: str) -> str:
    """Упрощает текстовый диагноз до одного из: норма / предвывих / подвывих / вывих."""
    text_lower = overall_diagnosis.lower()
    if "вывих" in text_lower or "iii ст" in text_lower:
        return "вывих"
    if "подвывих" in text_lower or "ii ст" in text_lower:
        return "подвывих"
    if "предвывих" in text_lower or "i ст" in text_lower or "вероятная патология" in text_lower:
        return "предвывих"
    return "норма"


def evaluate_points(
    correct_points: Dict[str, Any],
    student_points: Dict[str, Dict[str, float]],
    image_width: int,
    image_height: int,
) -> Dict[str, Any]:
    """Оценивает расстановку точек студентом по сравнению с эталонными координатами."""
    total_score = 0.0
    max_score = 0.0
    points_detail = {}

    for point_name, correct_point in correct_points.items():
        if point_name not in student_points:
            points_detail[point_name] = {
                "label": correct_point.label_ru,
                "distance_px": None,
                "grade": "poor",
                "grade_label": "Точка не расставлена",
                "correct": {"x": float(correct_point.x_norm), "y": float(correct_point.y_norm)},
                "student": None,
            }
            max_score += 1.0
            continue

        student = student_points[point_name]
        student_x_px = student["x"] * image_width
        student_y_px = student["y"] * image_height

        distance_px = math.sqrt(
            (student_x_px - correct_point.x_px) ** 2
            + (student_y_px - correct_point.y_px) ** 2
        )

        if distance_px < settings.EDU_POINTS_EXCELLENT_PX:
            grade, grade_label, point_score = "excellent", "Отлично", 1.0
        elif distance_px < settings.EDU_POINTS_GOOD_PX:
            grade, grade_label, point_score = "good", "Хорошо", 0.7
        else:
            grade, grade_label, point_score = "poor", "Плохо", 0.3

        total_score += point_score
        max_score += 1.0

        points_detail[point_name] = {
            "label": correct_point.label_ru,
            "distance_px": float(distance_px),
            "grade": grade,
            "grade_label": grade_label,
            "correct": {"x": float(correct_point.x_norm), "y": float(correct_point.y_norm)},
            "student": {"x": float(student["x"]), "y": float(student["y"])},
        }

    return {
        "score": int((total_score / max_score * 100) if max_score > 0 else 0),
        "points": points_detail,
    }


def evaluate_qualitative(
    student_qualitative: Dict[str, str],
    metrics_dict: Dict[str, Any],
    landmarks: Dict[str, Any],
) -> list[Dict[str, Any]]:
    """
    Оценивает качественные признаки и формирует подробный фидбек.

    Линия Шентона: берётся из метрик (shenton_left / shenton_right),
    вычисленных YOLO или Retuve. Если данных нет — fallback по IHDI.
    """
    feedback = []

    for side in ["left", "right"]:
        side_label = "лев" if side == "left" else "прав"

        # Линия Шентона: предпочитаем данные из YOLO/Retuve
        shenton_val = metrics_dict.get(f"shenton_{side}")
        if shenton_val is not None:
            correct_shenton = (
                "прерывается" if str(shenton_val) == "disrupted" else "непрерывная"
            )
        else:
            # Fallback: определяем по IHDI
            ihdi_grade = metrics_dict.get(f"ihdi_grade_{side}") or metrics_dict.get(f"ihdi_{side}")
            if ihdi_grade is not None:
                grade_num = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(str(ihdi_grade), int(ihdi_grade) if isinstance(ihdi_grade, (int, float)) else 0)
                correct_shenton = "прерывается" if grade_num >= 2 else "непрерывная"
            else:
                correct_shenton = "непрерывная"

        student_shenton = student_qualitative.get(f"shenton_{side}", "")
        feedback.append(
            {
                "field": f"Линия Шентона ({side_label})",
                "student": student_shenton,
                "correct": correct_shenton,
                "is_correct": student_shenton.lower() == correct_shenton.lower(),
            }
        )

        # Ядро окостенения
        fem_point = landmarks.get(f"fhc_{side}")
        correct_ossif = "есть" if fem_point is not None else "отсутствует"
        student_ossif = student_qualitative.get(f"ossif_{side}", "")
        is_correct = (
            student_ossif == "уменьшено" and correct_ossif == "есть"
        ) or student_ossif.lower() == correct_ossif.lower()
        feedback.append(
            {
                "field": f"Ядро окостенения ({side_label})",
                "student": student_ossif,
                "correct": correct_ossif,
                "is_correct": is_correct,
            }
        )

    return feedback


def compute_total_score(points_score: int, qual_feedback: list, diagnosis_correct: bool) -> int:
    """Вычисляет итоговый балл за задание (0..100)."""
    qual_score = 0
    if qual_feedback:
        correct = sum(1 for q in qual_feedback if q["is_correct"])
        qual_score = int(correct / len(qual_feedback) * 100)
    diagnosis_score = 100 if diagnosis_correct else 0
    return int(
        points_score * settings.EDU_WEIGHT_POINTS
        + qual_score * settings.EDU_WEIGHT_QUAL
        + diagnosis_score * settings.EDU_WEIGHT_DIAGNOSIS
    )


def convert_floats(obj):
    """Рекурсивно конвертирует np.float64 в float для JSON сериализации."""
    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    if hasattr(obj, "dtype") and "float" in str(obj.dtype):
        return float(obj)
    return obj
