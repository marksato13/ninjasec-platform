"""31-P1: gap analysis en PDF, reutilizando el motor ReportLab existente
(mismo patrón que app/modules/devices/services/topology_pdf.py)."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_MARGIN = 16 * mm
_RESULT_COLOR = {
    "pass": colors.HexColor("#10b981"),
    "fail": colors.HexColor("#dc2626"),
    "manual": colors.HexColor("#94a3b8"),
    "not_applicable": colors.HexColor("#cbd5e1"),
}
_RESULT_LABEL = {"pass": "Cumple", "fail": "No cumple", "manual": "Manual", "not_applicable": "No aplica"}


def generate_hardening_pdf(client_name: str, evaluations: list[dict], summary: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=_MARGIN, rightMargin=_MARGIN, topMargin=_MARGIN, bottomMargin=_MARGIN, title=f"Gap Analysis — {client_name}", author="NinjaSec Platform")

    base = getSampleStyleSheet()
    title_style = ParagraphStyle("hard_title", parent=base["Normal"], fontSize=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))
    subtitle_style = ParagraphStyle("hard_subtitle", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"))
    section_style = ParagraphStyle("hard_section", parent=base["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"), spaceBefore=12, spaceAfter=6)
    evidence_style = ParagraphStyle("hard_evidence", parent=base["Normal"], fontSize=7.5, textColor=colors.HexColor("#475569"))

    story: list = [
        Paragraph(f"Gap Analysis de Hardening — {client_name}", title_style),
        Paragraph(f"{summary['passed']}/{summary['passed'] + summary['failed']} reglas verificables cumplidas ({summary['compliance_percent']}%) · {summary['manual']} requieren verificación manual · {summary['not_applicable']} no aplican", subtitle_style),
        Spacer(1, 12),
        Paragraph("Resultado por regla", section_style),
    ]

    rows = [["Código", "Regla", "Categoría", "Resultado", "Evidencia"]]
    for evaluation in evaluations:
        rule = evaluation["rule"]
        rows.append([
            rule.code,
            Paragraph(rule.title, evidence_style),
            rule.category,
            _RESULT_LABEL.get(evaluation["result"], evaluation["result"]),
            Paragraph(evaluation["evidence"], evidence_style),
        ])
    table = Table(rows, repeatRows=1, colWidths=[45, 130, 80, 60, 175], hAlign="LEFT")
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row_index, evaluation in enumerate(evaluations, start=1):
        color = _RESULT_COLOR.get(evaluation["result"], colors.black)
        style_commands.append(("TEXTCOLOR", (3, row_index), (3, row_index), color))
        style_commands.append(("FONTNAME", (3, row_index), (3, row_index), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_commands))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
