"""Formación: planes de estudio, inscripción y progreso por módulo.

    GET   /study/plans                       planes activos de la organización
    GET   /study/plans/{id}                  un plan con sus módulos
    POST  /study/plans/{id}/enroll           inscribirse (uno mismo)
    GET   /study/me                          mis inscripciones con porcentaje
    GET   /study/me/{enrollment_id}          el detalle de una inscripción mía
    PATCH /study/me/{enrollment_id}/modules/{module_id}   marcar mi avance
    GET   /study/team                        admin: el avance de todos
    GET   /study/team/{enrollment_id}        admin: el detalle de una persona, para validar
    POST  /study/progress/{progress_id}/validate          admin: validar un módulo

## Reglas

- **Cada persona ve y toca solo lo suyo.** Pedir la inscripción de otra persona
  devuelve 404, no 403: no se confirma que exista. Lo mismo con otra organización.
- **El estado lo marca quien estudia**; `validated` solo lo pone un admin. Sin tutor
  un módulo se queda en `completed` y eso ya cuenta como avance.
- **El porcentaje se pondera por horas**, no por número de módulos: un módulo de 20 h
  pesa más que uno de 2. Si un módulo no tiene horas, cuenta como 1.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user, require_roles
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.enums import RoleCode
from app.db.models.study_plan import (
    StudyEnrollment,
    StudyModule,
    StudyPlan,
    StudyProgress,
)
from app.db.models.user import User
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/study", tags=["study"])

_STAFF = require_roles(
    RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value
)
_ADMIN = require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)

Estado = Literal["pending", "in_progress", "completed"]
HECHOS = {"completed", "validated"}


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class ModuloOut(BaseModel):
    id: int
    position: int
    title: str
    objective: str | None
    topics: str | None
    lab: str | None
    estimated_hours: int | None
    weight_percent: int | None


class PlanOut(BaseModel):
    id: int
    name: str
    slug: str
    area: str
    description: str | None
    target_certification: str | None
    vendor: str | None
    exam_code: str | None
    estimated_hours: int | None
    modules_count: int


class PlanDetalle(PlanOut):
    modules: list[ModuloOut]


class EnrollIn(BaseModel):
    target_date: date | None = None
    weekly_hours: int | None = Field(default=None, ge=1, le=80)


class AvanceIn(BaseModel):
    status: Estado
    hours_spent: int | None = Field(default=None, ge=0, le=1000)
    evidence_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class AvanceModulo(ModuloOut):
    status: str
    hours_spent: int | None
    evidence_url: str | None
    notes: str | None
    progress_id: int | None
    validated: bool


class InscripcionOut(BaseModel):
    id: int
    plan_id: int
    plan_name: str
    exam_code: str | None
    target_date: date | None
    weekly_hours: int | None
    percent: int
    modules_done: int
    modules_total: int
    hours_done: int
    hours_total: int


class InscripcionDetalle(InscripcionOut):
    modules: list[AvanceModulo]


class EquipoFila(BaseModel):
    enrollment_id: int
    user_id: int
    user_name: str
    plan_name: str
    percent: int
    modules_done: int
    modules_total: int
    pending_validation: int


# --------------------------------------------------------------------------
# Lógica
# --------------------------------------------------------------------------


def _modulos(db: Session, plan_id: int) -> list[StudyModule]:
    return list(db.scalars(
        select(StudyModule).where(StudyModule.plan_id == plan_id).order_by(StudyModule.position)
    ).all())


def _peso(m: StudyModule) -> int:
    return m.estimated_hours or 1


def _resumen(db: Session, insc: StudyEnrollment, plan: StudyPlan):
    """(percent, hechos, total, horas_hechas, horas_total, modulos, avance_por_modulo)."""
    modulos = _modulos(db, plan.id)
    avance = {
        p.module_id: p
        for p in db.scalars(
            select(StudyProgress).where(StudyProgress.enrollment_id == insc.id)
        ).all()
    }
    total_peso = sum(_peso(m) for m in modulos) or 1
    hecho_peso = sum(_peso(m) for m in modulos if avance.get(m.id) and avance[m.id].status in HECHOS)
    hechos = sum(1 for m in modulos if avance.get(m.id) and avance[m.id].status in HECHOS)
    horas_total = sum(m.estimated_hours or 0 for m in modulos)
    horas_hechas = sum(m.estimated_hours or 0 for m in modulos
                       if avance.get(m.id) and avance[m.id].status in HECHOS)
    return round(100 * hecho_peso / total_peso), hechos, len(modulos), horas_hechas, horas_total, modulos, avance


def _inscripcion_propia(db: Session, user: CurrentUser, enrollment_id: int) -> StudyEnrollment:
    insc = db.scalar(select(StudyEnrollment).where(
        StudyEnrollment.id == enrollment_id,
        StudyEnrollment.user_id == user.id,
        StudyEnrollment.organization_id == user.organization_id,
    ))
    if insc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inscripción no encontrada")
    return insc


def _out(db, insc, plan) -> InscripcionOut:
    p, h, t, hh, ht, _, _ = _resumen(db, insc, plan)
    return InscripcionOut(
        id=insc.id, plan_id=plan.id, plan_name=plan.name, exam_code=plan.exam_code,
        target_date=insc.target_date, weekly_hours=insc.weekly_hours,
        percent=p, modules_done=h, modules_total=t, hours_done=hh, hours_total=ht,
    )


def _plan_de_org(db: Session, user: CurrentUser, plan_id: int) -> StudyPlan:
    plan = db.scalar(select(StudyPlan).where(
        StudyPlan.id == plan_id,
        StudyPlan.organization_id == user.organization_id,
        StudyPlan.is_active == True,  # noqa: E712
    ))
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    return plan


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.get("/plans", response_model=list[PlanOut])
def listar_planes(user: CurrentUser = Depends(_STAFF), db: Session = Depends(get_db)):
    planes = db.scalars(select(StudyPlan).where(
        StudyPlan.organization_id == user.organization_id,
        StudyPlan.is_active == True,  # noqa: E712
    ).order_by(StudyPlan.name)).all()
    return [PlanOut(
        id=p.id, name=p.name, slug=p.slug, area=p.area, description=p.description,
        target_certification=p.target_certification, vendor=p.vendor, exam_code=p.exam_code,
        estimated_hours=p.estimated_hours, modules_count=len(_modulos(db, p.id)),
    ) for p in planes]


@router.get("/plans/{plan_id}", response_model=PlanDetalle)
def ver_plan(plan_id: int, user: CurrentUser = Depends(_STAFF), db: Session = Depends(get_db)):
    p = _plan_de_org(db, user, plan_id)
    mods = _modulos(db, p.id)
    return PlanDetalle(
        id=p.id, name=p.name, slug=p.slug, area=p.area, description=p.description,
        target_certification=p.target_certification, vendor=p.vendor, exam_code=p.exam_code,
        estimated_hours=p.estimated_hours, modules_count=len(mods),
        modules=[ModuloOut(
            id=m.id, position=m.position, title=m.title, objective=m.objective, topics=m.topics,
            lab=m.lab, estimated_hours=m.estimated_hours, weight_percent=m.weight_percent,
        ) for m in mods],
    )


@router.post("/plans/{plan_id}/enroll", response_model=InscripcionOut,
             status_code=status.HTTP_201_CREATED)
def inscribirse(plan_id: int, payload: EnrollIn, user: CurrentUser = Depends(_STAFF),
                db: Session = Depends(get_db)):
    plan = _plan_de_org(db, user, plan_id)
    ya = db.scalar(select(StudyEnrollment).where(
        StudyEnrollment.user_id == user.id, StudyEnrollment.plan_id == plan.id))
    if ya is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya estás inscrito en este plan")
    insc = StudyEnrollment(
        organization_id=user.organization_id, user_id=user.id, plan_id=plan.id,
        started_at=date.today(), target_date=payload.target_date, weekly_hours=payload.weekly_hours,
    )
    db.add(insc)
    db.flush()
    AuditService(db).record(
        organization_id=user.organization_id, action="create", entity_type="study_enrollment",
        entity_id=str(insc.id), user_id=user.id,
    )
    db.commit()
    return _out(db, insc, plan)


@router.get("/me", response_model=list[InscripcionOut])
def mis_inscripciones(user: CurrentUser = Depends(_STAFF), db: Session = Depends(get_db)):
    filas = db.scalars(select(StudyEnrollment).where(
        StudyEnrollment.user_id == user.id,
        StudyEnrollment.organization_id == user.organization_id,
    ).order_by(StudyEnrollment.id)).all()
    salida = []
    for i in filas:
        plan = db.get(StudyPlan, i.plan_id)
        if plan is not None:
            salida.append(_out(db, i, plan))
    return salida


@router.get("/me/{enrollment_id}", response_model=InscripcionDetalle)
def mi_detalle(enrollment_id: int, user: CurrentUser = Depends(_STAFF), db: Session = Depends(get_db)):
    insc = _inscripcion_propia(db, user, enrollment_id)
    plan = db.get(StudyPlan, insc.plan_id)
    p, h, t, hh, ht, mods, avance = _resumen(db, insc, plan)
    return InscripcionDetalle(
        **_out(db, insc, plan).model_dump(),
        modules=[AvanceModulo(
            id=m.id, position=m.position, title=m.title, objective=m.objective, topics=m.topics,
            lab=m.lab, estimated_hours=m.estimated_hours, weight_percent=m.weight_percent,
            status=(avance[m.id].status if m.id in avance else "pending"),
            hours_spent=(avance[m.id].hours_spent if m.id in avance else None),
            evidence_url=(avance[m.id].evidence_url if m.id in avance else None),
            notes=(avance[m.id].notes if m.id in avance else None),
            progress_id=(avance[m.id].id if m.id in avance else None),
            validated=bool(m.id in avance and avance[m.id].status == "validated"),
        ) for m in mods],
    )


@router.patch("/me/{enrollment_id}/modules/{module_id}", response_model=InscripcionOut)
def marcar_avance(enrollment_id: int, module_id: int, payload: AvanceIn,
                  user: CurrentUser = Depends(_STAFF), db: Session = Depends(get_db)):
    insc = _inscripcion_propia(db, user, enrollment_id)
    modulo = db.scalar(select(StudyModule).where(
        StudyModule.id == module_id, StudyModule.plan_id == insc.plan_id))
    if modulo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Módulo no encontrado")
    fila = db.scalar(select(StudyProgress).where(
        StudyProgress.enrollment_id == insc.id, StudyProgress.module_id == module_id))
    if fila is None:
        fila = StudyProgress(enrollment_id=insc.id, module_id=module_id, status="pending")
        db.add(fila)
    # Una vez validado por un tutor, quien estudia no lo puede desmarcar: la validacion
    # es un juicio de otra persona sobre un contenido concreto. Si cambia, hay que volver
    # a validarlo, no borrarlo en silencio.
    if fila.status == "validated" and payload.status != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Este módulo ya fue validado por un tutor; no se puede retroceder.")
    ahora = utcnow()
    if payload.status != "pending" and fila.started_at is None:
        fila.started_at = ahora
    fila.completed_at = ahora if payload.status == "completed" else None
    if fila.status != "validated":
        fila.status = payload.status
    for campo in ("hours_spent", "evidence_url", "notes"):
        valor = getattr(payload, campo)
        if valor is not None:
            setattr(fila, campo, valor)
    db.commit()
    return _out(db, insc, db.get(StudyPlan, insc.plan_id))


@router.get("/team", response_model=list[EquipoFila])
def avance_del_equipo(user: CurrentUser = Depends(_ADMIN), db: Session = Depends(get_db)):
    filas = db.scalars(select(StudyEnrollment).where(
        StudyEnrollment.organization_id == user.organization_id).order_by(StudyEnrollment.id)).all()
    salida = []
    for i in filas:
        plan, persona = db.get(StudyPlan, i.plan_id), db.get(User, i.user_id)
        if plan is None or persona is None:
            continue
        p, h, t, _, _, mods, avance = _resumen(db, i, plan)
        salida.append(EquipoFila(
            enrollment_id=i.id, user_id=persona.id, user_name=persona.full_name,
            plan_name=plan.name, percent=p, modules_done=h, modules_total=t,
            pending_validation=sum(1 for m in mods if m.id in avance and avance[m.id].status == "completed"),
        ))
    return salida


@router.get("/team/{enrollment_id}", response_model=InscripcionDetalle)
def detalle_del_equipo(enrollment_id: int, user: CurrentUser = Depends(_ADMIN),
                       db: Session = Depends(get_db)):
    """El detalle de la inscripcion de cualquier persona de la organizacion, para validar."""
    insc = db.scalar(select(StudyEnrollment).where(
        StudyEnrollment.id == enrollment_id,
        StudyEnrollment.organization_id == user.organization_id))
    if insc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inscripción no encontrada")
    plan = db.get(StudyPlan, insc.plan_id)
    _, _, _, _, _, mods, avance = _resumen(db, insc, plan)
    return InscripcionDetalle(
        **_out(db, insc, plan).model_dump(),
        modules=[AvanceModulo(
            id=m.id, position=m.position, title=m.title, objective=m.objective, topics=m.topics,
            lab=m.lab, estimated_hours=m.estimated_hours, weight_percent=m.weight_percent,
            status=(avance[m.id].status if m.id in avance else "pending"),
            hours_spent=(avance[m.id].hours_spent if m.id in avance else None),
            evidence_url=(avance[m.id].evidence_url if m.id in avance else None),
            notes=(avance[m.id].notes if m.id in avance else None),
            progress_id=(avance[m.id].id if m.id in avance else None),
            validated=bool(m.id in avance and avance[m.id].status == "validated"),
        ) for m in mods],
    )


@router.post("/progress/{progress_id}/validate", response_model=dict)
def validar(progress_id: int, user: CurrentUser = Depends(_ADMIN), db: Session = Depends(get_db)):
    fila = db.get(StudyProgress, progress_id)
    insc = db.get(StudyEnrollment, fila.enrollment_id) if fila else None
    # Otra organizacion: 404, no 403.
    if fila is None or insc is None or insc.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avance no encontrado")
    if insc.user_id == user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No puedes validar tu propio avance.")
    if fila.status != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se valida un módulo marcado como completado.")
    fila.status = "validated"
    fila.validated_by = user.id
    fila.validated_at = utcnow()
    AuditService(db).record(
        organization_id=user.organization_id, action="validate", entity_type="study_progress",
        entity_id=str(fila.id), user_id=user.id,
    )
    db.commit()
    return {"id": fila.id, "status": fila.status}
