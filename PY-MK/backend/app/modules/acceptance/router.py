"""Pruebas de aceptación (UAT) de un proyecto (35-P-05).

    GET    /acceptance-cases/projects/{id}   casos y resumen          (equipo del proyecto o su cliente)
    POST   /acceptance-cases/projects/{id}   escribir un caso         (admin o colaborador del proyecto)
    PUT    /acceptance-cases/{id}            corregir un caso         (admin o colaborador del proyecto)
    DELETE /acceptance-cases/{id}            quitar uno no aprobado   (admin)
    POST   /acceptance-cases/{id}/decision   aprobar u observar       (solo el cliente del proyecto)

## Quién hace qué

- **Admin / super admin:** todo, en los proyectos de su organización.
- **Colaborador:** escribe y corrige casos de los proyectos donde es miembro.
  No decide por el cliente y no borra.
- **Cliente:** ve los casos de SU proyecto y los marca. Observar exige nota
  (≥5 caracteres), como en C1. Un caso aprobado ya no cambia: es la evidencia
  del acta de conformidad.

Lo ajeno (otro proyecto, otro cliente, otra organización) devuelve **404**.

## Reglas

- Si el equipo cambia lo que se comprueba (título, pasos o resultado esperado)
  en un caso ya decidido, vuelve a `pendiente`: el cliente tiene que verlo de
  nuevo. Un caso aprobado no se corrige ni se borra (409); se añade otro.
- `ready_for_signoff`: hay casos y todos están aprobados. Es la señal para
  generar el acta de conformidad (35-P-06).
- Los textos no admiten nada con forma de clave (422).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.acceptance_case import AcceptanceCase
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.modules.audit.services.audit_service import AuditService
from app.modules.client_systems.router import _sin_secretos

router = APIRouter(prefix="/acceptance-cases", tags=["acceptance-cases"])

_ADMINS = {RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value}
_COLAB = RoleCode.COLLABORATOR.value
_CLIENTE = RoleCode.CLIENT.value
_CAMPOS_DE_PRUEBA = ("title", "steps", "expected")


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class CasoIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    steps: str = Field(min_length=3, max_length=4000)
    expected: str = Field(min_length=3, max_length=2000)
    position: int | None = Field(default=None, ge=0, le=10000)

    @field_validator("title", "steps", "expected")
    @classmethod
    def _limpio(cls, v: str) -> str:
        return _sin_secretos(v) or ""


class CasoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    steps: str | None = Field(default=None, min_length=3, max_length=4000)
    expected: str | None = Field(default=None, min_length=3, max_length=2000)
    position: int | None = Field(default=None, ge=0, le=10000)

    @field_validator("title", "steps", "expected")
    @classmethod
    def _limpio(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


class DecisionIn(BaseModel):
    decision: Literal["aprobado", "observado"]
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def _limpio(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


class CasoClienteOut(BaseModel):
    """Lo que ve el cliente: qué comprobar y su propia decisión. Nada de quién del equipo lo escribió."""

    id: int
    project_id: int
    position: int
    title: str
    steps: str
    expected: str
    status: str
    client_note: str | None
    decided_at: datetime | None


class CasoEquipoOut(CasoClienteOut):
    decided_by: int | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class ResumenOut(BaseModel):
    total: int
    pendiente: int
    aprobado: int
    observado: int
    ready_for_signoff: bool


class VistaClienteOut(BaseModel):
    project_id: int
    can_manage: bool
    can_decide: bool
    summary: ResumenOut
    cases: list[CasoClienteOut]


class VistaEquipoOut(VistaClienteOut):
    cases: list[CasoEquipoOut]


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------

_NADA_PROYECTO = HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
_NADA_CASO = HTTPException(status.HTTP_404_NOT_FOUND, "Acceptance case not found")


def _es_miembro(db: Session, user_id: int, project_id: int) -> bool:
    return db.scalar(
        select(ProjectMember.id).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    ) is not None


def _proyecto(db: Session, user: CurrentUser, project_id: int) -> Project:
    """El proyecto, si este usuario lo puede ver. Si no, 404 (no se confirma que exista)."""
    p = db.get(Project, project_id)
    if p is None or p.organization_id != user.organization_id:
        raise _NADA_PROYECTO
    if user.role in _ADMINS:
        return p
    if user.role == _COLAB:
        if not _es_miembro(db, user.id, p.id):
            raise _NADA_PROYECTO
        return p
    if user.role == _CLIENTE:
        perfil = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if perfil is None or p.client_id != perfil.client_id:
            raise _NADA_PROYECTO
        return p
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")


def _caso(db: Session, user: CurrentUser, case_id: int) -> tuple[AcceptanceCase, Project]:
    c = db.get(AcceptanceCase, case_id)
    if c is None or c.organization_id != user.organization_id:
        raise _NADA_CASO
    try:
        p = _proyecto(db, user, c.project_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise _NADA_CASO from None
        raise
    return c, p


def _equipo(user: CurrentUser) -> bool:
    return user.role in _ADMINS or user.role == _COLAB


# --------------------------------------------------------------------------
# Vista
# --------------------------------------------------------------------------


def _vista(db: Session, user: CurrentUser, p: Project) -> VistaClienteOut | VistaEquipoOut:
    casos = db.scalars(
        select(AcceptanceCase).where(AcceptanceCase.project_id == p.id)
        .order_by(AcceptanceCase.position, AcceptanceCase.id)
    ).all()
    cuenta = {"pendiente": 0, "aprobado": 0, "observado": 0}
    for c in casos:
        cuenta[c.status] = cuenta.get(c.status, 0) + 1
    resumen = ResumenOut(total=len(casos), **cuenta,
                         ready_for_signoff=bool(casos) and cuenta["aprobado"] == len(casos))
    comun = {"project_id": p.id, "summary": resumen}
    if _equipo(user):
        return VistaEquipoOut(**comun, can_manage=True, can_decide=False,
                              cases=[CasoEquipoOut.model_validate(c, from_attributes=True) for c in casos])
    return VistaClienteOut(**comun, can_manage=False, can_decide=True,
                           cases=[CasoClienteOut.model_validate(c, from_attributes=True) for c in casos])


def _auditar(db: Session, user: CurrentUser, c: AcceptanceCase, accion: str, extra: dict | None = None) -> None:
    datos = {"project_id": c.project_id, "status": c.status, "title": c.title}
    datos.update(extra or {})
    AuditService(db).record(
        organization_id=c.organization_id, action=accion, entity_type="acceptance_case",
        entity_id=str(c.id), user_id=user.id, metadata_json=json.dumps(datos, ensure_ascii=False),
    )


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------


@router.get("/projects/{project_id}", response_model=VistaEquipoOut | VistaClienteOut)
def ver_casos(project_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _vista(db, user, _proyecto(db, user, project_id))


@router.post("/projects/{project_id}", response_model=VistaEquipoOut, status_code=status.HTTP_201_CREATED)
def crear_caso(project_id: int, payload: CasoIn, user: CurrentUser = Depends(get_current_user),
               db: Session = Depends(get_db)):
    p = _proyecto(db, user, project_id)
    if not _equipo(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    posicion = payload.position
    if posicion is None:
        ultima = db.scalar(select(func.max(AcceptanceCase.position)).where(AcceptanceCase.project_id == p.id))
        posicion = (ultima or 0) + 1
    c = AcceptanceCase(
        organization_id=p.organization_id, project_id=p.id, position=posicion,
        title=payload.title, steps=payload.steps, expected=payload.expected,
        status="pendiente", created_by=user.id,
    )
    db.add(c)
    db.flush()
    _auditar(db, user, c, "acceptance_case.created")
    db.commit()
    return _vista(db, user, p)


@router.put("/{case_id}", response_model=VistaEquipoOut)
def editar_caso(case_id: int, payload: CasoUpdate, user: CurrentUser = Depends(get_current_user),
                db: Session = Depends(get_db)):
    c, p = _caso(db, user, case_id)
    if not _equipo(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    cambios = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    cambia_la_prueba = any(k in _CAMPOS_DE_PRUEBA and getattr(c, k) != v for k, v in cambios.items())
    if c.status == "aprobado" and cambia_la_prueba:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Un caso aprobado es evidencia del acta: no se cambia. Añade un caso nuevo.")
    anterior = c.status
    for k, v in cambios.items():
        setattr(c, k, v)
    if cambia_la_prueba and c.status == "observado":
        # Lo que el cliente observó ya no es lo mismo: tiene que volver a comprobarlo.
        c.status = "pendiente"
        c.decided_at = None
        c.decided_by = None
    db.flush()
    _auditar(db, user, c, "acceptance_case.updated",
             {"from": anterior, "fields": sorted(cambios)} if anterior != c.status else {"fields": sorted(cambios)})
    db.commit()
    return _vista(db, user, p)


@router.delete("/{case_id}", response_model=VistaEquipoOut)
def quitar_caso(case_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Devuelve la vista (no 204): el cliente HTTP del panel siempre espera JSON."""
    c, p = _caso(db, user, case_id)
    if user.role not in _ADMINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    if c.status == "aprobado":
        raise HTTPException(status.HTTP_409_CONFLICT, "Un caso aprobado no se puede quitar.")
    _auditar(db, user, c, "acceptance_case.deleted")
    db.delete(c)
    db.commit()
    return _vista(db, user, p)


@router.post("/{case_id}/decision", response_model=VistaClienteOut)
def decidir_caso(case_id: int, payload: DecisionIn, user: CurrentUser = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    c, p = _caso(db, user, case_id)
    if user.role != _CLIENTE:
        # El equipo no decide por el cliente.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el cliente aprueba u observa un caso.")
    if c.status == "aprobado":
        raise HTTPException(status.HTTP_409_CONFLICT, "Este caso ya está aprobado.")
    nota = (payload.note or "").strip() or None
    if payload.decision == "observado" and (nota is None or len(nota) < 5):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Cuenta qué no funcionó (al menos 5 caracteres).")
    anterior = c.status
    c.status = payload.decision
    c.client_note = nota
    c.decided_at = utcnow()
    c.decided_by = user.id
    db.flush()
    _auditar(db, user, c, f"acceptance_case.{payload.decision}", {"from": anterior})
    db.commit()
    return _vista(db, user, p)
