import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.db.models.audit import Audit
from app.db.models.client import Client
from app.db.models.user import User

_DARK = colors.HexColor("#1E293B")
_MUTED = colors.HexColor("#64748B")
_BORDER = colors.HexColor("#CBD5E1")
_ALT = colors.HexColor("#F1F5F9")

_FRAMEWORK_LABEL = {
    "cobit_2019": "COBIT 2019",
    "iso_27001": "ISO/IEC 27001",
    "iso_19011": "ISO 19011",
    "custom": "Marco propio",
}
_AUDIT_TYPE_LABEL = {
    "internal": "Interna",
    "external": "Externa",
    "certification": "Certificación",
    "follow_up": "Seguimiento",
}
_STATUS_LABEL = {
    "planned": "Planificada",
    "in_progress": "En curso",
    "reporting": "En informe",
    "closed": "Cerrada",
}


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "aud_title", parent=base["Normal"], fontSize=18,
            textColor=_DARK, fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "aud_subtitle", parent=base["Normal"], fontSize=10,
            textColor=_MUTED, fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "aud_section", parent=base["Normal"], fontSize=12,
            textColor=_DARK, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "aud_body", parent=base["Normal"], fontSize=9.5,
            textColor=_DARK, fontName="Helvetica", leading=14,
        ),
    }


def generate_audit_plan_pdf(audit: Audit, client: Client, auditor: User) -> bytes:
    """26-P1: PDF del plan de auditoría -- objetivo, alcance, criterios,
    equipo, cronograma y recursos. Reutiliza el mismo motor ReportLab que
    el resto de exports de la plataforma (reports/services/pdf_service.py),
    con estilos propios para no acoplarse a los internos de ese módulo."""
    st = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    story.append(Paragraph("Plan de Auditoría", st["title"]))
    story.append(Paragraph(f"{audit.code} · {client.company_name}", st["subtitle"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=_BORDER, thickness=1))

    story.append(Paragraph(audit.title, st["section"]))
    meta = Table(
        [
            ["Marco", _FRAMEWORK_LABEL.get(audit.framework, audit.framework)],
            ["Tipo", _AUDIT_TYPE_LABEL.get(audit.audit_type, audit.audit_type)],
            ["Estado", _STATUS_LABEL.get(audit.status, audit.status)],
            ["Auditor líder", auditor.full_name],
            ["Inicio planificado", str(audit.planned_start or "—")],
            ["Fin planificado", str(audit.planned_end or "—")],
        ],
        colWidths=[45 * mm, 120 * mm],
    )
    meta.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), _MUTED),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, _ALT]),
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta)

    story.append(Paragraph("Objetivo", st["section"]))
    story.append(Paragraph(audit.objective or "No especificado.", st["body"]))

    story.append(Paragraph("Alcance", st["section"]))
    story.append(Paragraph(audit.scope or "No especificado.", st["body"]))

    story.append(Paragraph("Criterios de auditoría", st["section"]))
    story.append(Paragraph(
        f"El encargo se evalúa contra el marco {_FRAMEWORK_LABEL.get(audit.framework, audit.framework)}, "
        "siguiendo las directrices de ISO 19011:2018 para la conducción de la auditoría.",
        st["body"],
    ))

    story.append(Paragraph("Equipo", st["section"]))
    story.append(Paragraph(f"Auditor líder: {auditor.full_name} ({auditor.email})", st["body"]))

    story.append(Paragraph("Cronograma", st["section"]))
    story.append(Paragraph(
        f"Inicio planificado: {audit.planned_start or '—'} · "
        f"Fin planificado: {audit.planned_end or '—'}"
        + (f" · Fin real: {audit.actual_end}" if audit.actual_end else ""),
        st["body"],
    ))

    story.append(Paragraph("Recursos", st["section"]))
    story.append(Paragraph(
        "Acceso a la documentación del SGSI del cliente, entrevistas con el personal "
        "responsable de los procesos en alcance y el registro de auditoría técnica "
        "(módulo de audit log) como evidencia de respaldo.",
        st["body"],
    ))

    doc.build(story)
    return buffer.getvalue()
