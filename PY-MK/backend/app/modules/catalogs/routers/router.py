import json
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, get_current_user, require_roles
from app.common.deps.database import get_db
from app.db.models.area import Area
from app.db.models.enums import RoleCode
from app.db.models.product import Product
from app.db.models.project import Project
from app.db.models.project_type import ProjectType
from app.db.models.service import Service
from app.modules.audit.services.audit_service import AuditService
from app.modules.catalogs.schemas import (
    AreaCreate,
    AreaRead,
    AreaUpdate,
    ProductRead,
    ProjectTypeCreate,
    ProjectTypeRead,
    ProjectTypeUpdate,
)

router = APIRouter(prefix="", tags=["catalogs"])

_ADMIN = require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


def slugify(value: str) -> str:
    """'Redes y Seguridad' -> 'redes-y-seguridad'."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _visible_to(model, organization_id: int):
    """Registros de la organizacion del usuario, mas los globales.

    Area y ProjectType tienen organization_id nullable: NULL significa
    "catalogo compartido por todas las organizaciones" (los que siembra
    el seed). Cualquier otro valor es dato de un tenant concreto y no
    debe cruzarse. Ver 20-P-10.
    """
    return or_(
        model.organization_id == organization_id,
        model.organization_id.is_(None),
    )


@router.get("/areas", response_model=list[AreaRead])
def list_areas(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AreaRead]:
    stmt = select(Area).where(
        Area.is_active == True,
        _visible_to(Area, current_user.organization_id),
    )
    return [AreaRead.model_validate(item) for item in db.scalars(stmt).all()]


@router.get("/project-types", response_model=list[ProjectTypeRead])
def list_project_types(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectTypeRead]:
    stmt = select(ProjectType).where(
        ProjectType.is_active == True,
        _visible_to(ProjectType, current_user.organization_id),
    )
    return [ProjectTypeRead.model_validate(item) for item in db.scalars(stmt).all()]


@router.get("/products", response_model=list[ProductRead])
def list_products(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    # Product.organization_id es NOT NULL: es dato por tenant, nunca catalogo global.
    stmt = select(Product).where(
        Product.is_active == True,
        Product.organization_id == current_user.organization_id,
    )
    return [ProductRead.model_validate(item) for item in db.scalars(stmt).all()]


# ---------------------------------------------------------------------------
# Escritura de catalogos (20-P-06)
#
# Hasta ahora solo habia GET: crear un area exigia SQL directo contra la base
# o tocar el seed. Esto convierte Configuracion en un panel de verdad.
#
# Reglas comunes:
#   - Solo admin y super_admin escriben.
#   - Lo que se crea nace con el organization_id de quien lo crea. No hay
#     forma de crear catalogos globales por API: los globales son del seed.
#   - No se borra, se desactiva. Un area referenciada por proyectos
#     historicos no puede desaparecer sin romperlos.
# ---------------------------------------------------------------------------


def _assert_nombre_libre(db: Session, model, name: str, organization_id: int, exclude_id: int | None = None) -> None:
    """Impide duplicados dentro de la misma organizacion.

    No es solo cortesia: sin esto el usuario recibiria un IntegrityError
    crudo de la restriccion unique compuesta (20-P-09).
    """
    stmt = select(model).where(
        model.name == name,
        or_(model.organization_id == organization_id, model.organization_id.is_(None)),
    )
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un registro con el nombre '{name}'",
        )


def _get_editable(db: Session, model, item_id: int, organization_id: int):
    """Recupera un registro propio y editable.

    Un catalogo global (organization_id NULL) se ve pero no se toca: lo
    comparten todas las organizaciones y editarlo afectaria a terceros.
    """
    item = db.scalar(select(model).where(model.id == item_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if item.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este catalogo es global y no puede modificarse desde una organizacion",
        )
    if item.organization_id != organization_id:
        # 404 y no 403: no confirmamos la existencia de datos ajenos.
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return item


def _contar_uso(db: Session, model, item_id: int) -> int:
    """Cuantos registros dependen de este catalogo (20-P-07)."""
    if model is Area:
        return (
            db.query(Project).filter(Project.area_id == item_id).count()
            + db.query(Service).filter(Service.area_id == item_id).count()
            + db.query(Product).filter(Product.area_id == item_id).count()
        )
    return (
        db.query(Project).filter(Project.project_type_id == item_id).count()
        + db.query(Service).filter(Service.project_type_id == item_id).count()
    )


def _crear(db, model, schema_read, payload, current_user, entidad: str):
    name = payload.name.strip()
    _assert_nombre_libre(db, model, name, current_user.organization_id)

    item = model(
        organization_id=current_user.organization_id,
        name=name,
        slug=(payload.slug or slugify(name)),
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    AuditService(db).record(
        current_user.organization_id,
        f"{entidad}.created",
        entidad,
        str(item.id),
        current_user.id,
        metadata_json=json.dumps({"name": item.name}, ensure_ascii=True),
    )
    return schema_read.model_validate(item)


def _actualizar(db, model, schema_read, item_id, payload, current_user, entidad: str):
    item = _get_editable(db, model, item_id, current_user.organization_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"]:
        nuevo = data["name"].strip()
        if nuevo != item.name:
            _assert_nombre_libre(
                db, model, nuevo, current_user.organization_id, exclude_id=item.id
            )
        item.name = nuevo

    en_uso = 0
    if data.get("is_active") is False and item.is_active:
        # 20-P-07: desactivar un area usada por 12 proyectos no puede ser
        # silencioso. No se bloquea (el historico sigue siendo valido),
        # pero queda registrado cuanto arrastra.
        en_uso = _contar_uso(db, model, item.id)
    if "is_active" in data and data["is_active"] is not None:
        item.is_active = data["is_active"]

    db.add(item)
    db.commit()
    db.refresh(item)

    AuditService(db).record(
        current_user.organization_id,
        f"{entidad}.updated",
        entidad,
        str(item.id),
        current_user.id,
        metadata_json=json.dumps(
            {"name": item.name, "is_active": item.is_active, "registros_afectados": en_uso},
            ensure_ascii=True,
        ),
    )
    return schema_read.model_validate(item)


@router.post("/areas", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
def create_area(
    payload: AreaCreate,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> AreaRead:
    return _crear(db, Area, AreaRead, payload, current_user, "areas")


@router.put("/areas/{area_id}", response_model=AreaRead)
def update_area(
    area_id: int,
    payload: AreaUpdate,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> AreaRead:
    return _actualizar(db, Area, AreaRead, area_id, payload, current_user, "areas")


@router.get("/areas/{area_id}/usage")
def area_usage(
    area_id: int,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Cuantos registros quedarian huerfanos al desactivar (20-P-07)."""
    _get_editable(db, Area, area_id, current_user.organization_id)
    return {"in_use_by": _contar_uso(db, Area, area_id)}


@router.post(
    "/project-types", response_model=ProjectTypeRead, status_code=status.HTTP_201_CREATED
)
def create_project_type(
    payload: ProjectTypeCreate,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> ProjectTypeRead:
    return _crear(db, ProjectType, ProjectTypeRead, payload, current_user, "project_types")


@router.put("/project-types/{type_id}", response_model=ProjectTypeRead)
def update_project_type(
    type_id: int,
    payload: ProjectTypeUpdate,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> ProjectTypeRead:
    return _actualizar(
        db, ProjectType, ProjectTypeRead, type_id, payload, current_user, "project_types"
    )


@router.get("/project-types/{type_id}/usage")
def project_type_usage(
    type_id: int,
    current_user: CurrentUser = Depends(_ADMIN),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    _get_editable(db, ProjectType, type_id, current_user.organization_id)
    return {"in_use_by": _contar_uso(db, ProjectType, type_id)}
