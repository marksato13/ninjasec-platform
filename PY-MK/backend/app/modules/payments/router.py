"""Hitos de pago de un proyecto (C3): cuanto se cobra, cuando y en que estado esta.

    GET    /payment-milestones/projects/{id}   los hitos y el resumen   (admin o el cliente dueno)
    POST   /payment-milestones/projects/{id}   crear un hito            (admin)
    PUT    /payment-milestones/{id}            editar o cambiar estado  (admin)
    DELETE /payment-milestones/{id}            quitar uno no pagado     (admin)

Solo estado: no hay pasarela, ni datos bancarios, ni comprobantes.

## Quien ve que

- **Admin / super admin:** los de su organizacion, y los gestiona.
- **Cliente:** solo los de SU proyecto, en lectura.
- **Colaborador:** nada. Lo que cobra la empresa no es parte de su trabajo (403 por rol).

Un proyecto ajeno devuelve **404**, no 403: no se confirma que exista.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode
from app.db.models.payment_milestone import PaymentMilestone
from app.db.models.project import Project
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/payment-milestones", tags=["payment-milestones"])

_ADMINS = {RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value}
Estado = Literal["pending", "invoiced", "paid"]
Moneda = Literal["PEN", "USD"]


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class HitoIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Moneda = "PEN"
    due_date: date | None = None
    status: Estado = "pending"
    note: str | None = Field(default=None, max_length=500)


class HitoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: Moneda | None = None
    due_date: date | None = None
    status: Estado | None = None
    note: str | None = Field(default=None, max_length=500)


class HitoOut(BaseModel):
    id: int
    project_id: int
    title: str
    amount: Decimal
    currency: str
    due_date: date | None
    status: str
    overdue: bool
    note: str | None
    paid_at: datetime | None


class TotalOut(BaseModel):
    currency: str
    total: Decimal
    paid: Decimal
    pending: Decimal


class HitosOut(BaseModel):
    project_id: int
    can_manage: bool
    milestones: list[HitoOut]
    totals: list[TotalOut]


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------


def _proyecto(db: Session, user: CurrentUser, project_id: int) -> tuple[Project, bool]:
    """(proyecto, puede_gestionar). 404 si no le corresponde; 403 si su rol no ve pagos."""
    if user.role not in _ADMINS and user.role != RoleCode.CLIENT.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    nada = HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    p = db.get(Project, project_id)
    if p is None:
        raise nada
    if user.role in _ADMINS:
        if p.organization_id != user.organization_id:
            raise nada
        return p, True
    perfil = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
    if perfil is None or p.client_id != perfil.client_id or p.organization_id != user.organization_id:
        raise nada
    return p, False


def _hito_gestionable(db: Session, user: CurrentUser, milestone_id: int) -> PaymentMilestone:
    if user.role not in _ADMINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    h = db.get(PaymentMilestone, milestone_id)
    if h is None or h.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
    return h


# --------------------------------------------------------------------------
# Vista
# --------------------------------------------------------------------------


def _out(h: PaymentMilestone, hoy: date) -> HitoOut:
    return HitoOut(
        id=h.id, project_id=h.project_id, title=h.title, amount=h.amount, currency=h.currency,
        due_date=h.due_date, status=h.status, note=h.note, paid_at=h.paid_at,
        overdue=h.status != "paid" and h.due_date is not None and h.due_date < hoy,
    )


def _vista(db: Session, p: Project, puede: bool) -> HitosOut:
    hitos = db.scalars(
        select(PaymentMilestone)
        .where(PaymentMilestone.project_id == p.id)
        .order_by(PaymentMilestone.due_date.is_(None), PaymentMilestone.due_date, PaymentMilestone.id)
    ).all()
    hoy = utcnow().date()
    totales: dict[str, TotalOut] = {}
    for h in hitos:
        t = totales.setdefault(h.currency, TotalOut(currency=h.currency, total=Decimal("0"),
                                                    paid=Decimal("0"), pending=Decimal("0")))
        t.total += h.amount
        if h.status == "paid":
            t.paid += h.amount
        else:
            t.pending += h.amount
    return HitosOut(project_id=p.id, can_manage=puede, milestones=[_out(h, hoy) for h in hitos],
                    totals=sorted(totales.values(), key=lambda t: t.currency))


def _auditar(db: Session, user: CurrentUser, h: PaymentMilestone, accion: str, extra: dict | None = None) -> None:
    datos = {"project_id": h.project_id, "status": h.status, "amount": str(h.amount), "currency": h.currency}
    datos.update(extra or {})
    AuditService(db).record(
        organization_id=h.organization_id, action=accion, entity_type="payment_milestone",
        entity_id=str(h.id), user_id=user.id, metadata_json=json.dumps(datos, ensure_ascii=False),
    )


def _fijar_estado(h: PaymentMilestone, nuevo: str) -> None:
    if nuevo == "paid" and h.paid_at is None:
        h.paid_at = utcnow()
    if nuevo != "paid":
        h.paid_at = None
    h.status = nuevo


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------


@router.get("/projects/{project_id}", response_model=HitosOut)
def ver_hitos(project_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p, puede = _proyecto(db, user, project_id)
    return _vista(db, p, puede)


@router.post("/projects/{project_id}", response_model=HitosOut, status_code=status.HTTP_201_CREATED)
def crear_hito(project_id: int, payload: HitoIn, user: CurrentUser = Depends(get_current_user),
               db: Session = Depends(get_db)):
    p, puede = _proyecto(db, user, project_id)
    if not puede:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    h = PaymentMilestone(
        organization_id=p.organization_id, project_id=p.id, title=payload.title.strip(),
        amount=payload.amount, currency=payload.currency, due_date=payload.due_date,
        note=(payload.note or "").strip() or None, created_by=user.id, status="pending",
    )
    _fijar_estado(h, payload.status)
    db.add(h)
    db.flush()
    _auditar(db, user, h, "payment_milestone.created")
    db.commit()
    return _vista(db, p, True)


@router.put("/{milestone_id}", response_model=HitosOut)
def editar_hito(milestone_id: int, payload: HitoUpdate, user: CurrentUser = Depends(get_current_user),
                db: Session = Depends(get_db)):
    h = _hito_gestionable(db, user, milestone_id)
    anterior = h.status
    cambios = payload.model_dump(exclude_unset=True)
    if "title" in cambios and cambios["title"] is not None:
        h.title = cambios["title"].strip()
    if cambios.get("amount") is not None:
        h.amount = cambios["amount"]
    if cambios.get("currency") is not None:
        h.currency = cambios["currency"]
    if "due_date" in cambios:
        h.due_date = cambios["due_date"]
    if "note" in cambios:
        h.note = (cambios["note"] or "").strip() or None
    if cambios.get("status") is not None:
        _fijar_estado(h, cambios["status"])
    db.flush()
    accion = "payment_milestone.status_updated" if h.status != anterior else "payment_milestone.updated"
    _auditar(db, user, h, accion, {"from": anterior} if h.status != anterior else None)
    db.commit()
    return _vista(db, db.get(Project, h.project_id), True)


@router.delete("/{milestone_id}", response_model=HitosOut)
def quitar_hito(milestone_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Devuelve la vista actualizada (no 204): el cliente HTTP del panel siempre espera JSON."""
    h = _hito_gestionable(db, user, milestone_id)
    if h.status == "paid":
        # Un pago registrado es historia: se corrige editandolo, no borrandolo.
        raise HTTPException(status.HTTP_409_CONFLICT, "Un hito pagado no se puede quitar.")
    proyecto = db.get(Project, h.project_id)
    _auditar(db, user, h, "payment_milestone.deleted", {"title": h.title})
    db.delete(h)
    db.commit()
    return _vista(db, proyecto, True)
