from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.modules.risk_scoring.schemas import HostScoreRead
from app.modules.risk_scoring.services.scoring_service import RiskScoringService

router = APIRouter(prefix="/risk-scoring", tags=["risk-scoring"])
ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)


@router.get("/hosts", response_model=list[HostScoreRead])
def list_host_scores(client_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskScoringService(db, user).score_client_hosts(client_id)
