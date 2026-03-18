from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class Modality(str, Enum):
    xray = "xray"
    microscopy = "microscopy"



# RESPONSE SCHEMAS

class ActivationPoint(BaseModel):
    x: int = Field(..., description="Координата X главной точки активации")
    y: int = Field(..., description="Координата Y главной точки активации")


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class PathologyZone(BaseModel):
    zone_id: int
    area_px: int = Field(..., description="Площадь зоны в пикселях")
    area_percent: float = Field(..., description="Процент от площади снимка")
    bounding_box: BoundingBox
    severity: str = Field(
        ..., description="low / medium / high — на основе средней активации"
    )


class DiagnosisResult(BaseModel):
    predicted_class: int
    label: str = Field(..., description="Человекочитаемый диагноз")
    confidence: float = Field(..., description="Уверенность модели 0..1")
    is_pathology: bool


class GradCamResult(BaseModel):
    heatmap_url: str = Field(..., description="URL тепловой карты")
    overlay_url: str = Field(..., description="URL наложения на оригинал")
    main_activation_point: ActivationPoint
    pathology_zones: list[PathologyZone]
    zones_count: int


# Микроскопия: Cellpose + EfficientNet классификатор 


class CellCount(BaseModel):
    WBC: int = 0
    RBC: int = 0
    Platelets: int = 0


class CellDetection(BaseModel):
    cell_id: int
    class_name: str
    confidence: float
    bounding_box: BoundingBox


class MicroscopyResult(BaseModel):
    overlay_url: str = Field(..., description="URL снимка с bbox клеток")
    cell_counts: CellCount
    cell_detections: list[CellDetection] = Field(default_factory=list)
    total_cells: int
    wbc_rbc_ratio: str = Field(..., description="Соотношение WBC/RBC, напр. '1:28'")
    clinical_note: str = Field(..., description="Клиническая интерпретация")


# Дисплазия ТБС: Retuve 


class HipDysplasiaMetric(BaseModel):
    name: str = Field(..., description="Имя метрики (ace_index_left и т.д.)")
    name_ru: str = Field(..., description="Русское название")
    side: str = Field(..., description="left / right / both")
    value: float | str = Field(..., description="Значение метрики (float для углов, str для IHDI/h/d)")
    classification: Optional[str] = Field(None, description="Классификация (Норма, Патология и т.д.)")
    color: Optional[str] = Field(None, description="Цвет для отображения (green, orange, red)")


class HipDysplasiaResult(BaseModel):
    overlay_url: str = Field(..., description="URL снимка с построениями Retuve")
    heatmap_url: Optional[str] = Field(None, description="URL оригинального снимка")
    metrics: list[HipDysplasiaMetric] = Field(..., description="Список метрик с классификацией")
    overall_diagnosis: str = Field(..., description="Комплексный диагноз по всем метрикам")
    educational_info: Optional[str] = Field(None, description="Образовательная информация о нормах")


class AnalysisResponse(BaseModel):
    request_id: str
    analyzer_id: str = Field("xray_pneumonia", description="ID анализатора из registry")
    modality: Modality
    diagnosis: DiagnosisResult
    gradcam: Optional[GradCamResult] = Field(
        None, description="Результат Grad-CAM (только для рентгена)"
    )
    microscopy: Optional[MicroscopyResult] = Field(
        None, description="Результат детекции клеток (только для микроскопии)"
    )
    hip_dysplasia: Optional[HipDysplasiaResult] = Field(
        None, description="Результат анализа дисплазии ТБС (только для рентгена)"
    )
    extra: Optional[dict[str, Any]] = Field(
        None, description="Дополнительные данные специфичные для анализатора"
    )
    model_version: str
    warning: str = (
        "Результат носит информационный характер и не является медицинским заключением"
    )


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class ModelInfo(BaseModel):
    name: str
    modality: Modality
    version: str
    classes: list[str]
    architecture: str
    is_loaded: bool


class HealthResponse(BaseModel):
    status: str
    models_loaded: dict[str, bool]
    device: str
