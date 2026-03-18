import logging
from pathlib import Path
from typing import cast

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from ultralytics.models import YOLO

from backend.app.config import settings
from backend.ml.gradcam import GradCAM
from backend.ml.models import MicroscopyModel, XRayModel
from backend.modules.hip_dysplasia.classifier import (
    EfficientNetOnnxRunner,
)
from backend.schema.schemas import Modality


class ModelManager:
    """
    Синглтон для управления моделями.
    Загружает модели один раз при старте приложения.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger(__name__)
        self.device = self._get_device()
        self.logger.info(f"[ModelManager] Выбрано устройство инференса: {self.device}")

        self.xray_model: XRayModel | None = None
        self.microscopy_model: MicroscopyModel | None = None
        self.xray_gradcam: GradCAM | None = None
        self.xray_weights_loaded = False
        self.microscopy_weights_loaded = False
        self.hip_yolo_model: YOLO | None = None
        self.hip_yolo_loaded = False
        self.hip_efficientnet_runner: EfficientNetOnnxRunner | None = None

        self._load_models()
        self._initialized = True

    def _get_device(self) -> torch.device:
        if settings.DEVICE == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(settings.DEVICE)

    def _load_models(self) -> None:
        # Рентген
        self.logger.info("[ModelManager] Инициализация рентген-модуля")
        self.xray_model = XRayModel().to(self.device)
        xray_path = settings.XRAY_MODEL_PATH

        if not xray_path.exists():
            self.logger.warning(
                f"[ModelManager] ВНИМАНИЕ: веса рентген-модели не найдены ({xray_path}). "
                f"Модель работает с pretrained backbone, результаты могут быть недостоверны."
            )
            self.xray_weights_loaded = False
        else:
            state = torch.load(xray_path, map_location=self.device)
            self.xray_model.load_state_dict(state)
            self.logger.info(f"[ModelManager] Рентген-модель загружена: {xray_path}")
            self.xray_weights_loaded = True

        self.xray_model.eval()
        self._init_xray_gradcam()

        # Микроскопия
        self.logger.info("[ModelManager] Инициализация модуля микроскопии")
        microscopy_path = settings.MICROSCOPY_MODEL_PATH
        if not microscopy_path.exists():
            self.logger.warning(
                f"[ModelManager] ВНИМАНИЕ: веса микроскопии не найдены ({microscopy_path}). "
                f"Анализ крови будет недоступен."
            )
            self.microscopy_model = None
            self.microscopy_weights_loaded = False
        else:
            self.microscopy_model = MicroscopyModel(str(microscopy_path))
            self.logger.info(
                f"[ModelManager] Модель микроскопии загружена: {microscopy_path}"
            )
            self.microscopy_weights_loaded = True

        # YOLO для дисплазии ТБС
        self.logger.info("[ModelManager] Инициализация YOLO модели для ТБС")
        hip_yolo_path = settings.DISPLASIYA_YOLO_PATH
        if not hip_yolo_path.exists():
            self.logger.warning(
                f"[ModelManager] ВНИМАНИЕ: веса YOLO ТБС не найдены ({hip_yolo_path})"
            )
            self.hip_yolo_model = None
            self.hip_yolo_loaded = False
        else:
            self.hip_yolo_model = YOLO(str(hip_yolo_path))
            self.logger.info(f"[ModelManager] YOLO ТБС загружена: {hip_yolo_path}")
            self.hip_yolo_loaded = True

        self.logger.info("[ModelManager] Инициализация EfficientNet классификатора ТБС")
        onnx_path = settings.HIP_EFFICIENTNET_ONNX_PATH
        config_path = settings.HIP_EFFICIENTNET_CONFIG_PATH
        if not onnx_path.exists():
            self.logger.warning(
                f"[ModelManager] ВНИМАНИЕ: ONNX классификатор не найден ({onnx_path})"
            )
        else:
            self.load_hip_efficientnet(onnx_path, config_path)

    def _init_xray_gradcam(self) -> None:
        if self.xray_model is None:
            self.logger.warning(
                "[ModelManager] Нельзя инициализировать Grad-CAM: рентген-модель отсутствует"
            )
            self.xray_gradcam = None
            return

        # Для EfficientNet-B3 берем последнюю сверточную карту признаков.
        target_layer = getattr(self.xray_model.backbone, "conv_head", None)
        if target_layer is None:
            self.logger.error(
                "[ModelManager] Не найден target layer для Grad-CAM (conv_head)"
            )
            self.xray_gradcam = None
            return

        self.xray_gradcam = GradCAM(self.xray_model, target_layer)
        self.logger.info("[ModelManager] Grad-CAM для рентгена успешно инициализирован")

    def get_model(self, modality: Modality | str):
        modality_value = modality.value if isinstance(modality, Modality) else str(modality)

        if modality_value == Modality.xray.value:
            return self.xray_model
        if modality_value in {"hip_dysplasia", "displasiya"}:
            return self.hip_yolo_model
        if modality_value == Modality.microscopy.value:
            return self.microscopy_model

        self.logger.warning(
            "[ModelManager] Неизвестная модальность в get_model: %s",
            modality_value,
        )
        return None

    def get_gradcam(self, modality: Modality) -> GradCAM | None:
        if modality == Modality.xray:
            return self.xray_gradcam
        return None

    def get_class_names(self, modality: Modality) -> list[str]:
        if modality == Modality.xray:
            return XRayModel.CLASS_NAMES
        if self.microscopy_model is not None:
            return self.microscopy_model.CLASSES
        return MicroscopyModel.CLASSES

    def is_loaded(self, modality: Modality | str) -> bool:
        modality_value = modality.value if isinstance(modality, Modality) else str(modality)

        if modality_value == Modality.xray.value:
            return bool(self.xray_weights_loaded)
        if modality_value == Modality.microscopy.value:
            return bool(self.microscopy_weights_loaded)
        if modality_value in {"hip_dysplasia", "displasiya"}:
            return bool(self.hip_yolo_loaded)

        self.logger.warning(
            "[ModelManager] Неизвестная модальность в is_loaded: %s",
            modality_value,
        )
        return False

    def load_hip_efficientnet(self, onnx_path: Path, config_path: Path) -> None:
        if not onnx_path.exists():
            self.logger.warning(f"[ModelManager] ONNX не найден: {onnx_path}")
            return
        if not config_path.exists():
            self.logger.warning(f"[ModelManager] JSON конфиг не найден: {config_path}")
            return
        try:
            self.hip_efficientnet_runner = EfficientNetOnnxRunner(onnx_path, config_path)
        except Exception as e:
            self.logger.error(f"[ModelManager] Ошибка загрузки EfficientNet ONNX: {e}")

    @property
    def transform(self) -> transforms.Compose:
        return transforms.Compose(
            [
                transforms.Resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def preprocess(self, image: Image.Image) -> tuple[torch.Tensor, np.ndarray]:
        """Препроцессинг для рентгена (EfficientNet-B3)."""
        image_rgb = image.convert("RGB")
        image_resized = image_rgb.resize(
            (settings.IMAGE_SIZE, settings.IMAGE_SIZE),
            Image.Resampling.LANCZOS,
        )
        original_np = np.array(image_resized)
        tensor = (
            cast(torch.Tensor, self.transform(image_resized))
            .unsqueeze(0)
            .to(self.device)
        )
        return tensor, original_np

    def preprocess_microscopy(self, image: Image.Image) -> np.ndarray:
        """Препроцессинг для микроскопии (Cellpose принимает np.ndarray RGB)."""
        return np.array(image.convert("RGB"))


# Глобальный экземпляр
model_manager = ModelManager()
