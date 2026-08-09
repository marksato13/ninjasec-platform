from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.architecture import ArchitectureElement, ArchitectureModel, ArchitectureRelationship
from app.db.models.client import Client
from app.db.models.enums import RoleCode
from app.modules.architecture.schemas import (ElementCreate, ElementRead, ElementUpdate, ModelCreate, ModelRead, ModelUpdate, RelationshipCreate, RelationshipRead, RelationshipUpdate)
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/architecture", tags=["architecture"])
READ_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)
WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


def _model(db: Session, user: CurrentUser, model_id: int, *, mutable: bool = False) -> ArchitectureModel:
    model = db.scalar(select(ArchitectureModel).options(selectinload(ArchitectureModel.elements), selectinload(ArchitectureModel.relationships)).where(ArchitectureModel.id == model_id, ArchitectureModel.organization_id == user.organization_id))
    if not model:
        raise HTTPException(404, "Architecture model not found")
    if mutable and model.status == "approved":
        raise HTTPException(409, "Approved architecture models are immutable")
    return model


def _commit(db: Session, user: CurrentUser, entity: object, action: str) -> None:
    db.add(entity); db.commit(); db.refresh(entity)
    AuditService(db).record(user.organization_id, action, type(entity).__name__, str(getattr(entity, "id")), user.id)


@router.get("/models", response_model=list[ModelRead])
def list_models(current_user: CurrentUser = Depends(require_roles(*READ_ROLES)), db: Session = Depends(get_db)):
    stmt = select(ArchitectureModel).options(selectinload(ArchitectureModel.elements), selectinload(ArchitectureModel.relationships)).where(ArchitectureModel.organization_id == current_user.organization_id)
    return db.scalars(stmt).all()


@router.post("/models", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelCreate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    client = db.scalar(select(Client).where(Client.id == payload.client_id, Client.organization_id == current_user.organization_id))
    if not client: raise HTTPException(404, "Client not found")
    item = ArchitectureModel(organization_id=current_user.organization_id, **payload.model_dump())
    _commit(db, current_user, item, "architecture_model.created")
    return _model(db, current_user, item.id)


@router.get("/models/{model_id}", response_model=ModelRead)
def get_model(model_id: int, current_user: CurrentUser = Depends(require_roles(*READ_ROLES)), db: Session = Depends(get_db)):
    return _model(db, current_user, model_id)


@router.put("/models/{model_id}", response_model=ModelRead)
def update_model(model_id: int, payload: ModelUpdate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = _model(db, current_user, model_id, mutable=True)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    _commit(db, current_user, item, "architecture_model.updated")
    return _model(db, current_user, model_id)


@router.delete("/models/{model_id}", status_code=204)
def delete_model(model_id: int, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = _model(db, current_user, model_id, mutable=True); db.delete(item); db.commit()
    AuditService(db).record(current_user.organization_id, "architecture_model.deleted", "ArchitectureModel", str(model_id), current_user.id)


@router.post("/models/{model_id}/elements", response_model=ElementRead, status_code=201)
def create_element(model_id: int, payload: ElementCreate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    _model(db, current_user, model_id, mutable=True); item = ArchitectureElement(model_id=model_id, **payload.model_dump()); _commit(db, current_user, item, "architecture_element.created"); return item


@router.put("/elements/{element_id}", response_model=ElementRead)
def update_element(element_id: int, payload: ElementUpdate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = db.get(ArchitectureElement, element_id)
    if not item: raise HTTPException(404, "Architecture element not found")
    _model(db, current_user, item.model_id, mutable=True)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    _commit(db, current_user, item, "architecture_element.updated"); return item


@router.delete("/elements/{element_id}", status_code=204)
def delete_element(element_id: int, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = db.get(ArchitectureElement, element_id)
    if not item: raise HTTPException(404, "Architecture element not found")
    _model(db, current_user, item.model_id, mutable=True); db.delete(item); db.commit(); AuditService(db).record(current_user.organization_id, "architecture_element.deleted", "ArchitectureElement", str(element_id), current_user.id)


@router.post("/models/{model_id}/relationships", response_model=RelationshipRead, status_code=201)
def create_relationship(model_id: int, payload: RelationshipCreate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    _model(db, current_user, model_id, mutable=True)
    endpoints = db.scalars(select(ArchitectureElement).where(ArchitectureElement.id.in_([payload.source_element_id, payload.target_element_id]), ArchitectureElement.model_id == model_id)).all()
    if len({e.id for e in endpoints}) != len({payload.source_element_id, payload.target_element_id}): raise HTTPException(400, "Relationship endpoints must belong to the model")
    item = ArchitectureRelationship(model_id=model_id, **payload.model_dump()); _commit(db, current_user, item, "architecture_relationship.created"); return item


@router.put("/relationships/{relationship_id}", response_model=RelationshipRead)
def update_relationship(relationship_id: int, payload: RelationshipUpdate, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = db.get(ArchitectureRelationship, relationship_id)
    if not item: raise HTTPException(404, "Architecture relationship not found")
    _model(db, current_user, item.model_id, mutable=True)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    _commit(db, current_user, item, "architecture_relationship.updated"); return item


@router.delete("/relationships/{relationship_id}", status_code=204)
def delete_relationship(relationship_id: int, current_user: CurrentUser = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)):
    item = db.get(ArchitectureRelationship, relationship_id)
    if not item: raise HTTPException(404, "Architecture relationship not found")
    _model(db, current_user, item.model_id, mutable=True); db.delete(item); db.commit(); AuditService(db).record(current_user.organization_id, "architecture_relationship.deleted", "ArchitectureRelationship", str(relationship_id), current_user.id)
