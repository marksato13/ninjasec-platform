import io

from app.core.time_utils import utcnow

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.modules.audit.services.audit_service import AuditService
from app.modules.health_score.schemas import HealthScoreRead
from app.modules.health_score.services.health_score_service import HealthScoreService

router = APIRouter(prefix="/health-score", tags=["health-score"])
ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)


@router.get("", response_model=HealthScoreRead)
def get_health_score(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return HealthScoreService(db, user).compute(client_id)


@router.get("/export/pdf")
def export_health_score_pdf(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)) -> StreamingResponse:
    from app.modules.health_score.services.soc_report_pdf import generate_soc_report_pdf

    score_data = HealthScoreService(db, user).compute(client_id)
    pdf_bytes = generate_soc_report_pdf(score_data)

    AuditService(db).record(user.organization_id, "health_score.exported_pdf", "clients", str(client_id), user.id)
    filename = f"salud_seguridad_{client_id}_{utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
