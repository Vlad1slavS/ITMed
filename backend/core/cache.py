from __future__ import annotations

import hashlib
from typing import Any, Dict, Tuple

from PIL import Image

from .base import AnalysisContext

_CACHE: Dict[Tuple[str, str], Any] = {}


def _image_md5(image: Image.Image) -> str:
    """
    Вычисляет md5 по байтовому представлению изображения.
    Для простоты используем RGB + PNG‑кодирование.
    """

    import io

    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    return hashlib.md5(buf.getvalue()).hexdigest()  


def make_cache_key(context: AnalysisContext, image: Image.Image) -> tuple[str, str]:
    """
    Ключ кэша: (analyzer_id, md5‑хеш изображения).
    """

    analyzer_id = context.analyzer_id or "unknown"
    return analyzer_id, _image_md5(image)


def get_from_cache(context: AnalysisContext, image: Image.Image) -> Any | None:
    key = make_cache_key(context, image)
    return _CACHE.get(key)


def set_cache(context: AnalysisContext, image: Image.Image, value: Any) -> None:
    key = make_cache_key(context, image)
    _CACHE[key] = value

