"""
Обёртка над библиотекой Retuve для анализа дисплазии тазобедренного сустава.

Single Responsibility: запуск Retuve-пайплайна и возврат сырых результатов.
Классификация метрик — ответственность modules/hip_dysplasia/steps.py.
"""

from __future__ import annotations

import logging

import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


def run_retuve_analysis(image: Image.Image) -> dict:
    """
    Запускает анализ рентгенограммы ТБС через Retuve + YOLO.

    Returns
    -------
    dict с ключами:
        - metrics   : dict[str, float]
        - overlay   : np.ndarray (RGB)
        - hip_data  : HipDataXray
    """
    logger.info("[RetuveRunner] Старт анализа Retuve")

    from retuve.defaults.hip_configs import default_xray
    from retuve.funcs import analyse_hip_xray_2D
    from retuve_yolo_plugin.xray import yolo_predict_xray

    default_xray.device = "cpu"

    img_rgb = image.convert("RGB")

    hip_data, labelled_img, _dev_metrics = analyse_hip_xray_2D(
        img_rgb,
        keyphrase=default_xray,
        modes_func=yolo_predict_xray,
        modes_func_kwargs_dict={},
    )

    metrics_dict = {m.name: m.value for m in (hip_data.metrics or [])}
    overlay_np = np.array(labelled_img)

    landmarks_count = 0
    if getattr(hip_data, "landmarks", None) is not None:
        landmarks_count = len([v for v in vars(hip_data.landmarks).values() if v is not None])

    logger.info(
        f"[RetuveRunner] Анализ завершен: метрик={len(metrics_dict)}, landmarks={landmarks_count}"
    )

    return {
        "metrics": metrics_dict,
        "overlay": overlay_np,
        "hip_data": hip_data,
    }
