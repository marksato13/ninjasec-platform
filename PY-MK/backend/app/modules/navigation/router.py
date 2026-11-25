"""Menus editables por rol.

Tres lecturas y una escritura:

    GET  /navigation/public   sin sesion: la barra del sitio web
    GET  /navigation/me       con sesion: los menus del panel y del portal
    GET  /navigation/config   super_admin: la matriz completa, para editarla
    PUT  /navigation/config   super_admin: guardar cambios

Esto decide **que se muestra**, no que se permite. El motivo y el limite estan
en `app/core/navegacion.py`; en corto: el que manda sobre el acceso real es
`require_roles` en cada endpoint, y el editor ni siquiera deja mostrar una
opcion a un rol al que el backend no se la dejaria usar.
"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user, require_roles
from app.common.deps.database import get_db
from app.core.config import settings
from app.core.features import esta_activa
from app.core.navegacion import (
    SUPERFICIES,
    Opcion,
    audiencias_de,
    opcion,
    opciones_de,
)
from app.core.time_utils import utcnow
from app.db.models.enums import RoleCode
from app.db.models.nav_visibility import NavVisibility
from app.db.models.organization import Organization
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/navigation", tags=["navigation"])

_SUPER_ADMIN = require_roles(RoleCode.SUPER_ADMIN.value)

Superficie = Literal["public", "staff", "portal"]


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class Cambio(BaseModel):
    superficie: Superficie
    clave: str = Field(min_length=1, max_length=120)
    audiencia: str = Field(min_length=1, max_length=20)
    visible: bool


class CambiosIn(BaseModel):
    cambios: list[Cambio] = Field(min_length=1, max_length=200)


# --------------------------------------------------------------------------
# Logica
# --------------------------------------------------------------------------


def _excepciones(
    db: Session, organization_id: int, superficie: str
) -> dict[tuple[str, str], bool]:
    filas = db.scalars(
        select(NavVisibility).where(
            NavVisibility.organization_id == organization_id,
            NavVisibility.surface == superficie,
        )
    ).all()
    return {(f.item_key, f.audience): f.visible for f in filas}


def _capsula_encendida(o: Opcion) -> bool:
    return o.capsula is None or esta_activa(o.capsula, settings.capsulas_activas)


def _visible(o: Opcion, audiencia: str, ex: dict[tuple[str, str], bool]) -> bool:
    if audiencia not in o.permitidas:
        return False
    if not _capsula_encendida(o):
        return False
    return ex.get((o.clave, audiencia), True)


def _claves_visibles(
    db: Session, organization_id: int, superficie: str, audiencia: str
) -> list[str]:
    ex = _excepciones(db, organization_id, superficie)
    return [o.clave for o in opciones_de(superficie) if _visible(o, audiencia, ex)]


def _organizacion_del_sitio(db: Session) -> Organization | None:
    """El sitio web publico pertenece a la organizacion principal.

    No hay sesion, asi que no hay `organization_id` del usuario. En una
    instalacion de una sola organizacion es la unica; si hubiera varias, manda
    la marcada como interna.
    """
    org = db.scalar(select(Organization).where(Organization.slug == "ninjasec-internal"))
    return org or db.scalar(select(Organization).order_by(Organization.id))


def _matriz(db: Session, organization_id: int) -> dict:
    salida: dict = {}
    for superficie, audiencias in SUPERFICIES.items():
        ex = _excepciones(db, organization_id, superficie)
        opciones = []
        for o in opciones_de(superficie):
            opciones.append({
                "clave": o.clave,
                "etiqueta": o.etiqueta,
                "grupo": o.grupo,
                "capsula": o.capsula,
                "capsula_encendida": _capsula_encendida(o),
                "permitidas": list(audiencias_de(o)),
                "obligatoria_para": list(o.obligatoria_para),
                # Solo las audiencias a las que tiene sentido mostrarla.
                "visible": {a: ex.get((o.clave, a), True) for a in audiencias_de(o)},
            })
        salida[superficie] = {"audiencias": list(audiencias), "opciones": opciones}
    return {"superficies": salida}


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.get("/public")
def menu_publico(db: Session = Depends(get_db)) -> dict:
    org = _organizacion_del_sitio(db)
    if org is None:
        return {"visibles": [o.clave for o in opciones_de("public")]}
    return {"visibles": _claves_visibles(db, org.id, "public", "visitor")}


@router.get("/me")
def mis_menus(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rol = current_user.role
    salida: dict = {"role": rol, "staff": None, "portal": None}
    for superficie in ("staff", "portal"):
        if rol in SUPERFICIES[superficie]:
            salida[superficie] = _claves_visibles(
                db, current_user.organization_id, superficie, rol
            )
    return salida


@router.get("/config")
def leer_configuracion(
    current_user: CurrentUser = Depends(_SUPER_ADMIN),
    db: Session = Depends(get_db),
) -> dict:
    return _matriz(db, current_user.organization_id)


@router.put("/config")
def guardar_configuracion(
    payload: CambiosIn,
    current_user: CurrentUser = Depends(_SUPER_ADMIN),
    db: Session = Depends(get_db),
) -> dict:
    # Se valida TODO antes de tocar nada: un lote a medias dejaria el menu
    # en un estado que nadie pidio.
    for c in payload.cambios:
        o = opcion(c.superficie, c.clave)
        if o is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"No existe la opcion '{c.clave}' en el menu '{c.superficie}'.",
            )
        if c.audiencia not in SUPERFICIES[c.superficie]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"'{c.audiencia}' no es una audiencia del menu '{c.superficie}'.",
            )
        if c.audiencia not in o.permitidas:
            # Mostrar un enlace que termina en un 403 es peor que no mostrarlo.
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"'{o.etiqueta}' no esta disponible para '{c.audiencia}': el backend "
                "no le deja usar esa pantalla, asi que mostrarla no serviria de nada.",
            )
        if not c.visible and c.audiencia in o.obligatoria_para:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"'{o.etiqueta}' no se puede ocultar para '{c.audiencia}': "
                "dejaria a alguien sin forma de entrar o de deshacer el cambio.",
            )

    org_id = current_user.organization_id
    ahora = utcnow()
    aplicados = []
    for c in payload.cambios:
        fila = db.scalar(
            select(NavVisibility).where(
                NavVisibility.organization_id == org_id,
                NavVisibility.surface == c.superficie,
                NavVisibility.item_key == c.clave,
                NavVisibility.audience == c.audiencia,
            )
        )
        if c.visible:
            # Es el valor por defecto: se borra la excepcion, no se guarda otra.
            if fila is not None:
                db.delete(fila)
        elif fila is None:
            db.add(NavVisibility(
                organization_id=org_id, surface=c.superficie, item_key=c.clave,
                audience=c.audiencia, visible=False,
                updated_by_user_id=current_user.id, updated_at=ahora,
            ))
        else:
            fila.visible = False
            fila.updated_by_user_id = current_user.id
            fila.updated_at = ahora
        aplicados.append(c.model_dump())

    AuditService(db).record(
        organization_id=org_id,
        action="update",
        entity_type="nav_visibility",
        user_id=current_user.id,
        metadata_json=json.dumps({"cambios": aplicados}, ensure_ascii=False),
    )
    db.commit()
    return _matriz(db, org_id)
