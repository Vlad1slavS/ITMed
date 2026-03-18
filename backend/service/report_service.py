import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
)
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.app.config import settings


# Регистрация шрифтов с поддержкой кириллицы

pdfmetrics.registerFont(TTFont("DejaVu", f"{settings.FONTS_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(
    TTFont("DejaVu-Bold", f"{settings.FONTS_DIR}/DejaVuSans-Bold.ttf")
)
pdfmetrics.registerFont(
    TTFont("DejaVu-Italic", f"{settings.FONTS_DIR}/DejaVuSans-Oblique.ttf")
)

FONT_NORMAL = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_ITALIC = "DejaVu-Italic"



# Цвета

ACCENT = colors.HexColor("#0066ff")
DANGER = colors.HexColor("#ef4444")
SUCCESS = colors.HexColor("#00c896")
WARNING = colors.HexColor("#f59e0b")
MUTED = colors.HexColor("#64748b")
BG_LIGHT = colors.HexColor("#f8fafc")
BORDER = colors.HexColor("#e2e8f0")
DARK = colors.HexColor("#0f172a")
BODY = colors.HexColor("#334155")



# Стили

def _build_styles() -> dict:
    return {
        "title": ParagraphStyle(
            "ITMedTitle",
            fontName=FONT_BOLD,
            fontSize=22,
            textColor=DARK,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "ITMedSubtitle",
            fontName=FONT_NORMAL,
            fontSize=10,
            textColor=MUTED,
            spaceAfter=16,
        ),
        "section": ParagraphStyle(
            "ITMedSection",
            fontName=FONT_BOLD,
            fontSize=11,
            textColor=DARK,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ITMedBody",
            fontName=FONT_NORMAL,
            fontSize=10,
            textColor=BODY,
            leading=16,
        ),
        "small": ParagraphStyle(
            "ITMedSmall",
            fontName=FONT_NORMAL,
            fontSize=8,
            textColor=MUTED,
            leading=12,
        ),
        "disclaimer": ParagraphStyle(
            "ITMedDisclaimer",
            fontName=FONT_ITALIC,
            fontSize=8,
            textColor=MUTED,
            leading=12,
            borderColor=WARNING,
            borderWidth=1,
            borderPadding=8,
            backColor=colors.HexColor("#fffbeb"),
        ),
    }



# Секции PDF

def _section_header(story: list, styles: dict) -> None:
    story.append(Paragraph("ITMed", styles["title"]))
    story.append(Paragraph("Система медицинской нейросетевой диагностики", styles["subtitle"]))
    story.append(
        Table(
            [[""]],
            colWidths=[17 * cm],
            style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.5, ACCENT)]),
        )
    )
    story.append(Spacer(1, 12))


def _section_meta(story: list, styles: dict, data: dict) -> None:
    modality_label = (
        "Рентген (X-Ray)" if data.get("modality") == "xray" else "УЗИ (Ultrasound)"
    )
    model_label = (
        "EfficientNet-B3 + Grad-CAM"
        if data.get("modality") == "xray"
        else "U-Net сегментация"
    )

    meta_data = [
        ["ID исследования", data.get("request_id", "—")],
        ["Дата и время", datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Тип исследования", modality_label],
        ["Модель", model_label],
    ]
    story.append(
        Table(
            meta_data,
            colWidths=[5 * cm, 12 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), BG_LIGHT),
                    ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
                    ("FONTNAME", (1, 0), (1, -1), FONT_NORMAL),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                    ("TEXTCOLOR", (1, 0), (1, -1), DARK),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, BG_LIGHT]),
                ]
            ),
        )
    )
    story.append(Spacer(1, 16))


def _section_diagnosis(story: list, styles: dict, data: dict) -> None:
    story.append(Paragraph("Результат диагностики", styles["section"]))

    diag = data.get("diagnosis", {})
    is_pathology = diag.get("is_pathology", False)
    label = diag.get("label", "—")
    conf_pct = f"{round(diag.get('confidence', 0) * 100)}%"
    status_text = "ПАТОЛОГИЯ ОБНАРУЖЕНА" if is_pathology else "НОРМА"
    status_color = DANGER if is_pathology else SUCCESS
    status_hex = "ef4444" if is_pathology else "00c896"

    diag_data = [
        [
            Paragraph(
                f'<font color="#{status_hex}" size="14"><b>{status_text}</b></font>',
                styles["body"],
            ),
            Paragraph(
                f'<font size="9" color="#64748b">Диагноз</font><br/><b>{label}</b>',
                styles["body"],
            ),
            Paragraph(
                f'<font size="9" color="#64748b">Уверенность</font><br/><font size="18" color="#0066ff"><b>{conf_pct}</b></font>',
                styles["body"],
            ),
        ]
    ]
    story.append(
        Table(
            diag_data,
            colWidths=[5 * cm, 8 * cm, 4 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("PADDING", (0, 0), (-1, -1), 12),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEABOVE", (0, 0), (-1, 0), 3, status_color),
                ]
            ),
        )
    )
    story.append(Spacer(1, 16))


def _section_images(story: list, styles: dict, gradcam: dict) -> None:
    story.append(Paragraph("Визуализация Grad-CAM", styles["section"]))

    img_cells, img_labels = [], []
    for url, lbl in [
        (gradcam.get("overlay_url", ""), "Наложение Grad-CAM"),
        (gradcam.get("heatmap_url", ""), "Тепловая карта"),
    ]:
        if url:
            img_path = settings.RESULTS_DIR / url.split("/")[-1]
            if img_path.exists():
                img_cells.append(
                    RLImage(str(img_path), width=7.5 * cm, height=7.5 * cm)
                )
                img_labels.append(Paragraph(lbl, styles["small"]))

    if not img_cells:
        return

    while len(img_cells) < 2:
        img_cells.append("")
        img_labels.append("")

    story.append(
        Table(
            [img_cells, img_labels],
            colWidths=[8.5 * cm, 8.5 * cm],
            style=TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, 0), 0.5, BORDER),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d1117")),
                ]
            ),
        )
    )
    story.append(Spacer(1, 16))


def _section_zones(story: list, styles: dict, zones: list) -> None:
    story.append(Paragraph(f"Зоны патологий ({len(zones)})", styles["section"]))

    severity_labels = {"low": "Низкая", "medium": "Средняя", "high": "Высокая"}
    severity_hex = {"low": "00c896", "medium": "f59e0b", "high": "ef4444"}

    rows = [
        [
            Paragraph("<b>Зона</b>", styles["small"]),
            Paragraph("<b>Площадь</b>", styles["small"]),
            Paragraph("<b>Тяжесть</b>", styles["small"]),
        ]
    ]
    for z in zones:
        sev = z.get("severity", "low")
        rows.append(
            [
                Paragraph(f"#{z.get('zone_id', '?')}", styles["body"]),
                Paragraph(f"{z.get('area_percent', 0)}% площади", styles["body"]),
                Paragraph(
                    f'<font color="#{severity_hex[sev]}"><b>{severity_labels.get(sev, sev)}</b></font>',
                    styles["body"],
                ),
            ]
        )

    story.append(
        Table(
            rows,
            colWidths=[3 * cm, 7 * cm, 7 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ]
            ),
        )
    )
    story.append(Spacer(1, 16))


def _section_comment(story: list, styles: dict, comment: str) -> None:
    story.append(Paragraph("Комментарий врача", styles["section"]))

    if comment:
        story.append(Paragraph(comment, styles["body"]))
    else:
        story.append(
            Table(
                [[Paragraph("<i>Комментарий не добавлен</i>", styles["small"])]],
                colWidths=[17 * cm],
                style=TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                        ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                        ("PADDING", (0, 0), (-1, -1), 12),
                    ]
                ),
            )
        )


def _section_disclaimer(story: list, styles: dict) -> None:
    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            "ВАЖНО: Данный отчёт сформирован автоматически системой искусственного интеллекта "
            "и носит исключительно информационный характер. Результаты не являются медицинским "
            "заключением и не могут заменить консультацию квалифицированного врача.",
            styles["disclaimer"],
        )
    )




def generate_pdf_report(data: dict) -> io.BytesIO:
    """
    Принимает словарь с результатами анализа (AnalysisResponse.model_dump()).
    Возвращает BytesIO с готовым PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story: list = []

    _section_header(story, styles)
    _section_meta(story, styles, data)
    _section_diagnosis(story, styles, data)

    gradcam = data.get("gradcam")
    if gradcam:
        _section_images(story, styles, gradcam)
        zones = gradcam.get("pathology_zones", [])
        if zones:
            _section_zones(story, styles, zones)

    _section_comment(story, styles, data.get("comment", ""))
    _section_disclaimer(story, styles)

    doc.build(story)
    buffer.seek(0)
    return buffer
