import base64
import io
import logging

import cv2
import numpy as np
import pydicom
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from backend.service.dicom_age_service import extract_patient_age_from_dicom

logger = logging.getLogger(__name__)
router = APIRouter()


def _dicom_to_image(contents: bytes) -> Image.Image:
    """
    Конвертирует DICOM байты в PIL Image с правильным windowing.
    Пробует несколько способов чтения.
    """
    # Пробуем с force=True — работает для файлов без заголовка DICM
    try:
        ds = pydicom.dcmread(io.BytesIO(contents), force=True)
    except Exception as e:
        raise ValueError(f"Не удалось прочитать DICOM: {e}")

    try:
        arr = ds.pixel_array
    except Exception as e:
        raise ValueError(f"Не удалось извлечь пиксели: {e}")

    arr = arr.astype(np.float32)

    # Применяем window center/width из метаданных если есть
    wc = getattr(ds, "WindowCenter", None)
    ww = getattr(ds, "WindowWidth", None)
    if wc is not None and ww is not None:
        try:
            wc = float(wc) if not hasattr(wc, "__iter__") else float(list(wc)[0])
            ww = float(ww) if not hasattr(ww, "__iter__") else float(list(ww)[0])
            arr = np.clip(arr, wc - ww / 2, wc + ww / 2)
        except Exception:
            pass  # если не удалось — просто нормализуем по min/max

    # Нормализация в 0-255
    arr_min, arr_max = arr.min(), arr.max()
    if arr_max > arr_min:
        arr = (arr - arr_min) / (arr_max - arr_min) * 255.0
    else:
        arr = np.zeros_like(arr)
    arr = arr.astype(np.uint8)

    # Grayscale → RGB
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
    elif arr.ndim == 3 and arr.shape[2] == 1:
        arr = cv2.cvtColor(arr[:, :, 0], cv2.COLOR_GRAY2RGB)

    return Image.fromarray(arr)


def _apply_clahe(image: Image.Image) -> Image.Image:
    """Улучшает контраст через CLAHE."""
    img_np = np.array(image.convert("RGB"))
    lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img_np = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB)
    return Image.fromarray(img_np)


@router.post("/preview")
async def preview(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename or ""
    logger.info(
        f"[Preview] filename={filename}, size={len(contents)}, magic={contents[128:132] if len(contents) > 132 else b''}"
    )

    # Определяем DICOM по magic bytes или расширению
    is_dcm_magic = len(contents) > 132 and contents[128:132] == b"DICM"
    is_dcm_ext = filename.lower().endswith(".dcm")
    # Файлы без расширения с именем из цифр — скорее всего DICOM
    is_no_ext = "." not in filename

    age_info = None
    if is_dcm_magic or is_dcm_ext or is_no_ext:
        age_info = extract_patient_age_from_dicom(contents)
        try:
            image = _dicom_to_image(contents)
            image = _apply_clahe(image)
            logger.info(f"[Preview] DICOM успешно прочитан: size={image.size}")
        except ValueError as e:
            logger.warning(f"[Preview] DICOM ошибка: {e}, пробуем PIL")
            # Пробуем открыть как обычное изображение
            try:
                image = Image.open(io.BytesIO(contents)).convert("RGB")
            except Exception:
                raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {e}")
    else:
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Не удалось открыть изображение: {e}")

    # Масштабируем сохраняя пропорции, максимум 600x600
    image.thumbnail((600, 600), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    logger.info(f"[Preview] Превью готово, base64 length={len(b64)}")
    return {
        "preview": f"data:image/jpeg;base64,{b64}",
        "patient_age_months": age_info.age_months if age_info else None,
        "patient_age_display": age_info.display if age_info else None,
        "patient_age_source": age_info.source if age_info else None,
    }
