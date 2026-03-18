from typing import cast

import timm
import torch
import torch.nn as nn
from torchvision import models as tv_models

from backend.app.config import settings


class XRayModel(nn.Module):
    """
    Модель для анализа рентгеновских снимков.
    Классификация: Норма / Пневмония
    """

    NUM_CLASSES = 2
    CLASS_NAMES = ["Норма", "Пневмония"]
    VERSION = "1.0.0"
    ARCHITECTURE = "EfficientNet-B3"

    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model(
            "efficientnet_b3",
            pretrained=True,
            num_classes=0,
            global_pool="",  # отключаем пулинг внутри backbone
        )
        in_features: int = cast(int, self.backbone.num_features)

        self.pool = nn.AdaptiveAvgPool2d(1)  # явный пулинг для GradCAM
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, self.NUM_CLASSES),
        )

    def forward(self, x):
        features = self.backbone(x)  # [B, 1536, 7, 7]
        pooled = self.pool(features)  # [B, 1536, 1, 1]
        pooled = pooled.flatten(1)  # [B, 1536]
        return self.classifier(pooled)


class MicroscopyModel:
    """
    Пайплайн для детекции клеток крови:
    Cellpose сегментация → EfficientNet-B0 классификатор по кропам.

    Классы: WBC, RBC, Platelets
    Для каждого класса задан порог уверенности — ниже порога → fallback на RBC.
    """

    VERSION = "1.0.0"
    ARCHITECTURE = "Cellpose + EfficientNet-B0"
    CLASSES = ["Platelets", "RBC", "WBC"]

    # Порог уверенности
    CONFIDENCE_THRESHOLDS = {
        "WBC": 0.60,
        "Platelets": 0.75,
        "RBC": 0.00,
    }

    COLORS = {
        "RBC": (255, 80, 80),
        "WBC": (80, 160, 255),
        "Platelets": (80, 220, 120),
    }

    # Cellpose параметры
    CP_DIAMETER = 130
    CP_FLOW_THRESHOLD = 0.7
    CP_CELLPROB_THRESHOLD = -4.0

    def __init__(self, weights_path: str, img_size: int = 64):

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.img_size = img_size

        # Классификатор 
        ckpt = torch.load(weights_path, map_location=self.device)

        # Порядок классов берём из чекпоинта, если есть
        if "classes" in ckpt:
            self.CLASSES = ckpt["classes"]
        if "img_size" in ckpt:
            self.img_size = ckpt["img_size"]

        clf = tv_models.efficientnet_b0(weights=None)
        in_features = cast(int, clf.classifier[1].in_features)  
        clf.classifier = nn.Sequential(
            nn.Dropout(0.3), nn.Linear(in_features, len(self.CLASSES))
        )
        clf.load_state_dict(ckpt["model_state"])
        self.classifier = clf.eval().to(self.device)

        from cellpose import models as cp_models

        self.cellpose = cp_models.CellposeModel(gpu=torch.cuda.is_available())

        from torchvision import transforms

        self.transform = transforms.Compose(
            [
                transforms.Resize((self.img_size, self.img_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    def __call__(self, x):
        return self.classifier(x)

    def predict(self, image_np):
        """
        image_np: np.ndarray RGB [H, W, 3]
        Возвращает список dict с ключами: cell_id, class, confidence, slice, mask_crop
        """
        import numpy as np
        import torch
        from PIL import Image
        from scipy.ndimage import find_objects

        # Сегментация 
        masks, flows, styles, *_ = self.cellpose.eval(
            image_np,
            diameter=self.CP_DIAMETER,
            channels=[0, 0],
            flow_threshold=self.CP_FLOW_THRESHOLD,
            cellprob_threshold=self.CP_CELLPROB_THRESHOLD,
        )

        slices = find_objects(masks)
        rbc_idx = self.CLASSES.index("RBC")
        results = []

        with torch.no_grad():
            for i, slc in enumerate(slices):
                if slc is None:
                    continue

                # Зануляем фон по маске Cellpose
                crop_np = image_np[slc].copy()
                cell_mask_crop = masks[slc] == i + 1
                crop_np[~cell_mask_crop] = 0

                crop_pil = Image.fromarray(crop_np).convert("RGB")
                transformed = cast(torch.Tensor, self.transform(crop_pil))
                tensor = transformed.unsqueeze(0).to(self.device)

                probs = torch.softmax(self.classifier(tensor), dim=1)[0]
                idx = int(probs.argmax().item())
                cls_name = self.CLASSES[idx]
                confidence = probs[idx].item()

                # Порог уверенности → fallback на RBC
                threshold = self.CONFIDENCE_THRESHOLDS.get(cls_name, 0.0)
                if confidence < threshold:
                    idx = rbc_idx
                    cls_name = "RBC"
                    confidence = probs[rbc_idx].item()

                results.append(
                    {
                        "cell_id": i + 1,
                        "class": cls_name,
                        "confidence": round(confidence, 3),
                        "slice": slc,
                    }
                )

        return masks, results
