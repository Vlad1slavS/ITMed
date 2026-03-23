# ITMed — AI-платформа для диагностики по медицинским снимкам

Система автоматического анализа медицинских изображений на базе нескольких ML-моделей. Поддерживает несколько моделей
рентгенографии, а также модель для микроскопии крови. Расширяемая архитектура позволяет добавлять новые
анализаторы без изменения ядра системы.

---

## Возможности

- **Дисплазия ТБС** — YOLO pose-модель для определения ключевых точек (ASM, TCC, FHC, MOFM), вычисление ацетабулярного
  индекса, IHDI, h/d смещений; бинарная классификация EfficientNet-B3 (ONNX)
- **DICOM поддержка** — автоматическое извлечение возраста пациента и Pixel Spacing из метаданных
- **Образовательный режим** — landmarks для расстановки точек студентом с оценкой точности
- **Кэширование** — повторные запросы одного снимка отдаются из БД без повторного инференса

---

## Стек технологий

| Слой                  | Технологии                                              |
|-----------------------|---------------------------------------------------------|
| Backend               | FastAPI, Uvicorn, SQLAlchemy, PostgreSQL                |
| ML                    | PyTorch, ONNX Runtime, Ultralytics YOLO, Cellpose, timm |
| Обработка изображений | OpenCV, Pillow, pydicom                                 |
| Инфраструктура        | Docker, Docker Compose                                  |
| Frontend              | `frontend/` (отдельная папка)                           |

---

## Структура проекта

```
ITMed/
├── backend/
│   ├── app/              # FastAPI приложение, config
│   ├── core/             # Реестр анализаторов, базовые классы
│   ├── db/               # Модели БД, миграции
│   ├── ml/               # Model manager, Grad-CAM
│   ├── modules/          # Анализаторы (hip_dysplasia, xray и др.)
│   ├── routers/          # HTTP роутеры
│   ├── schema/           # Pydantic схемы
│   ├── service/          # Сервисы (DICOM, overlay, PDF и др.)
│   └── weights/          # Веса моделей (не в git)
├── frontend/             # Фронтенд
├── retuve-data/          # Данные Retuve
├── scripts/              # Вспомогательные скрипты
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd ITMed
```

### 2. Создать `.env` файл

```bash
cp .env.example .env
```

При необходимости отредактируй `DATABASE_URL` и пути к весам. По умолчанию инференс на CPU (`DEVICE=cpu`), для GPU
измени на `DEVICE=cuda`.

### 3. Запустить базу данных

```bash
docker compose up -d db
```

### 4. Установить зависимости и запустить бэкенд

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 5. Запустить фронтенд

```bash
cd frontend
npm install
npm run dev
```

Фронтенд будет доступен на `http://localhost:5173`, API на `http://localhost:8000`.

---

## Веса моделей

Веса моделей хранятся в `backend/weights/` и не включены в репозиторий. Ожидаемая структура:

```
backend/weights/
├── xray_model.pth              # EfficientNet для рентгена лёгких
├── cell_clf.pth                # Классификатор клеток крови
├── hip-yolo-xray-pose.pt       # YOLO pose для ТБС
├── hip_classifier.onnx         # EfficientNet-B3 ONNX для дисплазии
└── model_metadata.json         # Конфиг ONNX модели (img_size, threshold, classes)
```

---

## API

После запуска документация доступна по адресу:

- Swagger UI: `http://localhost:8000/docs`

### Основные эндпоинты

| Метод  | Путь                               | Описание                             |
|--------|------------------------------------|--------------------------------------|
| `POST` | `/api/analysis/`                   | Анализ снимка                        |
| `GET`  | `/api/analysis/results/{filename}` | Получить overlay изображение         |
| `GET`  | `/api/analyzers`                   | Список доступных анализаторов        |
| `GET`  | `/health`                          | Статус сервера и загруженных моделей |

### Доступные анализаторы

| `analyzer_id`    | Описание                            |
|------------------|-------------------------------------|
| `xray_pneumonia` | Рентген лёгких                      |
| `hip_dysplasia`  | Дисплазия ТБС (YOLO + EfficientNet) |
| `microscopy`     | Микроскопия крови                   |

---

## Переменные окружения

| Переменная                     | По умолчанию                                                 | Описание                                       |
|--------------------------------|--------------------------------------------------------------|------------------------------------------------|
| `DATABASE_URL`                 | `postgresql+psycopg2://postgres:203669@localhost:5432/itmed` | Строка подключения к БД                        |
| `DEVICE`                       | `cpu`                                                        | Устройство инференса (`cpu` / `cuda`)          |
| `MAX_FILE_SIZE_MB`             | `20`                                                         | Максимальный размер загружаемого файла         |
| `IMAGE_SIZE`                   | `224`                                                        | Размер входного изображения для рентген-модели |
| `DISPLASIYA_YOLO_PATH`         | `backend/weights/hip-yolo-xray-pose.pt`                      | Путь к весам YOLO                              |
| `HIP_EFFICIENTNET_ONNX_PATH`   | `backend/weights/hip_classifier.onnx`                        | Путь к ONNX модели                             |
| `HIP_EFFICIENTNET_CONFIG_PATH` | `backend/weights/model_metadata.json`                        | Путь к конфигу ONNX                            |

---

## Админ-панель

Доступна на фронтенде — кнопка в навигации. Состоит из пяти вкладок:

| Вкладка          | Описание                                                                                                                           |
|------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **Статистика**   | Общее число анализов, % патологий, среднее время обработки, средний балл EDU; разбивка по анализаторам; статус загруженных моделей |
| **История**      | Таблица всех выполненных анализов с фильтрацией                                                                                    |
| **Логи**         | Системные логи в реальном времени (`INFO` / `WARNING` / `ERROR`)                                                                   |
| **Конфигурация** | Редактирование параметров системы на лету (пороги уверенности, веса EDU и др.) через `/api/admin/config`                           |
| **Плагины**      | Загрузка и удаление внешних анализаторов (`.py`) без перезапуска сервера                                                           |

Поддерживается автообновление данных каждые 30 секунд.

## Добавление нового анализатора

Система построена по принципу Open-Closed — новый анализатор добавляется без изменения существующего кода:

```python
from backend.core.registry import register
from backend.core.base import BaseAnalyzer


@register("my_analyzer")
class MyAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(id="my_analyzer", name="Мой анализатор", modality="xray")

    async def analyze(self, image, *, context, **kwargs):
        ...
```

После регистрации анализатор автоматически появляется в `/api/analyzers` и становится доступен через `/api/analysis/`.

---

## Требования

- Python 3.12+
- Node.js 20+ (для фронтенда)
- Docker и Docker Compose (для БД)
- PostgreSQL 16

## Demo

![Photo 1](https://github.com/Vlad1slavS/ITMed/blob/main/pictures/1.png)


![Photo 2](https://github.com/Vlad1slavS/ITMed/blob/main/pictures/2.png)


![Photo 3](https://github.com/Vlad1slavS/ITMed/blob/main/pictures/3.png)
