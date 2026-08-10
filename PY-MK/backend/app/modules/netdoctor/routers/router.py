from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.db.models.netdoctor import NetdoctorIssue
from app.modules.netdoctor.guided_tree import GUIDED_TREE
from app.modules.netdoctor.schemas import NetdoctorIssueRead

router = APIRouter(prefix="/netdoctor", tags=["netdoctor"])
ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)


@router.get("/guided-tree")
def get_guided_tree(_: CurrentUser = Depends(require_roles(*ROLES))) -> dict:
    return GUIDED_TREE


@router.get("/issues", response_model=list[NetdoctorIssueRead])
def list_issues(
    category: str | None = None,
    vendor: str | None = None,
    user: CurrentUser = Depends(require_roles(*ROLES)),
    db: Session = Depends(get_db),
):
    stmt = select(NetdoctorIssue).order_by(NetdoctorIssue.code)
    if category:
        stmt = stmt.where(NetdoctorIssue.category == category)
    issues = list(db.scalars(stmt))
    if vendor:
        issues = [i for i in issues if vendor in i.diagnostic_commands]
    return issues


@router.get("/issues/{code}", response_model=NetdoctorIssueRead)
def get_issue(code: str, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    issue = db.scalar(select(NetdoctorIssue).where(NetdoctorIssue.code == code.upper()))
    if not issue:
        raise HTTPException(404, "Problema no encontrado en el catálogo")
    return issue
