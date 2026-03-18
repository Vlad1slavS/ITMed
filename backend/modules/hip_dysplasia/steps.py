"""
Образовательные шаги и интерпретация метрик для дисплазии ТБС.

Single Responsibility: пороги, классификация отдельных метрик
и комплексный диагноз по совокупности признаков.
"""

from __future__ import annotations

from typing import Dict, Optional


# Пороги ацетабулярного угла по возрасту 


def _acetabular_thresholds(age_months: int | None) -> tuple[float, float, float]:
    """
    Возвращает пороги ацетабулярного угла:
    (норма, предвывих, подвывих).
    """
    if age_months is None:
        return 28.5, 33.0, 38.0

    if age_months <= 1:
        normal = 28.0
    elif age_months <= 6:
        normal = 25.0
    elif age_months <= 12:
        normal = 22.0
    elif age_months <= 24:
        normal = 20.0
    else:
        normal = 20.0

    return normal, normal + 4.0, normal + 9.0


# Классификация отдельных метрик 


def classify_acetabular_index(
        angle_deg: float | None,
        age_months: int | None = None,
) -> tuple[str, str]:
    """Классификация ацетабулярного угла → (текст, цвет)."""
    if age_months is None:
        return "Нет данных о возрасте", "gray"
    if angle_deg is None:
        return "Нет данных", "gray"
    normal_thr, pre_thr, sub_thr = _acetabular_thresholds(age_months)
    if angle_deg <= normal_thr:
        return "Норма", "green"
    if angle_deg <= pre_thr:
        return "I ст. (предвывих)", "orange"
    if angle_deg <= sub_thr:
        return "II ст. (подвывих)", "darkorange"
    return "III ст. (вывих)", "red"


def classify_wiberg(angle_deg: float | None) -> tuple[str, str]:
    """Классификация индекса Виберга → (текст, цвет)."""
    if angle_deg is None:
        return "Нет данных", "gray"
    if angle_deg >= 20:
        return "Норма (>=20\u00b0)", "green"
    if angle_deg >= 15:
        return "Погранично (15\u201319\u00b0)", "orange"
    if angle_deg >= 0:
        return "Патология (<15\u00b0)", "red"
    return "Дисплазия (отриц.)", "red"


def classify_ihdi(grade: int | str | None) -> tuple[str, str]:
    if grade is None:
        return "Нет данных", "gray"
    # конвертируем строку если нужно
    if isinstance(grade, str):
        grade = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(grade, 0)
    grade = int(grade)
    if grade <= 1:
        return "Норма (IHDI 1)", "green"
    if grade == 2:
        return "Лёгкое смещение (IHDI 2)", "orange"
    if grade == 3:
        return "Подвывих (IHDI 3)", "darkorange"
    return "Вывих (IHDI 4)", "red"


def classify_shenton(status: Optional[str]) -> tuple[str, str]:
    """
    Классификация состояния линии Шентона → (текст, цвет).

    status: "normal" | "disrupted" | "unknown" | None
    """
    if status is None or status == "unknown":
        return "Нет данных", "gray"
    if status == "normal":
        return "Непрерывная (норма)", "green"
    return "Прерывается (патология)", "red"


# Комплексный диагноз 


def classify_all_metrics(
        metrics_dict: Dict[str, object],
        age_months: int | None = None,
) -> str:
    """
    Комплексный диагноз по принципу «нескольких согласованных признаков».

    Учитывает: ацетабулярный индекс, IHDI, индекс Виберга,
    линию Шентона (если доступна).
    """
    results: list[str] = []

    for side, suffix in [("Левый", "_left"), ("Правый", "_right")]:
        ace = metrics_dict.get(f"ace_index{suffix}")
        ihdi = metrics_dict.get(f"ihdi_grade{suffix}")
        shenton = metrics_dict.get(f"shenton{suffix}")

        findings: list[str] = []
        pathology_votes = 0
        borderline_votes = 0
        severe = False

        ace_normal_thr, ace_pre_thr, ace_sub_thr = _acetabular_thresholds(age_months)

        # Ацетабулярный индекс
        if ace is not None:
            ace_f = float(ace)
            label, _ = classify_acetabular_index(ace_f, age_months=age_months)
            findings.append(f"Ace {ace_f:.1f}\u00b0 \u2192 {label}")
            if ace_f > ace_pre_thr:
                pathology_votes += 1
                if ace_f > ace_sub_thr:
                    severe = True
            elif ace_f > ace_normal_thr:
                borderline_votes += 1

        # IHDI
        if ihdi is not None:
            ihdi_i = int(ihdi) if isinstance(ihdi, (int, float)) else {"I": 1, "II": 2, "III": 3, "IV": 4}.get(
                str(ihdi), 0)
            label, _ = classify_ihdi(ihdi_i)
            findings.append(f"IHDI гр.{ihdi_i} \u2192 {label}")
            if ihdi_i >= 3:
                pathology_votes += 1
                severe = True
            elif ihdi_i == 2:
                pathology_votes += 1

        # Линия Шентона
        if shenton is not None:
            sh_label, _ = classify_shenton(str(shenton))
            findings.append(f"Шентон: {sh_label}")
            if shenton == "Прерывается":
                pathology_votes += 1

        # Вердикт
        if severe or pathology_votes >= 2:
            verdict = "Патология"
        elif pathology_votes == 1 and borderline_votes >= 1:
            verdict = "Вероятная патология (требует уточнения)"
        elif pathology_votes == 1 or borderline_votes >= 2:
            verdict = "Пограничное состояние"
        else:
            verdict = "Норма"

        results.append(f"{side}: {verdict}")
        if findings:
            results.append("   " + " | ".join(findings))

    return "\n".join(results)


def classify_by_table(
    ace_deg: float | None,
    d_mm: float | None,
    h_mm: float | None,
    age_months: int | None = None,
) -> tuple[str, str, list[str]]:
    """
    Классификация дисплазии по клинической таблице.
    """
    reasons: list[str] = []

    ai_threshold = 28.5
    if age_months is not None:
        ai_threshold, _, _ = _acetabular_thresholds(age_months)

    ace_pathology = False
    if ace_deg is None:
        reasons.append("AI недоступен")
    else:
        if ace_deg > ai_threshold:
            ace_pathology = True
            reasons.append(f"AI={ace_deg:.1f}° > {ai_threshold:.1f}° (патология)")
        else:
            reasons.append(f"AI={ace_deg:.1f}° ≤ {ai_threshold:.1f}° (норма)")

    has_mm = d_mm is not None and h_mm is not None
    if not has_mm:
        reasons.append("d/h недоступны в мм — степень по таблице уточнить невозможно")

        if ace_pathology:
            return "Подозрение на дисплазию (по AI)", "orange", reasons

        return "Норма", "green", reasons

    d_threshold = 12.0
    h_threshold = 10.0

    d_pathology = d_mm > d_threshold
    h_pathology = h_mm < h_threshold

    if d_mm < 10.0:
        reasons.append(f"d={d_mm:.1f} мм < 10 мм (погранично / ниже референса)")
    elif d_mm <= d_threshold:
        reasons.append(f"d={d_mm:.1f} мм ≤ {d_threshold:.1f} мм (норма)")
    else:
        reasons.append(f"d={d_mm:.1f} мм > {d_threshold:.1f} мм (патология)")

    if h_pathology:
        reasons.append(f"h={h_mm:.1f} мм < {h_threshold:.1f} мм (патология)")
    else:
        reasons.append(f"h={h_mm:.1f} мм ≥ {h_threshold:.1f} мм (норма)")

    if not ace_pathology and not d_pathology and not h_pathology:
        return "Норма", "green", reasons

    if ace_pathology and not d_pathology and not h_pathology:
        return "I ст. предвывих", "yellow", reasons

    if ace_pathology and d_pathology and not h_pathology:
        return "II ст. подвывих", "orange", reasons

    if ace_pathology and d_pathology and h_pathology:
        return "III ст. вывих", "red", reasons

    if not ace_pathology and d_pathology and not h_pathology:
        reasons.append("Нетипично: d патологичен при нормальном AI")
        return "Пограничное состояние", "orange", reasons

    if not ace_pathology and h_pathology:
        reasons.append("Нетипично: h патологичен при нормальном AI")
        return "Пограничное состояние", "orange", reasons

    if ace_pathology and not d_pathology and h_pathology:
        reasons.append("Нетипично: снижен h без увеличения d")
        return "Пограничное состояние", "orange", reasons

    reasons.append("Нетипичная комбинация признаков")
    return "Пограничное состояние", "orange", reasons
