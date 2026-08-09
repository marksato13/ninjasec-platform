from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.catalog_device import CatalogDevice
from app.db.models.enums import RoleCode
from app.db.repositories.base import Repository
from app.modules.audit.services.audit_service import AuditService
from app.modules.device_catalog.schemas import (
    CatalogDeviceCreate,
    CatalogDeviceRead,
    CatalogDeviceUpdate,
)

router = APIRouter(prefix="/catalog/devices", tags=["catalog-devices"])

# Consulta: todos los roles internos. Edición: solo super_admin/admin.
# El rol client no tiene acceso -- este catálogo es una herramienta interna
# de preventa/soporte, no un dato que el portal cliente necesite hoy.
_READ_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
_WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.get("/", response_model=list[CatalogDeviceRead])
def list_catalog_devices(
    brand: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    osi_layer: str | None = None,
    segment: str | None = None,
    lifecycle_status: str | None = None,
    poe: bool | None = None,
    stackable: bool | None = None,
    rack_mountable: bool | None = None,
    managed: bool | None = None,
    q: str | None = None,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[CatalogDeviceRead]:
    stmt = select(CatalogDevice)
    if brand:
        stmt = stmt.where(CatalogDevice.brand.ilike(brand))
    if category:
        stmt = stmt.where(CatalogDevice.category == category)
    if subcategory:
        stmt = stmt.where(CatalogDevice.subcategory == subcategory)
    if osi_layer:
        stmt = stmt.where(CatalogDevice.osi_layer == osi_layer)
    if segment:
        stmt = stmt.where(CatalogDevice.segment == segment)
    if lifecycle_status:
        stmt = stmt.where(CatalogDevice.lifecycle_status == lifecycle_status)
    if poe is not None:
        stmt = stmt.where(CatalogDevice.poe == poe)
    if stackable is not None:
        stmt = stmt.where(CatalogDevice.stackable == stackable)
    if rack_mountable is not None:
        stmt = stmt.where(CatalogDevice.rack_mountable == rack_mountable)
    if managed is not None:
        stmt = stmt.where(CatalogDevice.managed == managed)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (CatalogDevice.brand.ilike(like))
            | (CatalogDevice.model.ilike(like))
            | (CatalogDevice.tags.ilike(like))
        )
    stmt = stmt.order_by(CatalogDevice.brand, CatalogDevice.model)
    return [CatalogDeviceRead.model_validate(d) for d in db.scalars(stmt).all()]


@router.get("/{device_id}", response_model=CatalogDeviceRead)
def get_catalog_device(
    device_id: int,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceRead:
    device = Repository(db).get_by_id(CatalogDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Catalog device not found")
    return CatalogDeviceRead.model_validate(device)


@router.post("/", response_model=CatalogDeviceRead, status_code=status.HTTP_201_CREATED)
def create_catalog_device(
    payload: CatalogDeviceCreate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceRead:
    existing = db.scalar(select(CatalogDevice).where(CatalogDevice.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    device = CatalogDevice(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    AuditService(db).record(
        current_user.organization_id,
        "catalog_device.created",
        "catalog_devices",
        str(device.id),
        current_user.id,
    )
    return CatalogDeviceRead.model_validate(device)


@router.put("/{device_id}", response_model=CatalogDeviceRead)
def update_catalog_device(
    device_id: int,
    payload: CatalogDeviceUpdate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceRead:
    # 29-P1: el slug es estable e inmutable. CatalogDeviceUpdate ni
    # siquiera expone el campo -- no hay forma de mandarlo por esta vía,
    # así que nunca puede cambiar en silencio ni a propósito.
    device = Repository(db).get_by_id(CatalogDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Catalog device not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    db.add(device)
    db.commit()
    db.refresh(device)
    AuditService(db).record(
        current_user.organization_id,
        "catalog_device.updated",
        "catalog_devices",
        str(device.id),
        current_user.id,
    )
    return CatalogDeviceRead.model_validate(device)
