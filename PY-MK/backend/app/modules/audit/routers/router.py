import io
from typing import Literal

import openpyxl
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.audit_log import AuditLog
from app.db.models.enums import RoleCode
from app.db.models.user import User
from app.modules.audit.schemas import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit"])

EXPORT_LIMIT = 5_000
EXPORT_COLUMNS = ("Fecha", "Usuario", "Acción", "Entidad afectada")


def _filtered_query(
    organization_id: int,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    stmt = (
        select(AuditLog, User.full_name)
        .outerjoin(User, AuditLog.user_id == User.id)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    return stmt


def _export_rows(db: Session, organization_id: int, **filters) -> list[tuple[str, str, str, str]]:
    records = db.execute(
        _filtered_query(organization_id, **filters).limit(EXPORT_LIMIT)
    ).all()
    rows = []
    for log, full_name in records:
        created_at = log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
        user = full_name or (f"Usuario #{log.user_id}" if log.user_id else "Sistema")
        entity = log.entity_type
        if log.entity_id:
            entity = f"{entity} #{log.entity_id}"
        rows.append((created_at, user, log.action, entity))
    return rows


def _build_xlsx(rows: list[tuple[str, str, str, str]]) -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Auditoría"
    widths = (22, 28, 30, 35)
    header_fill = PatternFill("solid", fgColor="1E293B")
    header_font = Font(bold=True, color="F8FAFC")
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for column, (title, width) in enumerate(zip(EXPORT_COLUMNS, widths), 1):
        cell = sheet.cell(1, column, title)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal="center")
        sheet.column_dimensions[get_column_letter(column)].width = width

    for row_number, values in enumerate(rows, 2):
        for column, value in enumerate(values, 1):
            cell = sheet.cell(row_number, column, value)
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = "A1:D1"
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _build_pdf(rows: list[tuple[str, str, str, str]]) -> io.BytesIO:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Registro de auditoría",
    )
    styles = getSampleStyleSheet()
    body_style = styles["BodyText"]
    body_style.fontSize = 8
    body_style.leading = 10
    table_data = [list(EXPORT_COLUMNS)] + [
        [Paragraph(str(value), body_style) for value in row] for row in rows
    ]
    table = Table(table_data, colWidths=(38 * mm, 55 * mm, 70 * mm, 90 * mm), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story = [Paragraph("Registro de auditoría", styles["Title"]), Spacer(1, 5 * mm), table]
    document.build(story)
    buffer.seek(0)
    return buffer


@router.get("/export")
def export_audit_logs(
    format: Literal["pdf", "xlsx"] = Query(...),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    rows = _export_rows(
        db, current_user.organization_id,
        action=action, entity_type=entity_type, entity_id=entity_id,
    )
    timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
    if format == "pdf":
        buffer = _build_pdf(rows)
        media_type = "application/pdf"
    else:
        buffer = _build_xlsx(rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="auditoria_{timestamp}.{format}"',
            "X-Export-Limit": str(EXPORT_LIMIT),
        },
    )


@router.get("/", response_model=list[AuditLogRead])
def list_audit_logs(
    limit: int | None = Query(default=None, ge=1, le=EXPORT_LIMIT),
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    stmt = _filtered_query(current_user.organization_id)
    if limit:
        stmt = stmt.limit(limit)
    return [AuditLogRead.model_validate(log) for log, _ in db.execute(stmt).all()]
