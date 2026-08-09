from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.db.models.risk import Threat, Vulnerability
from app.modules.risks.schemas import (
    CatalogEntryCreate,
    CatalogEntryRead,
    HeatmapCell,
    RiskAssetCreate,
    RiskAssetRead,
    RiskAssetUpdate,
    RiskAssociationsUpdate,
    RiskCreate,
    RiskRead,
    RiskUpdate,
)
from app.modules.risks.service import RiskService

router = APIRouter(prefix="/risks", tags=["risks"])
ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.COLLABORATOR.value)


@router.get("/assets", response_model=list[RiskAssetRead])
def list_assets(client_id: int | None = None, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).list_assets(client_id)


@router.post("/assets", response_model=RiskAssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(payload: RiskAssetCreate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).create_asset(payload)


@router.put("/assets/{asset_id}", response_model=RiskAssetRead)
def update_asset(asset_id: int, payload: RiskAssetUpdate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).update_asset(asset_id, payload)


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    RiskService(db, user).delete_asset(asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/threats", response_model=list[CatalogEntryRead])
def list_threats(user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).list_catalog(Threat)


@router.post("/threats", response_model=CatalogEntryRead, status_code=status.HTTP_201_CREATED)
def create_threat(payload: CatalogEntryCreate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).create_catalog_entry(Threat, payload)


@router.get("/vulnerabilities", response_model=list[CatalogEntryRead])
def list_vulnerabilities(user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).list_catalog(Vulnerability)


@router.post("/vulnerabilities", response_model=CatalogEntryRead, status_code=status.HTTP_201_CREATED)
def create_vulnerability(payload: CatalogEntryCreate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).create_catalog_entry(Vulnerability, payload)


@router.get("/heatmap", response_model=list[HeatmapCell])
def heatmap(client_id: int | None = None, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).heatmap(client_id)


@router.get("/", response_model=list[RiskRead])
def list_risks(client_id: int | None = None, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).list_risks(client_id)


@router.get("/{risk_id}", response_model=RiskRead)
def get_risk(risk_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).get_risk(risk_id)


@router.post("/", response_model=RiskRead, status_code=status.HTTP_201_CREATED)
def create_risk(payload: RiskCreate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).create_risk(payload)


@router.put("/{risk_id}", response_model=RiskRead)
def update_risk(risk_id: int, payload: RiskUpdate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).update_risk(risk_id, payload)


@router.put("/{risk_id}/associations", response_model=RiskRead)
def update_risk_associations(risk_id: int, payload: RiskAssociationsUpdate, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    return RiskService(db, user).update_associations(risk_id, payload)


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(risk_id: int, user: CurrentUser = Depends(require_roles(*ROLES)), db: Session = Depends(get_db)):
    RiskService(db, user).delete_risk(risk_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
