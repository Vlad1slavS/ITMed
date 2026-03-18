"""Сервис загрузки, активации и отключения плагинов анализаторов."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from backend.core.registry import list_analyzers, unload_plugin
from backend.service.admin.plugin_validator import PluginValidator


logger = logging.getLogger(__name__)
PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent / "plugins"
_validator = PluginValidator()


def ensure_plugins_dir() -> Path:
    """Создает директорию плагинов при необходимости и возвращает путь."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return PLUGINS_DIR


def load_plugin_file(plugin_path: Path) -> None:
    """Импортирует python-плагин по файловому пути."""
    module_name = f"backend.plugins.{plugin_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось создать spec для {plugin_path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def upload_plugin_file(filename: str, content: bytes) -> tuple[list[str], dict]:
    """Загружает плагин, валидирует его и возвращает новые analyzer_id."""
    if not filename.lower().endswith(".py"):
        raise ValueError("Только .py файлы")
    if b"@register" not in content:
        raise ValueError("Файл не содержит @register — не является анализатором")

    _validator.validate(content)

    plugins_dir = ensure_plugins_dir()
    plugin_path = plugins_dir / filename
    plugin_path.write_bytes(content)

    before = set(list_analyzers().keys())
    try:
        load_plugin_file(plugin_path)
    except Exception:
        plugin_path.unlink(missing_ok=True)
        raise

    after = set(list_analyzers().keys())
    new_analyzers = sorted(after - before)
    if not new_analyzers:
        plugin_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Плагин загружен но анализатор не зарегистрировался. Проверь что в файле есть @register('id')"
        )

    logger.info(f"[Плагины] Загружен плагин {filename}, зарегистрированы: {new_analyzers}")
    return new_analyzers, list_analyzers()


def remove_plugin_by_id(analyzer_id: str) -> bool:
    """Отключает анализатор из реестра."""
    removed = unload_plugin(analyzer_id)
    if removed:
        logger.info(f"[Плагины] Отключен анализатор: {analyzer_id}")
    return removed


def get_plugins_snapshot() -> dict:
    """Возвращает список файлов плагинов и активных анализаторов."""
    plugins_dir = ensure_plugins_dir()
    plugin_files = sorted(p.name for p in plugins_dir.glob("*.py"))
    active_analyzers = sorted(list_analyzers().keys())
    return {"plugins": plugin_files, "active_analyzers": active_analyzers}


def load_saved_plugins() -> None:
    """Загружает все ранее сохраненные плагины из папки plugins."""
    plugins_dir = ensure_plugins_dir()
    for py_file in plugins_dir.glob("*.py"):
        try:
            load_plugin_file(py_file)
            logger.info(f"[Плагины] Загружен плагин: {py_file.name}")
        except Exception as e:
            logger.warning(f"[Плагины] Ошибка загрузки {py_file.name}: {e}")
