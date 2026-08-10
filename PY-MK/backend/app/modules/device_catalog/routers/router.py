from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.catalog_device import CatalogDevice
from app.db.models.catalog_device_link import CatalogDeviceLink
from app.db.models.catalog_device_summary import CatalogDeviceSummary
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import RoleCode
from app.db.models.integration import Integration
from app.db.repositories.base import Repository
from app.modules.audit.services.audit_service import AuditService
from app.modules.device_catalog.schemas import (
    CatalogDeviceCreate,
    CatalogDeviceDetail,
    CatalogDeviceLinkCreate,
    CatalogDeviceLinkRead,
    CatalogDeviceRead,
    CatalogDeviceSummaryRead,
    CatalogDeviceSummaryUpsert,
    CatalogDeviceUpdate,
)

router = APIRouter(prefix="/catalog/devices", tags=["catalog-devices"])

# Consulta: todos los roles internos. Edición del modelo: solo
# super_admin/admin. El resumen ejecutivo lo puede editar también
# collaborator (ver 29-MODULO-CATALOGO-EQUIPOS.md § Acciones disponibles).
# El rol client no tiene acceso -- este catálogo es una herramienta interna
# de preventa/soporte, no un dato que el portal cliente necesite hoy.
_READ_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
_WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
_SUMMARY_WRITE_ROLES = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.COLLABORATOR.value,
)


def _instance_count(db: Session, current_user: CurrentUser, brand: str, model: str) -> int:
    """Cuántos `Device` del parque instalado de la organización actual
    corresponden a este modelo. Cruce best-effort por texto (vendor/model
    son campos libres, no hay FK a CatalogDevice) -- mismo alcance de
    aislamiento por organización que DeviceService._base_stmt()."""
    stmt = (
        select(func.count(Device.id))
        .outerjoin(Integration, Device.integration_id == Integration.id)
        .outerjoin(ClientSite, Device.site_id == ClientSite.id)
        .where(
            or_(
                Integration.organization_id == current_user.organization_id,
                ClientSite.client.has(organization_id=current_user.organization_id),
            ),
            func.lower(Device.vendor) == brand.lower(),
            func.lower(Device.model) == model.lower(),
        )
    )
    return db.scalar(stmt) or 0


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


@router.get("/{device_id}", response_model=CatalogDeviceDetail)
def get_catalog_device(
    device_id: int,
    current_user: CurrentUser = Depends(require_roles(*_READ_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceDetail:
    device = Repository(db).get_by_id(CatalogDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Catalog device not found")

    links = db.scalars(
        select(CatalogDeviceLink)
        .where(CatalogDeviceLink.catalog_device_id == device_id)
        .order_by(CatalogDeviceLink.link_type)
    ).all()
    summary = db.scalar(
        select(CatalogDeviceSummary).where(
            CatalogDeviceSummary.catalog_device_id == device_id
        )
    )
    count = _instance_count(db, current_user, device.brand, device.model)

    return CatalogDeviceDetail(
        **CatalogDeviceRead.model_validate(device).model_dump(),
        links=[CatalogDeviceLinkRead.model_validate(link) for link in links],
        summary=CatalogDeviceSummaryRead.model_validate(summary) if summary else None,
        instance_count=count,
    )


@router.post(
    "/{device_id}/links",
    response_model=CatalogDeviceLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def add_catalog_device_link(
    device_id: int,
    payload: CatalogDeviceLinkCreate,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceLinkRead:
    device = Repository(db).get_by_id(CatalogDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Catalog device not found")

    link = CatalogDeviceLink(catalog_device_id=device_id, **payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    AuditService(db).record(
        current_user.organization_id,
        "catalog_device_link.created",
        "catalog_device_links",
        str(link.id),
        current_user.id,
    )
    return CatalogDeviceLinkRead.model_validate(link)


@router.delete("/{device_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_device_link(
    device_id: int,
    link_id: int,
    current_user: CurrentUser = Depends(require_roles(*_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> None:
    link = db.scalar(
        select(CatalogDeviceLink).where(
            CatalogDeviceLink.id == link_id,
            CatalogDeviceLink.catalog_device_id == device_id,
        )
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()
    AuditService(db).record(
        current_user.organization_id,
        "catalog_device_link.deleted",
        "catalog_device_links",
        str(link_id),
        current_user.id,
    )


@router.put("/{device_id}/summary", response_model=CatalogDeviceSummaryRead)
def upsert_catalog_device_summary(
    device_id: int,
    payload: CatalogDeviceSummaryUpsert,
    current_user: CurrentUser = Depends(require_roles(*_SUMMARY_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogDeviceSummaryRead:
    device = Repository(db).get_by_id(CatalogDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Catalog device not found")

    summary = db.scalar(
        select(CatalogDeviceSummary).where(
            CatalogDeviceSummary.catalog_device_id == device_id
        )
    )
    if summary:
        summary.content = payload.content
        summary.source_note = payload.source_note
        summary.updated_by_user_id = current_user.id
    else:
        summary = CatalogDeviceSummary(
            catalog_device_id=device_id,
            content=payload.content,
            source_note=payload.source_note,
            updated_by_user_id=current_user.id,
        )
        db.add(summary)

    db.commit()
    db.refresh(summary)
    AuditService(db).record(
        current_user.organization_id,
        "catalog_device_summary.updated",
        "catalog_device_summaries",
        str(device_id),
        current_user.id,
    )
    return CatalogDeviceSummaryRead.model_validate(summary)


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
