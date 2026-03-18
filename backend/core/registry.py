"""
Реестр анализаторов — центральная точка расширяемости системы.

Новый модуль регистрируется декоратором @register("id") и становится
доступен через get_analyzer("id") без изменения кода ядра или роутеров.

Добавление нового анализатора не требует
модификации существующего кода — только создания нового модуля.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Type

from .base import BaseAnalyzer

_REGISTRY: Dict[str, BaseAnalyzer] = {}


def register(analyzer_id: str) -> Callable[[Type[BaseAnalyzer]], Type[BaseAnalyzer]]:
    """
    Декоратор-регистратор анализатора.

    Пример:
        @register("xray_pneumonia")
        class XRayPneumoniaAnalyzer(BaseAnalyzer):
            ...
    """

    def decorator(cls: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        instance = cls()
        _REGISTRY[analyzer_id] = instance
        return cls

    return decorator


def get_analyzer(analyzer_id: str) -> BaseAnalyzer:
    """Получить зарегистрированный анализатор по id."""
    try:
        return _REGISTRY[analyzer_id]
    except KeyError:
        available = ", ".join(_REGISTRY.keys()) or "(пусто)"
        raise KeyError(
            f"Анализатор '{analyzer_id}' не зарегистрирован. "
            f"Доступные: {available}"
        ) from None


def list_analyzers() -> dict[str, dict[str, Any]]:
    """Список всех зарегистрированных анализаторов (для /admin/stats)."""
    return {
        analyzer_id: {
            "id": analyzer.id,
            "name": analyzer.name,
            "modality": analyzer.modality,
            "class": analyzer.__class__.__name__,
        }
        for analyzer_id, analyzer in _REGISTRY.items()
    }


def unload_plugin(analyzer_id: str) -> bool:
    """Отключить анализатор из реестра. Возвращает True если был удален."""
    if analyzer_id not in _REGISTRY:
        return False
    del _REGISTRY[analyzer_id]
    return True
