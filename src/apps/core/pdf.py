from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse


PDF_FONT_NAME = "MyInventorySans"
PDF_FALLBACK_FONT = "Helvetica"
_registered_font_name = None


def _load_reportlab():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF generation requires the 'reportlab' package.") from exc

    return {
        "A4": A4,
        "colors": colors,
        "getSampleStyleSheet": getSampleStyleSheet,
        "LongTable": LongTable,
        "Paragraph": Paragraph,
        "ParagraphStyle": ParagraphStyle,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
        "TTFont": TTFont,
        "mm": mm,
        "pdfmetrics": pdfmetrics,
    }


def _get_pdf_font_name():
    global _registered_font_name
    if _registered_font_name:
        return _registered_font_name

    reportlab = _load_reportlab()
    pdfmetrics = reportlab["pdfmetrics"]
    TTFont = reportlab["TTFont"]

    font_candidates = [
        settings.BASE_DIR / "var" / "fonts" / "DejaVuSans.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]

    for font_path in font_candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(font_path)))
            _registered_font_name = PDF_FONT_NAME
            return _registered_font_name

    _registered_font_name = PDF_FALLBACK_FONT
    return _registered_font_name


def build_pdf_styles():
    reportlab = _load_reportlab()
    ParagraphStyle = reportlab["ParagraphStyle"]
    getSampleStyleSheet = reportlab["getSampleStyleSheet"]

    font_name = _get_pdf_font_name()
    styles = getSampleStyleSheet()

    styles["Title"].fontName = font_name
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22
    styles["Title"].spaceAfter = 10

    styles["Heading2"].fontName = font_name
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceBefore = 10
    styles["Heading2"].spaceAfter = 8

    styles["BodyText"].fontName = font_name
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 13
    styles["BodyText"].spaceAfter = 6

    styles.add(
        ParagraphStyle(
            name="PdfMeta",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor="#5F6C7B",
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PdfTableHeader",
            parent=styles["BodyText"],
            fontSize=9,
            leading=11,
            textColor="#153B66",
        )
    )

    return styles


def pdf_paragraph(text, style, *, paragraph_class=None):
    paragraph_class = paragraph_class or _load_reportlab()["Paragraph"]
    safe_text = escape(str(text or ""))
    safe_text = safe_text.replace("\n", "<br/>")
    return paragraph_class(safe_text, style)


def build_kv_table(rows, styles, *, col_widths=None):
    reportlab = _load_reportlab()
    colors = reportlab["colors"]
    Paragraph = reportlab["Paragraph"]
    Table = reportlab["Table"]
    TableStyle = reportlab["TableStyle"]
    mm = reportlab["mm"]

    table_rows = [
        [
            pdf_paragraph(label, styles["PdfTableHeader"], paragraph_class=Paragraph),
            pdf_paragraph(value, styles["BodyText"], paragraph_class=Paragraph),
        ]
        for label, value in rows
    ]

    table = Table(table_rows, colWidths=col_widths or [52 * mm, 118 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F8FD")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D9E6F2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E6F2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_long_table(headers, rows, styles, *, col_widths=None):
    reportlab = _load_reportlab()
    colors = reportlab["colors"]
    LongTable = reportlab["LongTable"]
    Paragraph = reportlab["Paragraph"]
    TableStyle = reportlab["TableStyle"]

    table_rows = [
        [pdf_paragraph(header, styles["PdfTableHeader"], paragraph_class=Paragraph) for header in headers]
    ]
    for row in rows:
        table_rows.append(
            [pdf_paragraph(value, styles["BodyText"], paragraph_class=Paragraph) for value in row]
        )

    table = LongTable(table_rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7F1FA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#153B66")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E6F2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_pdf_response(*, filename, title, subject="", story):
    reportlab = _load_reportlab()
    A4 = reportlab["A4"]
    SimpleDocTemplate = reportlab["SimpleDocTemplate"]
    mm = reportlab["mm"]

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="my.inventory",
        subject=subject or title,
    )
    document.build(story)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
