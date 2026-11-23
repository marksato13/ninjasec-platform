from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.enums import RoleCode, SiteStatus
from app.modules.audit.services.audit_service import AuditService
from app.modules.client_sites.schemas import ClientSiteCreate, ClientSiteRead, ClientSiteUpdate

router = APIRouter(prefix="/client-sites", tags=["client-sites"])


# `client_sites` no lleva organization_id: el tenant se deriva por su cliente.
# Estas dos ayudas son el unico camino permitido para llegar a una sede, y
# replican el patron ya establecido en clients/routers/client_services.py.
def _cliente_de_mi_org(client_id: int, org_id: int, db: Session) -> Client:
    cliente = db.get(Client, client_id)
    if not cliente or cliente.organization_id != org_id:
        # 404 y no 403: un 403 confirmaria que el cliente existe.
        raise HTTPException(status_code=404, detail="Client not found")
    return cliente


def _sede_de_mi_org(site_id: int, org_id: int, db: Session) -> ClientSite:
    sede = db.scalar(
        select(ClientSite)
        .join(Client, Client.id == ClientSite.client_id)
        .where(ClientSite.id == site_id, Client.organization_id == org_id)
    )
    if not sede:
        raise HTTPException(status_code=404, detail="Site not found")
    return sede


@router.get("/", response_model=list[ClientSiteRead])
def list_client_sites(
    client_id: int | None = None,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value,
            RoleCode.ADMIN.value,
            RoleCode.COLLABORATOR.value,
            RoleCode.CLIENT.value,
        )
    ),
    db: Session = Depends(get_db),
) -> list[ClientSiteRead]:
    if current_user.role == RoleCode.CLIENT.value:
        # 05-P-05: un cliente del portal solo ve las sedes de su propia
        # empresa -- cualquier client_id que mande en la query se ignora.
        profile = db.scalar(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        if not profile:
            return []
        stmt = select(ClientSite).where(ClientSite.client_id == profile.client_id)
        return [ClientSiteRead.model_validate(s) for s in db.scalars(stmt).all()]

    # Antes: `select(ClientSite)` sin ninguna condicion -- devolvia las sedes
    # de todos los clientes de todas las organizaciones.
    stmt = (
        select(ClientSite)
        .join(Client, Client.id == ClientSite.client_id)
        .where(Client.organization_id == current_user.organization_id)
    )
    if client_id:
        stmt = stmt.where(ClientSite.client_id == client_id)
    return [ClientSiteRead.model_validate(s) for s in db.scalars(stmt).all()]


@router.post("/", response_model=ClientSiteRead, status_code=status.HTTP_201_CREATED)
def create_client_site(
    payload: ClientSiteCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ClientSiteRead:
    # Sin esto, se podia crear una sede DENTRO del cliente de otra organizacion
    # simplemente mandando su client_id en el payload.
    _cliente_de_mi_org(payload.client_id, current_user.organization_id, db)

    site = ClientSite(
        client_id=payload.client_id,
        name=payload.name,
        address=payload.address,
        city=payload.city,
        country=payload.country,
        status=SiteStatus(payload.status),
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    AuditService(db).record(
        current_user.organization_id, "client_site.created", "client_sites", str(site.id), current_user.id
    )
    return ClientSiteRead.model_validate(site)


@router.put("/{site_id}", response_model=ClientSiteRead)
def update_client_site(
    site_id: int,
    payload: ClientSiteUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ClientSiteRead:
    site = _sede_de_mi_org(site_id, current_user.organization_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "status" and value is not None:
            value = SiteStatus(value)
        setattr(site, field, value)
    db.add(site)
    db.commit()
    db.refresh(site)
    AuditService(db).record(
        current_user.organization_id, "client_site.updated", "client_sites", str(site.id), current_user.id
    )
    return ClientSiteRead.model_validate(site)


@router.delete("/{site_id}")
def delete_client_site(
    site_id: int,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    # Era el peor de los cuatro: un admin podia BORRAR fisicamente la sede de
    # un cliente de otra organizacion pasando su id.
    site = _sede_de_mi_org(site_id, current_user.organization_id, db)
    db.delete(site)
    db.commit()
    AuditService(db).record(
        current_user.organization_id, "client_site.deleted", "client_sites", str(site_id), current_user.id
    )
    return {"message": "Site deleted"}
