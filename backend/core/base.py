from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from PIL import Image


@dataclass
class AnalysisContext:
    """
    Общий контекст анализа, который могут использовать разные анализаторы.

    Идея: сюда можно добавлять всё, что относится не к конкретной патологии,
    а к запросу в целом (пользователь, источник, язык интерфейса и т.п.).
    """

    request_id: str
    modality: Optional[str] = None
    analyzer_id: Optional[str] = None
    patient_age_months: Optional[int] = None
    patient_age_source: Optional[str] = None


@dataclass
class LandmarkPoint:
    """
    Ключевая точка на изображении для образовательного режима.
    
    Используется для оценки точности расстановки точек студентом.
    """
    x_px: float  # Пиксельные координаты
    y_px: float
    x_norm: float  # Нормализованные координаты 0..1
    y_norm: float
    name: str  # Ключ точки (например, "pel_l_o")
    label_ru: str  # Человекочитаемое название


class BaseAnalyzer(ABC):
    """
    Базовый интерфейс для всех модулей анализа.

    Любой новый модуль (другая анатомическая зона / патология) должен
    реализовать этот интерфейс и зарегистрироваться в реестре.
    """

    id: str
    name: str
    modality: Optional[str] = None  # напр. "xray", "microscopy"

    def __init__(self, *, id: str, name: str, modality: Optional[str] = None) -> None:
        self.id = id
        self.name = name
        self.modality = modality

    @abstractmethod
    async def analyze(
        self,
        image: Image.Image,
        *,
        context: AnalysisContext,
        **kwargs: Any,
    ) -> Any:
        """
        Запускает анализ одного изображения.

        Возвращаемое значение оставляем свободным: это может быть Pydantic‑модель
        (например, `AnalysisResponse`) или словарь. Главное: формат стабильный
        внутри конкретного анализатора.
        """

    async def get_landmarks(
        self, image: Image.Image
    ) -> Dict[str, LandmarkPoint]:
        """
        Возвращает ключевые точки для образовательного режима.
        
        По умолчанию возвращает пустой словарь. Анализаторы, поддерживающие
        образовательный режим, должны переопределить этот метод.
        
        Returns
        -------
        dict[str, LandmarkPoint]
            Словарь ключ_точки → LandmarkPoint с координатами и метаданными.
        """
        return {}
