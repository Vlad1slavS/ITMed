from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env.example",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Пути
    BASE_DIR: Path = Path(__file__).parent.parent  # backend/
    RESULTS_DIR: Path = BASE_DIR / "overlays"  # backend/overlays/
    FONTS_DIR: Path = BASE_DIR / "fonts"  # backend/fonts/
    WEIGHTS_DIR: Path = BASE_DIR / "weights"  # backend/weights/

    XRAY_MODEL_PATH: Path = WEIGHTS_DIR / "xray_model.pth"
    MICROSCOPY_MODEL_PATH: Path = WEIGHTS_DIR / "microscopy_model.pt"
    DISPLASIYA_YOLO_PATH: Path = WEIGHTS_DIR / "hip-yolo-xray-pose.pt"
    HIP_EFFICIENTNET_ONNX_PATH: Path = WEIGHTS_DIR / "hip_efficientnet_b3.onnx"
    HIP_EFFICIENTNET_CONFIG_PATH: Path = WEIGHTS_DIR / "hip_efficientnet_b3.json"

    # ML
    IMAGE_SIZE: int = 224
    DEVICE: str = "auto"
    HIP_CONFIDENCE_PATHOLOGY: float = 0.95
    HIP_CONFIDENCE_NORMAL: float = 0.90
    XRAY_ADVANCED_THRESHOLD: float = 0.65

    # Образовательный режим
    EDU_POINTS_EXCELLENT_PX: int = 20
    EDU_POINTS_GOOD_PX: int = 40
    EDU_WEIGHT_POINTS: float = 0.4
    EDU_WEIGHT_QUAL: float = 0.3
    EDU_WEIGHT_DIAGNOSIS: float = 0.3

    # Загрузка файлов
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "bmp", "tiff"]

    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://postgres:203669@localhost:5432/itmed"


settings = Settings()

# Создаём нужные директории
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
settings.WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
