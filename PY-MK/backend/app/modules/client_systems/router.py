"""Sistemas del cliente y sus entornos (35-P-01).

    GET    /client-systems                         listar (filtro ?client_id=)
    GET    /client-systems/{id}                    ficha con entornos
    POST   /client-systems                         crear                    (admin)
    PUT    /client-systems/{id}                    editar o cambiar estado  (admin)
    DELETE /client-systems/{id}                    quitar uno en construcción (admin)
    POST   /client-systems/{id}/environments       añadir entorno           (admin)
    PUT    /client-systems/environments/{env_id}   editar entorno           (admin)
    DELETE /client-systems/environments/{env_id}   quitar entorno           (admin)

## Quién ve qué

- **Admin / super admin:** todo lo de su organización; crea y edita.
- **Colaborador:** en lectura, los sistemas cuyo proyecto de origen tiene a él
  como miembro (la planificación dice "de los proyectos donde es miembro").
- **Cliente:** solo los suyos, SIN `repository_url` ni `secrets_location`, y
  solo los entornos marcados `visible_to_client`. Es otro esquema de salida,
  no un filtro sobre el mismo: lo interno no viaja.

Lo ajeno devuelve **404**, no 403: no se confirma que exista. El 403 es solo
para un rol que no puede gestionar.

## Borrar

Un sistema solo se quita mientras está `en_construccion` (se creó por error).
Uno que llegó a producción es historia: se marca `retirado` (409 si no). Al
quitarlo caen sus entornos, y la auditoría guarda cuántos eran.

## Secretos

Ninguno. `secrets_location` dice dónde están ("gestor de la empresa, entrada
X"); un valor con forma de clave, token o llave privada se rechaza con 422.
Las URL tampoco aceptan usuario ni contraseña embebidos.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user
from app.common.deps.database import get_db
from app.core.time_utils import utcnow
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_system import ClientSystem, ClientSystemEnvironment
from app.db.models.enums import RoleCode
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/client-systems", tags=["client-systems"])

_ADMINS = {RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value}
AVISO_DIAS = 30
"""La plataforma avisa con este margen de garantía, dominio y certificado por vencer."""

Estado = Literal["en_construccion", "en_produccion", "en_mantenimiento", "retirado"]
Plan = Literal["ninguno", "basico", "profesional", "a_medida"]
Tipo = Literal["dev", "staging", "prod"]

# Formas de secreto conocidas. No pretende ser exhaustivo: evita el error
# común de pegar la clave en vez de decir dónde está.
_SECRETO = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|sk_(live|test)_[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}"
    r"|-----BEGIN [A-Z ]*(PRIVATE KEY|CERTIFICATE)|AKIA[0-9A-Z]{12,}|xox[abprs]-[A-Za-z0-9-]{8,}"
    r"|AIza[0-9A-Za-z_-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|(password|passwd|contrase[nñ]a|clave|token|secret)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


def _sin_secretos(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor = valor.strip()
    if _SECRETO.search(valor):
        raise ValueError("Escribe dónde está la clave (p. ej. 'gestor de la empresa, entrada X'), nunca la clave.")
    return valor or None


def _url_limpia(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    partes = urlsplit(valor)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError("La URL debe empezar por http:// o https://")
    if partes.username or partes.password:
        raise ValueError("La URL no puede llevar usuario ni contraseña.")
    return valor


def _texto(valor: str | None) -> str | None:
    return (valor or "").strip() or None


# --------------------------------------------------------------------------
# Esquemas de entrada
# --------------------------------------------------------------------------


class SistemaIn(BaseModel):
    client_id: int
    name: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=300)
    stack: str | None = Field(default=None, max_length=160)
    repository_url: str | None = Field(default=None, max_length=500)
    status: Estado = "en_construccion"
    warranty_until: date | None = None
    support_plan: Plan = "ninguno"
    origin_project_id: int | None = None

    @field_validator("repository_url")
    @classmethod
    def _repo(cls, v: str | None) -> str | None:
        return _url_limpia(v)

    @field_validator("description", "stack")
    @classmethod
    def _textos(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


class SistemaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=300)
    stack: str | None = Field(default=None, max_length=160)
    repository_url: str | None = Field(default=None, max_length=500)
    status: Estado | None = None
    warranty_until: date | None = None
    support_plan: Plan | None = None
    origin_project_id: int | None = None

    @field_validator("repository_url")
    @classmethod
    def _repo(cls, v: str | None) -> str | None:
        return _url_limpia(v)

    @field_validator("description", "stack")
    @classmethod
    def _textos(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


class EntornoIn(BaseModel):
    kind: Tipo
    url: str | None = Field(default=None, max_length=500)
    hosting: str | None = Field(default=None, max_length=120)
    domain_expires_at: date | None = None
    certificate_expires_at: date | None = None
    secrets_location: str | None = Field(default=None, max_length=300)
    visible_to_client: bool = False

    @field_validator("url")
    @classmethod
    def _url(cls, v: str | None) -> str | None:
        return _url_limpia(v)

    @field_validator("hosting", "secrets_location")
    @classmethod
    def _textos(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


class EntornoUpdate(BaseModel):
    kind: Tipo | None = None
    url: str | None = Field(default=None, max_length=500)
    hosting: str | None = Field(default=None, max_length=120)
    domain_expires_at: date | None = None
    certificate_expires_at: date | None = None
    secrets_location: str | None = Field(default=None, max_length=300)
    visible_to_client: bool | None = None

    @field_validator("url")
    @classmethod
    def _url(cls, v: str | None) -> str | None:
        return _url_limpia(v)

    @field_validator("hosting", "secrets_location")
    @classmethod
    def _textos(cls, v: str | None) -> str | None:
        return _sin_secretos(v)


# --------------------------------------------------------------------------
# Esquemas de salida: uno para el equipo, otro (recortado) para el cliente
# --------------------------------------------------------------------------


class EntornoClienteOut(BaseModel):
    id: int
    kind: str
    url: str | None
    hosting: str | None
    domain_expires_at: date | None
    certificate_expires_at: date | None
    expiring_soon: bool
    """Dominio o certificado vence en 30 días o menos (o ya venció)."""


class EntornoEquipoOut(EntornoClienteOut):
    secrets_location: str | None
    visible_to_client: bool


class SistemaClienteOut(BaseModel):
    id: int
    client_id: int
    name: str
    description: str | None
    stack: str | None
    status: str
    warranty_until: date | None
    warranty_expiring: bool
    support_plan: str
    environments: list[EntornoClienteOut]


class SistemaEquipoOut(SistemaClienteOut):
    client_name: str | None
    repository_url: str | None
    origin_project_id: int | None
    environments: list[EntornoEquipoOut]  # type: ignore[assignment]


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------


def _nada() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "System not found")


def _solo_admin(user: CurrentUser) -> None:
    if user.role not in _ADMINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")


def _cliente_del_usuario(db: Session, user: CurrentUser) -> int | None:
    perfil = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
    return perfil.client_id if perfil else None


def _proyectos_del_colaborador(db: Session, user: CurrentUser):
    return select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)


def _consulta_visible(db: Session, user: CurrentUser):
    """SELECT de los sistemas que este usuario puede leer. Nunca sale de su organización."""
    q = select(ClientSystem).where(ClientSystem.organization_id == user.organization_id)
    if user.role in _ADMINS:
        return q
    if user.role == RoleCode.COLLABORATOR.value:
        return q.where(ClientSystem.origin_project_id.in_(_proyectos_del_colaborador(db, user)))
    if user.role == RoleCode.CLIENT.value:
        cliente = _cliente_del_usuario(db, user)
        if cliente is None:
            return q.where(False)
        return q.where(ClientSystem.client_id == cliente)
    return q.where(False)


def _sistema_visible(db: Session, user: CurrentUser, system_id: int) -> ClientSystem:
    s = db.scalar(_consulta_visible(db, user).where(ClientSystem.id == system_id))
    if s is None:
        raise _nada()
    return s


def _sistema_gestionable(db: Session, user: CurrentUser, system_id: int) -> ClientSystem:
    _solo_admin(user)
    s = db.get(ClientSystem, system_id)
    if s is None or s.organization_id != user.organization_id:
        raise _nada()
    return s


def _entorno_gestionable(db: Session, user: CurrentUser, env_id: int) -> ClientSystemEnvironment:
    _solo_admin(user)
    e = db.get(ClientSystemEnvironment, env_id)
    if e is None or e.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Environment not found")
    return e


def _cliente_de_la_org(db: Session, user: CurrentUser, client_id: int) -> Client:
    c = db.get(Client, client_id)
    if c is None or c.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return c


def _validar_proyecto_origen(db: Session, user: CurrentUser, project_id: int | None, client_id: int) -> None:
    if project_id is None:
        return
    p = db.get(Project, project_id)
    if p is None or p.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if p.client_id != client_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El proyecto de origen es de otro cliente.")


# --------------------------------------------------------------------------
# Vista
# --------------------------------------------------------------------------


def _por_vencer(fecha: date | None, hoy: date) -> bool:
    return fecha is not None and fecha <= hoy + timedelta(days=AVISO_DIAS)


def _entorno_out(e: ClientSystemEnvironment, hoy: date, equipo: bool):
    base = dict(
        id=e.id, kind=e.kind, url=e.url, hosting=e.hosting,
        domain_expires_at=e.domain_expires_at, certificate_expires_at=e.certificate_expires_at,
        expiring_soon=_por_vencer(e.domain_expires_at, hoy) or _por_vencer(e.certificate_expires_at, hoy),
    )
    if equipo:
        return EntornoEquipoOut(**base, secrets_location=e.secrets_location, visible_to_client=e.visible_to_client)
    return EntornoClienteOut(**base)


def _sistema_out(db: Session, s: ClientSystem, equipo: bool) -> SistemaEquipoOut | SistemaClienteOut:
    hoy = utcnow().date()
    entornos = [
        _entorno_out(e, hoy, equipo) for e in s.environments if equipo or e.visible_to_client
    ]
    base = dict(
        id=s.id, client_id=s.client_id, name=s.name, description=s.description, stack=s.stack,
        status=s.status, warranty_until=s.warranty_until, support_plan=s.support_plan,
        warranty_expiring=s.status != "retirado" and _por_vencer(s.warranty_until, hoy),
        environments=entornos,
    )
    if equipo:
        cliente = db.get(Client, s.client_id)
        return SistemaEquipoOut(**base, client_name=cliente.company_name if cliente else None,
                                repository_url=s.repository_url, origin_project_id=s.origin_project_id)
    return SistemaClienteOut(**base)


def _es_equipo(user: CurrentUser) -> bool:
    return user.role != RoleCode.CLIENT.value


def _ficha(db: Session, user: CurrentUser, s: ClientSystem) -> dict:
    """Respuesta de detalle. Se serializa aquí, con el esquema del rol, para que
    lo interno no pueda colarse por un response_model compartido."""
    datos = _sistema_out(db, s, _es_equipo(user)).model_dump(mode="json")
    datos["can_manage"] = user.role in _ADMINS
    return datos


def _auditar(db: Session, user: CurrentUser, entidad: str, entidad_id: int, accion: str, datos: dict) -> None:
    AuditService(db).record(
        organization_id=user.organization_id, action=accion, entity_type=entidad,
        entity_id=str(entidad_id), user_id=user.id, metadata_json=json.dumps(datos, ensure_ascii=False, default=str),
    )


def _commit_o_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese sistema ya tiene un entorno de ese tipo.")


# --------------------------------------------------------------------------
# Rutas: sistemas
# --------------------------------------------------------------------------


@router.get("", response_model=None)
def listar_sistemas(
    client_id: int | None = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    q = _consulta_visible(db, user)
    if client_id is not None:
        q = q.where(ClientSystem.client_id == client_id)
    sistemas = db.scalars(q.order_by(ClientSystem.name, ClientSystem.id)).all()
    equipo = _es_equipo(user)
    return {
        "can_manage": user.role in _ADMINS,
        "systems": [_sistema_out(db, s, equipo).model_dump(mode="json") for s in sistemas],
    }


@router.get("/{system_id:int}", response_model=None)
def ver_sistema(system_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _ficha(db, user, _sistema_visible(db, user, system_id))


@router.post("", response_model=None, status_code=status.HTTP_201_CREATED)
def crear_sistema(payload: SistemaIn, user: CurrentUser = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> dict:
    _solo_admin(user)
    _cliente_de_la_org(db, user, payload.client_id)
    _validar_proyecto_origen(db, user, payload.origin_project_id, payload.client_id)
    s = ClientSystem(
        organization_id=user.organization_id, client_id=payload.client_id, name=payload.name.strip(),
        description=_texto(payload.description), stack=_texto(payload.stack), repository_url=payload.repository_url,
        status=payload.status, warranty_until=payload.warranty_until, support_plan=payload.support_plan,
        origin_project_id=payload.origin_project_id, created_by=user.id,
    )
    db.add(s)
    db.flush()
    _auditar(db, user, "client_system", s.id, "client_system.created",
             {"client_id": s.client_id, "name": s.name, "status": s.status})
    db.commit()
    db.refresh(s)
    return _ficha(db, user, s)


@router.put("/{system_id:int}", response_model=None)
def editar_sistema(system_id: int, payload: SistemaUpdate, user: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    s = _sistema_gestionable(db, user, system_id)
    cambios = payload.model_dump(exclude_unset=True)
    if "origin_project_id" in cambios:
        _validar_proyecto_origen(db, user, cambios["origin_project_id"], s.client_id)
    anterior = s.status
    for campo in ("name", "status", "support_plan"):
        if cambios.get(campo) is not None:
            setattr(s, campo, cambios[campo].strip() if campo == "name" else cambios[campo])
    for campo in ("description", "stack"):
        if campo in cambios:
            setattr(s, campo, _texto(cambios[campo]))
    for campo in ("repository_url", "warranty_until", "origin_project_id"):
        if campo in cambios:
            setattr(s, campo, cambios[campo])
    db.flush()
    cambio_estado = s.status != anterior
    _auditar(db, user, "client_system", s.id,
             "client_system.status_updated" if cambio_estado else "client_system.updated",
             {"fields": sorted(cambios), "status": s.status, **({"from": anterior} if cambio_estado else {})})
    db.commit()
    db.refresh(s)
    return _ficha(db, user, s)


@router.delete("/{system_id:int}", response_model=None)
def quitar_sistema(system_id: int, user: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Devuelve JSON (no 204): el cliente HTTP del panel siempre espera JSON."""
    s = _sistema_gestionable(db, user, system_id)
    if s.status != "en_construccion":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Un sistema que llegó a producción no se quita: márcalo como retirado.")
    _auditar(db, user, "client_system", s.id, "client_system.deleted",
             {"client_id": s.client_id, "name": s.name, "environments": len(s.environments)})
    db.delete(s)
    db.commit()
    return {"deleted": system_id}


# --------------------------------------------------------------------------
# Rutas: entornos
# --------------------------------------------------------------------------


@router.post("/{system_id:int}/environments", response_model=None, status_code=status.HTTP_201_CREATED)
def crear_entorno(system_id: int, payload: EntornoIn, user: CurrentUser = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> dict:
    s = _sistema_gestionable(db, user, system_id)
    e = ClientSystemEnvironment(
        organization_id=s.organization_id, system_id=s.id, kind=payload.kind, url=payload.url,
        hosting=_texto(payload.hosting), domain_expires_at=payload.domain_expires_at,
        certificate_expires_at=payload.certificate_expires_at, secrets_location=_texto(payload.secrets_location),
        visible_to_client=payload.visible_to_client,
    )
    db.add(e)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese sistema ya tiene un entorno de ese tipo.")
    # Sin secrets_location en la auditoría: basta con saber que cambió.
    _auditar(db, user, "client_system_environment", e.id, "client_system_environment.created",
             {"system_id": s.id, "kind": e.kind, "visible_to_client": e.visible_to_client})
    _commit_o_409(db)
    db.refresh(s)
    return _ficha(db, user, s)


@router.put("/environments/{env_id}", response_model=None)
def editar_entorno(env_id: int, payload: EntornoUpdate, user: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    e = _entorno_gestionable(db, user, env_id)
    cambios = payload.model_dump(exclude_unset=True)
    if cambios.get("kind") is not None:
        e.kind = cambios["kind"]
    if cambios.get("visible_to_client") is not None:
        e.visible_to_client = cambios["visible_to_client"]
    for campo in ("url", "domain_expires_at", "certificate_expires_at"):
        if campo in cambios:
            setattr(e, campo, cambios[campo])
    for campo in ("hosting", "secrets_location"):
        if campo in cambios:
            setattr(e, campo, _texto(cambios[campo]))
    system_id = e.system_id
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese sistema ya tiene un entorno de ese tipo.")
    _auditar(db, user, "client_system_environment", e.id, "client_system_environment.updated",
             {"system_id": system_id, "kind": e.kind, "fields": sorted(cambios)})
    _commit_o_409(db)
    s = db.get(ClientSystem, system_id)
    db.refresh(s)
    return _ficha(db, user, s)


@router.delete("/environments/{env_id}", response_model=None)
def quitar_entorno(env_id: int, user: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    e = _entorno_gestionable(db, user, env_id)
    s = db.get(ClientSystem, e.system_id)
    _auditar(db, user, "client_system_environment", e.id, "client_system_environment.deleted",
             {"system_id": s.id, "kind": e.kind})
    db.delete(e)
    db.commit()
    db.refresh(s)
    return _ficha(db, user, s)
