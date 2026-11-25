"""Ventanas de trabajo (auditoria funcional 2026-11-25, C2).

Quien ve que:
- admin y super_admin: todas las de su organizacion.
- colaborador: las de los proyectos donde es miembro.
- cliente: las de los proyectos de su empresa.
Lo que no se puede ver responde 404, igual que lo que no existe.

Quien hace que:
- pedir: admin, super_admin o colaborador miembro del proyecto. Con 72 h de
  anticipacion; una emergencia se salta el plazo, pero solo la pide un admin.
- aprobar o rechazar: solo el cliente del proyecto. Es su autorizacion por escrito.
- ejecutar, terminar, volver atras o cancelar: el equipo.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.work_window import WorkWindow
from app.modules.audit.services.audit_service import AuditService
from app.modules.work_windows.schemas import (
    WorkWindowCreate,
    WorkWindowDecision,
    WorkWindowRead,
    WorkWindowStatus,
    WorkWindowStatusChange,
)

router = APIRouter(prefix="/work-windows", tags=["work-windows"])

ANTICIPACION = timedelta(hours=72)
STAFF = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
ADMINS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)

# Estado actual -> estados a los que el equipo puede llevarla.
TRANSICIONES: dict[str, set[str]] = {
    WorkWindowStatus.REQUESTED: {WorkWindowStatus.CANCELLED},
    WorkWindowStatus.APPROVED: {WorkWindowStatus.IN_PROGRESS, WorkWindowStatus.CANCELLED},
    WorkWindowStatus.IN_PROGRESS: {WorkWindowStatus.COMPLETED, WorkWindowStatus.ROLLED_BACK},
}


def _client_id_of(db: Session, user: CurrentUser) -> int | None:
    return db.scalar(select(ClientProfile.client_id).where(ClientProfile.user_id == user.id))


def _puede_ver_proyecto(db: Session, user: CurrentUser, project: Project | None) -> bool:
    if not project or project.organization_id != user.organization_id:
        return False
    if user.role in ADMINS:
        return True
    if user.role == RoleCode.COLLABORATOR.value:
        return db.scalar(
            select(ProjectMember.id).where(
                ProjectMember.project_id == project.id, ProjectMember.user_id == user.id
            )
        ) is not None
    if user.role == RoleCode.CLIENT.value:
        client_id = _client_id_of(db, user)
        return client_id is not None and project.client_id == client_id
    return False


def _ventana_visible(db: Session, user: CurrentUser, window_id: int, *, bloquear: bool = False) -> WorkWindow:
    stmt = select(WorkWindow).where(WorkWindow.id == window_id)
    if bloquear:
        stmt = stmt.with_for_update()
    ventana = db.scalar(stmt)
    if not ventana or not _puede_ver_proyecto(db, user, db.get(Project, ventana.project_id)):
        raise HTTPException(status_code=404, detail="Work window not found")
    return ventana


def _auditar(db: Session, user: CurrentUser, accion: str, ventana: WorkWindow) -> None:
    AuditService(db).record(user.organization_id, accion, "work_windows", str(ventana.id), user.id)


@router.get("/", response_model=list[WorkWindowRead])
def list_work_windows(
    project_id: int | None = None,
    window_status: WorkWindowStatus | None = None,
    current_user: CurrentUser = Depends(require_roles(*STAFF, RoleCode.CLIENT.value)),
    db: Session = Depends(get_db),
) -> list[WorkWindowRead]:
    stmt = (
        select(WorkWindow)
        .join(Project, Project.id == WorkWindow.project_id)
        .where(WorkWindow.organization_id == current_user.organization_id)
    )
    if current_user.role == RoleCode.COLLABORATOR.value:
        stmt = stmt.join(ProjectMember, ProjectMember.project_id == Project.id).where(
            ProjectMember.user_id == current_user.id
        )
    elif current_user.role == RoleCode.CLIENT.value:
        client_id = _client_id_of(db, current_user)
        if client_id is None:
            return []
        stmt = stmt.where(Project.client_id == client_id)
    if project_id is not None:
        stmt = stmt.where(WorkWindow.project_id == project_id)
    if window_status is not None:
        stmt = stmt.where(WorkWindow.status == window_status.value)
    stmt = stmt.order_by(WorkWindow.starts_at.desc())
    return [WorkWindowRead.model_validate(v) for v in db.scalars(stmt).unique().all()]


@router.get("/{window_id}", response_model=WorkWindowRead)
def get_work_window(
    window_id: int,
    current_user: CurrentUser = Depends(require_roles(*STAFF, RoleCode.CLIENT.value)),
    db: Session = Depends(get_db),
) -> WorkWindowRead:
    return WorkWindowRead.model_validate(_ventana_visible(db, current_user, window_id))


@router.post("/", response_model=WorkWindowRead, status_code=status.HTTP_201_CREATED)
def request_work_window(
    payload: WorkWindowCreate,
    current_user: CurrentUser = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
) -> WorkWindowRead:
    project = db.get(Project, payload.project_id)
    if not _puede_ver_proyecto(db, current_user, project):
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")
    if payload.is_emergency:
        if current_user.role not in ADMINS:
            raise HTTPException(status_code=403, detail="Only an admin can request an emergency window")
    elif payload.starts_at < utcnow() + ANTICIPACION:
        raise HTTPException(
            status_code=422, detail="A work window must be requested at least 72 hours in advance"
        )
    ventana = WorkWindow(
        organization_id=current_user.organization_id,
        project_id=project.id,
        requested_by_user_id=current_user.id,
        title=payload.title,
        change_description=payload.change_description,
        systems_affected=payload.systems_affected,
        impact=payload.impact.value,
        rollback_plan=payload.rollback_plan,
        is_emergency=payload.is_emergency,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status=WorkWindowStatus.REQUESTED.value,
    )
    db.add(ventana)
    db.commit()
    db.refresh(ventana)
    _auditar(db, current_user, "work_window.requested", ventana)
    return WorkWindowRead.model_validate(ventana)


@router.post("/{window_id}/decision", response_model=WorkWindowRead)
def decide_work_window(
    window_id: int,
    payload: WorkWindowDecision,
    current_user: CurrentUser = Depends(require_roles(RoleCode.CLIENT.value)),
    db: Session = Depends(get_db),
) -> WorkWindowRead:
    ventana = _ventana_visible(db, current_user, window_id, bloquear=True)
    if ventana.status != WorkWindowStatus.REQUESTED:
        raise HTTPException(status_code=409, detail=f"Work window is already {ventana.status}")
    if not payload.approve and not (payload.comment and payload.comment.strip()):
        raise HTTPException(status_code=422, detail="A rejection needs a comment")
    ventana.status = (WorkWindowStatus.APPROVED if payload.approve else WorkWindowStatus.REJECTED).value
    ventana.client_decision_by_user_id = current_user.id
    ventana.client_decision_at = utcnow()
    ventana.client_comment = payload.comment
    db.commit()
    db.refresh(ventana)
    _auditar(db, current_user, f"work_window.{ventana.status}", ventana)
    return WorkWindowRead.model_validate(ventana)


@router.post("/{window_id}/status", response_model=WorkWindowRead)
def change_work_window_status(
    window_id: int,
    payload: WorkWindowStatusChange,
    current_user: CurrentUser = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
) -> WorkWindowRead:
    ventana = _ventana_visible(db, current_user, window_id, bloquear=True)
    if payload.status.value not in TRANSICIONES.get(ventana.status, set()):
        raise HTTPException(
            status_code=409, detail=f"Cannot go from {ventana.status} to {payload.status.value}"
        )
    if payload.status == WorkWindowStatus.ROLLED_BACK and not (payload.note and payload.note.strip()):
        raise HTTPException(status_code=422, detail="A rollback needs a note explaining what happened")
    ventana.status = payload.status.value
    if payload.note:
        ventana.execution_note = payload.note
    db.commit()
    db.refresh(ventana)
    _auditar(db, current_user, f"work_window.{ventana.status}", ventana)
    return WorkWindowRead.model_validate(ventana)
