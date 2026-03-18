"""
Модуль: Расширенный анализ рентгена — 18 патологий.
Архитектура: DenseNet121 (torchxrayvision) + Grad-CAM топ-3.
"""
from __future__ import annotations

import uuid
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from backend.app.config import settings
from backend.core.base import AnalysisContext, BaseAnalyzer
from backend.core.registry import register
from backend.schema.schemas import (
    AnalysisResponse,
    DiagnosisResult,
    GradCamResult,
    ActivationPoint,
    Modality,
)
from backend.service.image_utils import save_overlay

PATHOLOGY_META: dict[str, dict] = {
    "Pneumonia":                  {"ru": "Пневмония",              "severity": "high"},
    "Pneumothorax":               {"ru": "Пневмоторакс",           "severity": "high"},
    "Effusion":                   {"ru": "Плевральный выпот",      "severity": "high"},
    "Edema":                      {"ru": "Отёк лёгких",            "severity": "high"},
    "Cardiomegaly":               {"ru": "Кардиомегалия",          "severity": "medium"},
    "Atelectasis":                {"ru": "Ателектаз",              "severity": "medium"},
    "Consolidation":              {"ru": "Консолидация",           "severity": "medium"},
    "Infiltration":               {"ru": "Инфильтрация",           "severity": "medium"},
    "Mass":                       {"ru": "Образование",            "severity": "high"},
    "Nodule":                     {"ru": "Узелок",                 "severity": "medium"},
    "Emphysema":                  {"ru": "Эмфизема",               "severity": "medium"},
    "Fibrosis":                   {"ru": "Фиброз",                 "severity": "medium"},
    "Pleural_Thickening":         {"ru": "Утолщение плевры",       "severity": "low"},
    "Hernia":                     {"ru": "Грыжа",                  "severity": "low"},
    "Lung Lesion":                {"ru": "Поражение лёгкого",      "severity": "high"},
    "Fracture":                   {"ru": "Перелом",                "severity": "medium"},
    "Lung Opacity":               {"ru": "Затемнение лёгкого",     "severity": "medium"},
    "Enlarged Cardiomediastinum": {"ru": "Расширение средостения", "severity": "medium"},
}

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_model = None


def _get_model():
    global _model
    if _model is None:
        import torchxrayvision as xrv
        _model = xrv.models.DenseNet(weights="densenet121-res224-all")
        _model.eval()
    return _model


def _preprocess(image: Image.Image) -> torch.Tensor:
    import torchvision
    import torchxrayvision as xrv

    img_np = np.array(image.convert("L")).astype(np.float32)
    img_np = xrv.datasets.normalize(img_np, 255)
    img_np = img_np[None, ...]
    transform = torchvision.transforms.Compose([
        xrv.datasets.XRayCenterCrop(),
        xrv.datasets.XRayResizer(224),
    ])
    return torch.from_numpy(transform(img_np))


def _build_gradcam(model, tensor, class_idx, original_np):
    """Grad-CAM для одного класса — возвращает (heatmap_url, overlay_url)."""
    gradients, activations = [], []

    def fwd_hook(module, inp, out):
        activations.append(out)
        out.register_hook(lambda g: gradients.append(g))

    handle = model.features.norm5.register_forward_hook(fwd_hook)
    model.zero_grad()

    inp = tensor[None, ...].detach().requires_grad_(True)
    out = model(inp)
    out[0, class_idx].backward()
    handle.remove()

    grads = gradients[0].detach().cpu().numpy()[0]
    acts  = activations[0].detach().cpu().numpy()[0]
    weights = grads.mean(axis=(1, 2))
    cam = np.maximum(np.sum(weights[:, None, None] * acts, axis=0), 0)

    h, w = original_np.shape[:2]
    if cam.max() > 0:
        cam = (cam - cam.min()) / (cam.max() - cam.min())
    cam = cv2.resize(cam, (w, h))

    heatmap = cv2.cvtColor(
        cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET),
        cv2.COLOR_BGR2RGB,
    )
    overlay = cv2.addWeighted(original_np.astype(np.uint8), 0.6, heatmap, 0.4, 0)

    fid = str(uuid.uuid4())[:8]
    heatmap_url = save_overlay(heatmap,  f"{fid}_adv_heatmap.jpg")
    overlay_url = save_overlay(overlay,  f"{fid}_adv_overlay.jpg")
    return heatmap_url, overlay_url


@register("xray_advanced")
class XRayAdvancedAnalyzer(BaseAnalyzer):
    """DenseNet121 — 18 патологий + Grad-CAM топ-3."""

    NAME = "Рентген расширенный — 18 патологий"

    def __init__(self, **_: Any) -> None:
        super().__init__(id="xray_advanced", name=self.NAME, modality="xray")

    async def analyze(
        self,
        image: Image.Image,
        *,
        context: AnalysisContext,
        **_: Any,
    ) -> AnalysisResponse:
        request_id = context.request_id or str(uuid.uuid4())[:8]

        model  = _get_model()
        tensor = _preprocess(image)

        with torch.no_grad():
            probs = model(tensor[None, ...])[0].numpy()

        scored = []
        threshold = settings.XRAY_ADVANCED_THRESHOLD
        for i, (name, prob) in enumerate(zip(model.pathologies, probs)):
            if name not in PATHOLOGY_META:
                continue
            scored.append({
                "name":      name,
                "name_ru":   PATHOLOGY_META[name]["ru"],
                "score":     round(float(prob), 4),
                "severity":  PATHOLOGY_META[name]["severity"],
                "detected":  float(prob) >= threshold,
                "class_idx": i,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        detected = [e for e in scored if e["detected"]]

        is_pathology = bool(detected)
        top = next((e for e in detected if e["severity"] == "high"), None) \
              or (detected[0] if detected else scored[0])

        # Grad-CAM топ-3
        original_np = np.array(image.resize((224, 224)).convert("RGB"))
        top3 = sorted(
            detected or scored,
            key=lambda x: (_SEVERITY_ORDER.get(x["severity"], 9), -x["score"])
        )[:3]

        gradcam_list = []
        for entry in top3:
            h_url, o_url = _build_gradcam(model, tensor, entry["class_idx"], original_np)
            gradcam_list.append({
                "pathology":    entry["name"],
                "pathology_ru": entry["name_ru"],
                "score":        entry["score"],
                "severity":     entry["severity"],
                "heatmap_url":  h_url,
                "overlay_url":  o_url,
            })

        # Убираем class_idx из ответа
        for e in scored:
            e.pop("class_idx", None)

        # Уверенность
        if is_pathology:
            confidence = round(top["score"], 4)
        else:
            high_scores = [e["score"] for e in scored if e["severity"] == "high"]
            confidence = round(1.0 - max(high_scores), 4) if high_scores else 0.9

        # Берём overlay топ-1 для основного GradCamResult
        main_gc = gradcam_list[0] if gradcam_list else None

        return AnalysisResponse(
            request_id=request_id,
            analyzer_id="xray_advanced",
            modality=Modality.xray,
            diagnosis=DiagnosisResult(
                predicted_class=1 if is_pathology else 0,
                label=top["name_ru"] if is_pathology else "Патологий не выявлено",
                confidence=confidence,
                is_pathology=is_pathology,
            ),
            gradcam=GradCamResult(
                heatmap_url=main_gc["heatmap_url"] if main_gc else "",
                overlay_url=main_gc["overlay_url"] if main_gc else "",
                main_activation_point=ActivationPoint(x=112, y=112),
                pathology_zones=[],
                zones_count=0,
            ) if main_gc else None,
            microscopy=None,
            hip_dysplasia=None,
            model_version="densenet121-res224-all",
            # Дополнительные поля для фронта
            extra={
                "gradcam_multi": gradcam_list,
                "pathologies":   scored,
                "detected":      detected,
                "detected_count": len(detected),
            }
        )
