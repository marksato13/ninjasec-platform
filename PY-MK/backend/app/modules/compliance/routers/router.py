from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.modules.compliance.schemas import ControlStatusRead, ControlStatusUpdate, SoaSummary
from app.modules.compliance.services.soa_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])

_READ_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
_WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.get("/controls", response_model=list[ControlStatusRead])
def list_controls(
    client_id: int,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[ControlStatusRead]:
    return ComplianceService(db, current_user).list_controls(client_id)


@router.get("/soa", response_model=SoaSummary)
def get_soa(
    client_id: int,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> SoaSummary:
    return ComplianceService(db, current_user).soa_summary(client_id)


@router.put("/controls/{control_id}", response_model=ControlStatusRead)
def update_control_status(
    control_id: int,
    client_id: int,
    payload: ControlStatusUpdate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ControlStatusRead:
    return ComplianceService(db, current_user).update_status(client_id, control_id, payload)
