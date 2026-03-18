"""Валидатор безопасности кода плагинов перед загрузкой."""

from __future__ import annotations

import ast
import logging


logger = logging.getLogger(__name__)


class PluginValidator:
    """Проверяет безопасность Python-плагина перед загрузкой в систему."""

    DANGEROUS_PATTERNS = [
        b"os.system",
        b"subprocess",
        b"__import__",
        b"eval(",
        b"exec(",
        b"socket",
        b"urllib",
        b"shutil.rmtree",
        b"os.remove",
        b"os.unlink",
        b"open(",
    ]

    ALLOWED_IMPORTS = {
        "PIL",
        "pillow",
        "numpy",
        "np",
        "torch",
        "cv2",
        "backend",
        "typing",
        "dataclasses",
        "abc",
        "uuid",
        "logging",
        "__future__",
    }

    def validate(self, content: bytes) -> None:
        """Запускает все этапы валидации плагина."""
        logger.debug("[Плагины] Запуск валидации: проверка сигнатур и AST")
        self._validate_dangerous_patterns(content)
        self._validate_ast(content)
        logger.debug("[Плагины] Валидация плагина пройдена успешно")

    def _validate_dangerous_patterns(self, content: bytes) -> None:
        """Проверяет сырой код на наличие опасных паттернов."""
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in content:
                text = pattern.decode("utf-8", errors="ignore")
                logger.warning(f"[Плагины] Обнаружен запрещенный паттерн: {text}")
                raise ValueError(f"Обнаружен запрещенный паттерн: {text}")
        logger.debug("[Плагины] Проверка опасных паттернов завершена")

    def _validate_ast(self, content: bytes) -> None:
        """Проверяет AST: импорты и запрещенные вызовы функций."""
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning(f"[Плагины] Ошибка декодирования файла плагина: {e}")
            raise ValueError("Файл плагина должен быть в UTF-8")

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"[Плагины] Синтаксическая ошибка в плагине: {e}")
            raise ValueError(f"Синтаксическая ошибка в плагине: {e.msg}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in self.ALLOWED_IMPORTS:
                        logger.warning(f"[Плагины] Запрещенный импорт: {root}")
                        raise ValueError(f"Запрещенный импорт: {root}")

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root not in self.ALLOWED_IMPORTS:
                        logger.warning(f"[Плагины] Запрещенный импорт: {root}")
                        raise ValueError(f"Запрещенный импорт: {root}")

            if isinstance(node, ast.Call):
                self._validate_call_node(node)

        logger.debug("[Плагины] AST-проверка завершена")

    def _validate_call_node(self, node: ast.Call) -> None:
        """Проверяет, что вызов функции не относится к запрещенным."""
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
            if call_name in {"eval", "exec", "compile", "open", "__import__"}:
                logger.warning(f"[Плагины] Запрещенный вызов: {call_name}")
                raise ValueError(f"Запрещенный вызов: {call_name}")

        full_name = self._get_call_full_name(node.func)
        if not full_name:
            return

        if full_name == "os.system":
            logger.warning("[Плагины] Запрещенный вызов: os.system")
            raise ValueError("Запрещенный вызов: os.system")
        if full_name.startswith("subprocess."):
            logger.warning(f"[Плагины] Запрещенный вызов: {full_name}")
            raise ValueError(f"Запрещенный вызов: {full_name}")
        if full_name.startswith("socket."):
            logger.warning(f"[Плагины] Запрещенный вызов: {full_name}")
            raise ValueError(f"Запрещенный вызов: {full_name}")
        if full_name in {"os.remove", "os.unlink", "shutil.rmtree"}:
            logger.warning(f"[Плагины] Запрещенный вызов: {full_name}")
            raise ValueError(f"Запрещенный вызов: {full_name}")

    def _get_call_full_name(self, node: ast.AST) -> str:
        """Возвращает полное имя вызова из AST, например 'os.system'."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            left = self._get_call_full_name(node.value)
            return f"{left}.{node.attr}" if left else node.attr
        return ""
