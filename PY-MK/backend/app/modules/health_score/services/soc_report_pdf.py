"""30-P3: informe ejecutivo "SOC as a report" -- panel de salud en PDF,
reutilizando el motor ReportLab existente (mismo patrón que
topology_pdf.py / hardening_pdf.py)."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_MARGIN = 20 * mm
_LABEL_COLOR = {"Saludable": colors.HexColor("#10b981"), "Con observaciones": colors.HexColor("#f59e0b"), "Requiere atención": colors.HexColor("#dc2626")}


def generate_soc_report_pdf(score_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=_MARGIN, rightMargin=_MARGIN, topMargin=_MARGIN, bottomMargin=_MARGIN, title=f"Salud de seguridad — {score_data['client_name']}", author="Ninja Tech")

    base = getSampleStyleSheet()
    title_style = ParagraphStyle("soc_title", parent=base["Normal"], fontSize=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))
    subtitle_style = ParagraphStyle("soc_subtitle", parent=base["Normal"], fontSize=10, textColor=colors.HexColor("#64748b"))
    score_style = ParagraphStyle("soc_score", parent=base["Normal"], fontSize=48, fontName="Helvetica-Bold", textColor=_LABEL_COLOR.get(score_data["label"], colors.black))
    label_style = ParagraphStyle("soc_label", parent=base["Normal"], fontSize=14, fontName="Helvetica-Bold", textColor=_LABEL_COLOR.get(score_data["label"], colors.black))
    narrative_style = ParagraphStyle("soc_narrative", parent=base["Normal"], fontSize=11, textColor=colors.HexColor("#334155"), leading=16)
    section_style = ParagraphStyle("soc_section", parent=base["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"), spaceBefore=16, spaceAfter=6)

    story: list = [
        Paragraph(f"Informe ejecutivo de salud de seguridad — {score_data['client_name']}", title_style),
        Paragraph("Resumen no técnico para gerencia. El detalle técnico completo está disponible en los módulos de la plataforma.", subtitle_style),
        Spacer(1, 18),
        Paragraph(str(score_data["score"]), score_style),
        Paragraph(score_data["label"], label_style),
        Spacer(1, 10),
        Paragraph(score_data["narrative"], narrative_style),
        Paragraph("¿Cómo se calcula?", section_style),
        Paragraph(
            "El índice parte de 100 y resta puntos por cada señal de riesgo real detectada en la plataforma: "
            "hallazgos de revisiones de seguridad sin resolver, reglas técnicas de hardening incumplidas, "
            "hosts identificados como de alto riesgo por reputación externa, y vulnerabilidades conocidas con "
            "alta probabilidad real de explotación. Cada categoría tiene un tope máximo de deducción.",
            narrative_style,
        ),
    ]

    rows = [["Categoría", "Cantidad", "Puntos restados"]]
    for item in score_data["breakdown"]:
        rows.append([item["category"], str(item["count"]), f"-{item['deduction']}"])
    table = Table(rows, colWidths=[280, 80, 100], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
