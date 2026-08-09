import io

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.client import Client
from app.db.models.enums import RoleCode
from app.db.models.user import User
from app.modules.audits.schemas import AuditCreate, AuditRead, AuditUpdate
from app.modules.audits.services.audit_pdf import generate_audit_plan_pdf
from app.modules.audits.services.audit_service import AuditManagementService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/audits", tags=["audits"])

_READ_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
_WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.get("/", response_model=list[AuditRead])
def list_audits(
    client_id: int | None = None,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[AuditRead]:
    return AuditManagementService(db, current_user).list(client_id)


@router.post("/", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
def create_audit(
    payload: AuditCreate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> AuditRead:
    return AuditManagementService(db, current_user).create(payload)


@router.put("/{audit_id}", response_model=AuditRead)
def update_audit(
    audit_id: int,
    payload: AuditUpdate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> AuditRead:
    return AuditManagementService(db, current_user).update(audit_id, payload)


@router.get("/{audit_id}/plan-pdf")
def export_audit_plan_pdf(
    audit_id: int,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    service = AuditManagementService(db, current_user)
    audit = service.get(audit_id)
    client = db.get(Client, audit.client_id)
    auditor = db.get(User, audit.lead_auditor_id)

    pdf_bytes = generate_audit_plan_pdf(audit, client, auditor)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="plan_{audit.code}.pdf"'},
    )
