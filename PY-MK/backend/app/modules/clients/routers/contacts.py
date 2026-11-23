from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.client import Client
from app.db.models.client_contact import ClientContact
from app.db.models.enums import RoleCode
from app.modules.audit.services.audit_service import AuditService
from app.modules.client_contacts.schemas import (
    ClientContactCreate,
    ClientContactRead,
    ClientContactUpdate,
)

router = APIRouter(prefix="/client-contacts", tags=["client-contacts"])


# `client_contacts` no lleva organization_id: el tenant se deriva por su
# cliente. Estas dos ayudas son el unico camino permitido para llegar a un
# contacto, y replican el patron de clients/routers/client_services.py.
def _cliente_de_mi_org(client_id: int, org_id: int, db: Session) -> Client:
    cliente = db.get(Client, client_id)
    if not cliente or cliente.organization_id != org_id:
        # 404 y no 403: un 403 confirmaria que el cliente existe.
        raise HTTPException(status_code=404, detail="Client not found")
    return cliente


def _contacto_de_mi_org(contact_id: int, org_id: int, db: Session) -> ClientContact:
    contacto = db.scalar(
        select(ClientContact)
        .join(Client, Client.id == ClientContact.client_id)
        .where(ClientContact.id == contact_id, Client.organization_id == org_id)
    )
    if not contacto:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contacto


@router.get("/", response_model=list[ClientContactRead])
def list_client_contacts(
    client_id: int | None = None,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
    ),
    db: Session = Depends(get_db),
) -> list[ClientContactRead]:
    # Antes: `select(ClientContact)` sin ninguna condicion -- devolvia nombre,
    # correo, telefono y cargo de TODOS los contactos de TODOS los clientes de
    # TODAS las organizaciones. Fuga de datos personales entre tenants.
    stmt = (
        select(ClientContact)
        .join(Client, Client.id == ClientContact.client_id)
        .where(Client.organization_id == current_user.organization_id)
    )
    if client_id:
        stmt = stmt.where(ClientContact.client_id == client_id)
    return [ClientContactRead.model_validate(c) for c in db.scalars(stmt).all()]


@router.post("/", response_model=ClientContactRead, status_code=status.HTTP_201_CREATED)
def create_client_contact(
    payload: ClientContactCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ClientContactRead:
    # Sin esto, se podia crear un contacto DENTRO del cliente de otra
    # organizacion mandando su client_id en el payload.
    _cliente_de_mi_org(payload.client_id, current_user.organization_id, db)

    contact = ClientContact(**payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    AuditService(db).record(
        current_user.organization_id, "client_contact.created", "client_contacts", str(contact.id), current_user.id
    )
    return ClientContactRead.model_validate(contact)


@router.put("/{contact_id}", response_model=ClientContactRead)
def update_client_contact(
    contact_id: int,
    payload: ClientContactUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> ClientContactRead:
    contact = _contacto_de_mi_org(contact_id, current_user.organization_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    AuditService(db).record(
        current_user.organization_id, "client_contact.updated", "client_contacts", str(contact.id), current_user.id
    )
    return ClientContactRead.model_validate(contact)


@router.delete("/{contact_id}")
def delete_client_contact(
    contact_id: int,
    current_user: CurrentUser = Depends(
        require_roles(RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
    ),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    contact = _contacto_de_mi_org(contact_id, current_user.organization_id, db)
    db.delete(contact)
    db.commit()
    AuditService(db).record(
        current_user.organization_id, "client_contact.deleted", "client_contacts", str(contact_id), current_user.id
    )
    return {"message": "Contact deleted"}
