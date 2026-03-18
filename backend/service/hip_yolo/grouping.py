"""Группировка детекций YOLO по сторонам и нормализация keypoints."""

from __future__ import annotations


def group_by_side(results, model_names: dict) -> dict[str, dict]:
    """
    Группирует hip_pelvis / hip_femour по сторонам (left/right).

    Возвращает:
    {
      "left":  {"conf", "bbox", "kp": {name: (x,y)}, "measurements": {}},
      "right": {"conf", "bbox", "kp": {name: (x,y)}, "measurements": {}},
    }
    """
    pelvis_list: list[dict] = []
    femur_list: list[dict] = []

    for i, box in enumerate(results.boxes):
        label = model_names[int(box.cls[0])]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx = (x1 + x2) / 2.0

        kps = results.keypoints.data[i] if results.keypoints is not None else None
        if kps is None:
            continue

        entry = {
            "label": label,
            "conf": conf,
            "bbox": (x1, y1, x2, y2),
            "cx": cx,
            "kps": kps,
        }
        if label == "hip_pelvis":
            pelvis_list.append(entry)
        elif label == "hip_femour":
            femur_list.append(entry)

    pelvis_list.sort(key=lambda item: item["cx"])
    femur_list.sort(key=lambda item: item["cx"])

    sides: dict[str, dict] = {}
    side_names = ["left", "right"]

    for idx, pelvis in enumerate(pelvis_list[:2]):
        side = side_names[idx] if idx < 2 else f"side_{idx}"
        kp: dict[str, tuple[float, float]] = {}
        kps = pelvis["kps"]

        for j, name in enumerate(["ASM", "TCC"]):
            if j < len(kps):
                kx, ky, kv = float(kps[j][0]), float(kps[j][1]), float(kps[j][2])
                if kv > 0.1:
                    kp[name] = (kx, ky)

        if femur_list:
            closest = min(femur_list, key=lambda item: abs(item["cx"] - pelvis["cx"]))
            fkps = closest["kps"]
            for j, name in enumerate(["FHC", "MOFM"]):
                if j < len(fkps):
                    kx, ky, kv = float(fkps[j][0]), float(fkps[j][1]), float(fkps[j][2])
                    if kv > 0.1:
                        kp[name] = (kx, ky)
            femur_list = [item for item in femur_list if item is not closest]

        sides[side] = {
            "conf": pelvis["conf"],
            "bbox": pelvis["bbox"],
            "kp": kp,
            "measurements": {},
        }

    return sides
