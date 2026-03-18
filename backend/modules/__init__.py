"""
Авто-регистрация всех модулей анализа.

При импорте этого пакета каждый модуль подключается к core.registry
через декоратор @register. Добавление нового модуля — это:
  1. Создать папку  backend/modules/<module_name>/
  2. Реализовать analyzer.py с классом(BaseAnalyzer) и @register("<id>")
  3. Добавить одну строку импорта ниже.
"""

from backend.modules.blood_cells import analyzer as _blood  # noqa: F401
from backend.modules.hip_dysplasia import analyzer as _hip  # noqa: F401
from backend.modules.xray_advanced import analyzer as _adv  # noqa: F401
from backend.modules.xray_pneumonia import analyzer as _xray  # noqa: F401
