import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import backend.modules
from backend.app.config import settings
from backend.core.registry import list_analyzers
from backend.db import models
from backend.db.database import SessionLocal, engine, log_to_db
from backend.ml.model_manager import model_manager

# Импорт модулей -> авто-регистрация анализаторов в core.registry
from backend.routers import admin, educational, routers_analysis, utils
from backend.schema.schemas import HealthResponse, Modality
from backend.service.admin.plugin_service import load_saved_plugins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Medical Diagnostics API",
    description=(
        "Платформа для диагностики патологий по медицинским изображениям.\n\n"
        "Модули анализа подключаются через core/registry — расширяемая архитектура."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers_analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(utils.router, prefix="/api/utils", tags=["utils"])
app.include_router(educational.router, prefix="/api/educational", tags=["educational"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
def root():
    logger.info("[System] Запрошен корневой endpoint")
    return {"service": "Medical Diagnostics", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        status="ok",
        models_loaded={
            "xray": model_manager.is_loaded(Modality.xray),
            "microscopy": model_manager.is_loaded(Modality.microscopy),
        },
        device=str(model_manager.device),
    )


@app.get("/api/analyzers", tags=["system"])
def get_available_analyzers():
    """Список доступных анализаторов."""
    analyzers = list_analyzers()
    logger.info(f"[System] Запрошен список анализаторов: count={len(analyzers)}")
    return analyzers


@app.on_event("startup")
def startup() -> None:
    logger.info("[System] Инициализация приложения: создание таблиц")
    models.Base.metadata.create_all(bind=engine)
    load_saved_plugins()
    print("WEIGHTS_DIR:", settings.WEIGHTS_DIR)
    print("XRAY exists:", settings.XRAY_MODEL_PATH.exists())
    print("MICROSCOPY exists:", settings.MICROSCOPY_MODEL_PATH.exists())
    logger.info(
        f"[Config] Пути к весам: WEIGHTS_DIR={settings.WEIGHTS_DIR}, "
        f"XRAY_MODEL_PATH={settings.XRAY_MODEL_PATH}, "
        f"MICROSCOPY_MODEL_PATH={settings.MICROSCOPY_MODEL_PATH}"
    )

    # Применить сохраненные конфиги из БД к settings
    db = None
    try:
        db = SessionLocal()
        saved = db.query(models.ConfigEntry).all()
        for entry in saved:
            if hasattr(settings, entry.key):
                if entry.value_type == "float":
                    setattr(settings, entry.key, float(entry.value))
                elif entry.value_type == "int":
                    setattr(settings, entry.key, int(entry.value))
                elif entry.value_type == "bool":
                    setattr(settings, entry.key, str(entry.value).lower() == "true")
                else:
                    setattr(settings, entry.key, entry.value)
        logger.info(f"[Config] Загружено конфигов из БД: {len(saved)}")
    except Exception as e:
        logger.warning(f"[Config] Не удалось загрузить конфиги из БД: {e}")
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    log_to_db("INFO", "system", "Сервер запущен")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
