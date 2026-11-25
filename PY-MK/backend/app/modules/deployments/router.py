"""Registro de despliegues de los sistemas del cliente (35-P-02).

    GET    /deployments                listar (filtros ?system_id= ?environment_id= ?project_id=)
    GET    /deployments/{id}           detalle
    POST   /deployments                registrar          (admin, o colaborador que ve el sistema)
    PUT    /deployments/{id}           corregir o cambiar el resultado (admin, o quien lo registró)
    DELETE /deployments/{id}           quitar un registro erróneo      (admin)

## Quién ve qué

Se apoya en la visibilidad de los sistemas (35-P-01): un despliegue se ve si
se ve su sistema.

- **Admin / super admin:** todo lo de su organización.
- **Colaborador:** los de los sistemas de sus proyectos; los registra él.
- **Cliente:** solo los despliegues a `prod` de sus sistemas que llegaron a
  producción (`ok` o `revertido`), con versión, fecha, resumen y resultado.
  Nunca el checklist, el plan de vuelta atrás ni quién lo hizo. Es otro
  esquema de salida, no un filtro sobre el mismo.

Lo ajeno devuelve **404**.

## Reglas

- El entorno debe ser del sistema (422).
- A `prod` con resultado `ok` exige **respaldo** y **prueba de humo** marcados (422).
- Un `ok` a `prod` publica "Versión X publicada" en la bitácora del proyecto,
  visible para el cliente. Una sola vez por despliegue.
- Sin secretos en versión, resumen ni plan de vuelta atrás (422).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.client_system import ClientSystem, ClientSystemEnvironment
from app.db.models.client_system_deployment import ClientSystemDeployment
from app.db.models.enums import RoleCode
from app.db.models.project import Project
from app.db.models.project_tracking import ProjectUpdate
from app.db.models.user import User
from app.modules.audit.services.audit_service import AuditService
from app.modules.client_systems.router import _consulta_visible, _sin_secretos

router = APIRouter(prefix="/deployments", tags=["deployments"])

_ADMINS = {RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value}
Resultado = Literal["ok", "fallido", "revertido"]
_VISIBLES_AL_CLIENTE = ("ok", "revertido")
"""Lo que llegó a producción. Un intento fallido no cambió nada que el cliente use."""
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+\-/]{0,59}$")
_MARGEN_FUTURO = timedelta(minutes=5)


# --------------------------------------------------------------------------
# Esquemas de entrada
# --------------------------------------------------------------------------


def _version(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if not _VERSION.match(v):
        raise ValueError("La versión es una etiqueta o un SHA corto: letras, números, '.', '-', '_', '+' o '/'.")
    return _sin_secretos(v)


def _fecha(v: datetime | None) -> datetime | None:
    if v is None:
        return None
    if v.tzinfo is not None:  # se guarda en UTC sin zona, como el resto de la base
        v = v.astimezone(timezone.utc).replace(tzinfo=None)
    if v > utcnow() + _MARGEN_FUTURO:
        raise ValueError("Un despliegue no puede tener fecha futura.")
    return v


class DespliegueIn(BaseModel):
    system_id: int
    environment_id: int
    version: str = Field(min_length=1, max_length=60)
    summary: str = Field(min_length=3, max_length=500)
    deployed_at: datetime | None = None
    backup_done: bool = False
    smoke_test_passed: bool = False
    rollback_plan_written: bool = False
    rollback_plan: str | None = Field(default=None, max_length=500)
    result: Resultado = "ok"
    project_id: int | None = None

    @field_validator("version")
    @classmethod
    def _v(cls, v: str | None) -> str | None:
        return _version(v)

    @field_validator("summary", "rollback_plan")
    @classmethod
    def _t(cls, v: str | None) -> str | None:
        return _sin_secretos(v)

    @field_validator("deployed_at")
    @classmethod
    def _f(cls, v: datetime | None) -> datetime | None:
        return _fecha(v)


class DespliegueUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=60)
    summary: str | None = Field(default=None, min_length=3, max_length=500)
    deployed_at: datetime | None = None
    backup_done: bool | None = None
    smoke_test_passed: bool | None = None
    rollback_plan_written: bool | None = None
    rollback_plan: str | None = Field(default=None, max_length=500)
    result: Resultado | None = None

    @field_validator("version")
    @classmethod
    def _v(cls, v: str | None) -> str | None:
        return _version(v)

    @field_validator("summary", "rollback_plan")
    @classmethod
    def _t(cls, v: str | None) -> str | None:
        return _sin_secretos(v)

    @field_validator("deployed_at")
    @classmethod
    def _f(cls, v: datetime | None) -> datetime | None:
        return _fecha(v)


# --------------------------------------------------------------------------
# Esquemas de salida
# --------------------------------------------------------------------------


class DespliegueClienteOut(BaseModel):
    id: int
    system_id: int
    system_name: str
    environment_kind: str
    version: str
    summary: str
    deployed_at: datetime
    result: str


class DespliegueEquipoOut(DespliegueClienteOut):
    environment_id: int | None
    deployed_by: int | None
    deployed_by_name: str | None
    backup_done: bool
    smoke_test_passed: bool
    rollback_plan_written: bool
    rollback_plan: str | None
    project_id: int | None
    published_update_id: int | None
    can_edit: bool


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------


def _es_cliente(user: CurrentUser) -> bool:
    return user.role == RoleCode.CLIENT.value


def _puede_registrar(user: CurrentUser) -> None:
    if user.role not in _ADMINS and user.role != RoleCode.COLLABORATOR.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")


def _puede_editar(user: CurrentUser, d: ClientSystemDeployment) -> bool:
    return user.role in _ADMINS or (user.role == RoleCode.COLLABORATOR.value and d.deployed_by == user.id)


def _consulta(db: Session, user: CurrentUser):
    """Despliegues que este usuario puede leer: los de los sistemas que ve, en su organización."""
    sistemas = _consulta_visible(db, user).with_only_columns(ClientSystem.id)
    q = select(ClientSystemDeployment).where(
        ClientSystemDeployment.organization_id == user.organization_id,
        ClientSystemDeployment.system_id.in_(sistemas),
    )
    if _es_cliente(user):
        q = q.where(ClientSystemDeployment.environment_kind == "prod",
                    ClientSystemDeployment.result.in_(_VISIBLES_AL_CLIENTE))
    return q


def _visible(db: Session, user: CurrentUser, deployment_id: int) -> ClientSystemDeployment:
    d = db.scalar(_consulta(db, user).where(ClientSystemDeployment.id == deployment_id))
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deployment not found")
    return d


def _sistema_visible(db: Session, user: CurrentUser, system_id: int) -> ClientSystem:
    s = db.scalar(_consulta_visible(db, user).where(ClientSystem.id == system_id))
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "System not found")
    return s


def _entorno_del_sistema(db: Session, user: CurrentUser, s: ClientSystem, env_id: int) -> ClientSystemEnvironment:
    e = db.get(ClientSystemEnvironment, env_id)
    if e is None or e.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Environment not found")
    if e.system_id != s.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ese entorno es de otro sistema.")
    return e


def _proyecto(db: Session, user: CurrentUser, s: ClientSystem, project_id: int | None) -> int | None:
    """El proyecto explícito o, si no hay, el de origen del sistema."""
    if project_id is None:
        return s.origin_project_id
    p = db.get(Project, project_id)
    if p is None or p.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if p.client_id != s.client_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El proyecto es de otro cliente.")
    return p.id


# --------------------------------------------------------------------------
# Reglas
# --------------------------------------------------------------------------


def _exigir_checklist(d: ClientSystemDeployment) -> None:
    if d.environment_kind == "prod" and d.result == "ok":
        faltan = [n for n, ok in (("respaldo", d.backup_done), ("prueba de humo", d.smoke_test_passed)) if not ok]
        if faltan:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Un despliegue correcto a producción exige marcar: {' y '.join(faltan)}.",
            )


def _publicar(db: Session, user: CurrentUser, d: ClientSystemDeployment, entorno: ClientSystemEnvironment | None) -> None:
    """Un ok a prod deja "Versión X publicada" en la bitácora del proyecto. Una sola vez."""
    if d.environment_kind != "prod" or d.result != "ok" or d.project_id is None or d.published_update_id:
        return
    u = ProjectUpdate(
        organization_id=d.organization_id, project_id=d.project_id, author_user_id=user.id, kind="update",
        title=f"Versión {d.version} publicada"[:160], body=d.summary,
        link_url=entorno.url if entorno is not None and entorno.visible_to_client else None,
        visible_to_client=True,
    )
    db.add(u)
    db.flush()
    d.published_update_id = u.id


def _auditar(db: Session, user: CurrentUser, d: ClientSystemDeployment, accion: str, extra: dict | None = None) -> None:
    datos = {"system_id": d.system_id, "environment_kind": d.environment_kind, "version": d.version,
             "result": d.result, **(extra or {})}
    AuditService(db).record(
        organization_id=user.organization_id, action=accion, entity_type="client_system_deployment",
        entity_id=str(d.id), user_id=user.id, metadata_json=json.dumps(datos, ensure_ascii=False, default=str),
    )


# --------------------------------------------------------------------------
# Vista
# --------------------------------------------------------------------------


def _out(db: Session, user: CurrentUser, d: ClientSystemDeployment) -> dict:
    s = db.get(ClientSystem, d.system_id)
    base = dict(id=d.id, system_id=d.system_id, system_name=s.name if s else "", environment_kind=d.environment_kind,
                version=d.version, summary=d.summary, deployed_at=d.deployed_at, result=d.result)
    if _es_cliente(user):
        return DespliegueClienteOut(**base).model_dump(mode="json")
    autor = db.get(User, d.deployed_by) if d.deployed_by else None
    return DespliegueEquipoOut(
        **base, environment_id=d.environment_id, deployed_by=d.deployed_by,
        deployed_by_name=(autor.full_name or autor.email) if autor else None,
        backup_done=d.backup_done, smoke_test_passed=d.smoke_test_passed,
        rollback_plan_written=d.rollback_plan_written, rollback_plan=d.rollback_plan,
        project_id=d.project_id, published_update_id=d.published_update_id, can_edit=_puede_editar(user, d),
    ).model_dump(mode="json")


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------


@router.get("", response_model=None)
def listar_despliegues(
    system_id: int | None = Query(default=None),
    environment_id: int | None = Query(default=None),
    project_id: int | None = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    q = _consulta(db, user)
    if system_id is not None:
        q = q.where(ClientSystemDeployment.system_id == system_id)
    if environment_id is not None:
        q = q.where(ClientSystemDeployment.environment_id == environment_id)
    if project_id is not None:
        q = q.where(ClientSystemDeployment.project_id == project_id)
    filas = db.scalars(q.order_by(ClientSystemDeployment.deployed_at.desc(), ClientSystemDeployment.id.desc())).all()
    return {
        "can_register": user.role in _ADMINS or user.role == RoleCode.COLLABORATOR.value,
        "deployments": [_out(db, user, d) for d in filas],
    }


@router.get("/{deployment_id:int}", response_model=None)
def ver_despliegue(deployment_id: int, user: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    return _out(db, user, _visible(db, user, deployment_id))


@router.post("", response_model=None, status_code=status.HTTP_201_CREATED)
def registrar_despliegue(payload: DespliegueIn, user: CurrentUser = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> dict:
    _puede_registrar(user)
    s = _sistema_visible(db, user, payload.system_id)
    e = _entorno_del_sistema(db, user, s, payload.environment_id)
    d = ClientSystemDeployment(
        organization_id=user.organization_id, system_id=s.id, environment_id=e.id, environment_kind=e.kind,
        version=payload.version, summary=payload.summary.strip(), deployed_by=user.id,
        deployed_at=payload.deployed_at or utcnow(), backup_done=payload.backup_done,
        smoke_test_passed=payload.smoke_test_passed, rollback_plan_written=payload.rollback_plan_written,
        rollback_plan=(payload.rollback_plan or "").strip() or None, result=payload.result,
        project_id=_proyecto(db, user, s, payload.project_id),
    )
    _exigir_checklist(d)
    db.add(d)
    db.flush()
    _publicar(db, user, d, e)
    _auditar(db, user, d, "client_system_deployment.created",
             {"published_update_id": d.published_update_id})
    db.commit()
    db.refresh(d)
    return _out(db, user, d)


@router.put("/{deployment_id:int}", response_model=None)
def editar_despliegue(deployment_id: int, payload: DespliegueUpdate, user: CurrentUser = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> dict:
    _puede_registrar(user)
    d = _visible(db, user, deployment_id)
    if not _puede_editar(user, d):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo quien lo registró o un administrador lo corrige.")
    cambios = payload.model_dump(exclude_unset=True)
    anterior = d.result
    for campo in ("version", "result", "backup_done", "smoke_test_passed", "rollback_plan_written", "deployed_at"):
        if cambios.get(campo) is not None:
            setattr(d, campo, cambios[campo])
    if cambios.get("summary") is not None:
        d.summary = cambios["summary"].strip()
    if "rollback_plan" in cambios:
        d.rollback_plan = (cambios["rollback_plan"] or "").strip() or None
    _exigir_checklist(d)
    entorno = db.get(ClientSystemEnvironment, d.environment_id) if d.environment_id else None
    _publicar(db, user, d, entorno)
    db.flush()
    cambio = d.result != anterior
    _auditar(db, user, d, "client_system_deployment.result_updated" if cambio else "client_system_deployment.updated",
             {"fields": sorted(cambios), **({"from": anterior} if cambio else {})})
    db.commit()
    db.refresh(d)
    return _out(db, user, d)


@router.delete("/{deployment_id:int}", response_model=None)
def quitar_despliegue(deployment_id: int, user: CurrentUser = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Solo para un registro erróneo. Devuelve JSON (no 204): el cliente HTTP del panel espera JSON.
    El avance ya publicado en la bitácora se queda: lo que el cliente vio no se reescribe en silencio."""
    if user.role not in _ADMINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    d = _visible(db, user, deployment_id)
    _auditar(db, user, d, "client_system_deployment.deleted")
    db.delete(d)
    db.commit()
    return {"deleted": deployment_id}
