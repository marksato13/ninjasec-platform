import io

from app.core.time_utils import utcnow

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.client import Client
from app.db.models.enums import RoleCode
from app.db.models.hardening import HardeningRule
from app.modules.audit.services.audit_service import AuditService
from app.modules.hardening.schemas import GapSummary, HardeningRuleRead, RuleEvaluationRead
from app.modules.hardening.services.evaluation_service import HardeningEvaluationService

router = APIRouter(prefix="/hardening", tags=["hardening"])
ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)


@router.get("/rules", response_model=list[HardeningRuleRead])
def list_rules(user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return list(db.scalars(select(HardeningRule).order_by(HardeningRule.code)))


@router.get("/evaluate", response_model=list[RuleEvaluationRead])
def evaluate_client(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return HardeningEvaluationService(db, user).evaluate(client_id)


@router.get("/summary", response_model=GapSummary)
def summary(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    service = HardeningEvaluationService(db, user)
    return service.summarize(service.evaluate(client_id))


@router.get("/export/pdf")
def export_pdf(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)) -> StreamingResponse:
    from app.modules.hardening.services.hardening_pdf import generate_hardening_pdf

    service = HardeningEvaluationService(db, user)
    client = service.get_client(client_id)
    evaluations = service.evaluate(client_id)
    summary_data = service.summarize(evaluations)
    pdf_bytes = generate_hardening_pdf(client.company_name, evaluations, summary_data)

    AuditService(db).record(user.organization_id, "hardening.exported_pdf", "clients", str(client_id), user.id)
    filename = f"gap_analysis_{client_id}_{utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
