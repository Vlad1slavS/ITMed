from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
import torch


@dataclass
class GradCAMOutput:
    cam: np.ndarray  # нормализованная карта активаций [0..1]
    heatmap: np.ndarray  # тепловая карта RGB
    overlay: np.ndarray  # наложение на оригинал RGB
    main_point: tuple  # (y, x) главной активации
    contours: list = field(default_factory=list)  # список контуров зон патологий


class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None

        target_layer.register_forward_hook(self._save_activations)
        target_layer.register_full_backward_hook(self._save_gradients)

    def _save_activations(self, module, input, output):
        self.activations = output.detach()

    def _save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(
        self, input_tensor: torch.Tensor, class_idx: Optional[int] = None
    ) -> tuple[np.ndarray, int]:
        self.model.eval()
        raw_output = self.model(input_tensor)

        output = raw_output[1] if isinstance(raw_output, (tuple, list)) else raw_output

        if class_idx is None:
            class_idx = int(output.argmax(dim=1).item())

        self.model.zero_grad()
        score = output[0, class_idx]
        score.backward()

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations not captured.")

        weights = torch.clamp(self.gradients, min=0).mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)

        cam = torch.relu(cam)
        cam_np: np.ndarray = cam.squeeze().detach().cpu().numpy()

        cam_min, cam_max = cam_np.min(), cam_np.max()
        cam_np = (cam_np - cam_min) / (cam_max - cam_min + 1e-8)

        return cam_np, class_idx

    def process(
        self,
        input_tensor: torch.Tensor,
        original_image: np.ndarray,
        class_idx: Optional[int] = None,
        threshold: float = 0.6,
    ) -> GradCAMOutput:
        cam, predicted_class = self.generate(input_tensor, class_idx)

        h, w = original_image.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))

        cam_uint8 = (255 * cam_resized).astype(np.uint8)
        heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

        original_uint8 = original_image.astype(np.uint8)
        overlay = cv2.addWeighted(original_uint8, 0.55, heatmap, 0.45, 0)

        max_idx = cam_resized.argmax()
        main_point = np.unravel_index(max_idx, cam_resized.shape)
        cx, cy = int(main_point[1]), int(main_point[0])

        overlay_marked = overlay.copy()
        cv2.circle(overlay_marked, (cx, cy), 10, (255, 50, 50), -1)
        cv2.circle(overlay_marked, (cx, cy), 14, (255, 255, 255), 2)

        binary = ((cam_resized > threshold) * 255).astype(np.uint8)
        contours_raw, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = list(contours_raw)

        cv2.drawContours(overlay_marked, contours, -1, (255, 230, 0), 2)

        return GradCAMOutput(
            cam=cam_resized,
            heatmap=heatmap,
            overlay=overlay_marked,
            main_point=(cy, cx),
            contours=contours,
        )
