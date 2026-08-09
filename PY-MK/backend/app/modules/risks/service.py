from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.device import Device
from app.db.models.risk import Risk, RiskAsset
from app.modules.audit.services.audit_service import AuditService
from app.modules.risks.schemas import RiskAssetCreate, RiskAssetUpdate, RiskCreate, RiskUpdate


class RiskService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.audit = AuditService(db)

    def _client(self, client_id: int) -> Client:
        client = self.db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == self.current_user.organization_id))
        if not client:
            raise HTTPException(404, "Cliente no encontrado")
        return client

    def _asset(self, asset_id: int) -> RiskAsset:
        asset = self.db.scalar(select(RiskAsset).join(Client).where(RiskAsset.id == asset_id, Client.organization_id == self.current_user.organization_id))
        if not asset:
            raise HTTPException(404, "Activo de riesgo no encontrado")
        return asset

    def _risk(self, risk_id: int) -> Risk:
        risk = self.db.scalar(select(Risk).join(Client).where(Risk.id == risk_id, Client.organization_id == self.current_user.organization_id))
        if not risk:
            raise HTTPException(404, "Riesgo no encontrado")
        return risk

    def _validate_device(self, device_id: int | None, client_id: int) -> None:
        if device_id is None:
            return
        device = self.db.scalar(select(Device).join(Device.integration).where(Device.id == device_id))
        if not device or device.integration.client_id != client_id or device.integration.organization_id != self.current_user.organization_id:
            raise HTTPException(404, "Dispositivo no encontrado")

    @staticmethod
    def _scores(data: dict, current: Risk | None = None) -> tuple[int, int | None]:
        likelihood = data.get("likelihood", current.likelihood if current else None)
        impact = data.get("impact", current.impact if current else None)
        inherent = likelihood * impact
        rl = data.get("residual_likelihood", current.residual_likelihood if current else None)
        ri = data.get("residual_impact", current.residual_impact if current else None)
        supplied = data.get("residual_score", current.residual_score if current else None)
        residual = rl * ri if rl is not None and ri is not None else supplied
        if residual is not None and residual > inherent:
            raise HTTPException(422, "El score residual no puede superar el score inherente")
        return inherent, residual

    def list_assets(self, client_id: int | None = None) -> list[RiskAsset]:
        stmt = select(RiskAsset).join(Client).where(Client.organization_id == self.current_user.organization_id)
        if client_id is not None:
            self._client(client_id)
            stmt = stmt.where(RiskAsset.client_id == client_id)
        return list(self.db.scalars(stmt.order_by(RiskAsset.id)).all())

    def create_asset(self, payload: RiskAssetCreate) -> RiskAsset:
        self._client(payload.client_id); self._validate_device(payload.device_id, payload.client_id)
        data = payload.model_dump(); data["business_value"] = max(data["confidentiality"], data["integrity"], data["availability"])
        asset = RiskAsset(**data); self.db.add(asset); self.db.commit(); self.db.refresh(asset)
        self.audit.record(self.current_user.organization_id, "risk_asset.created", "risk_assets", str(asset.id), self.current_user.id)
        return asset

    def update_asset(self, asset_id: int, payload: RiskAssetUpdate) -> RiskAsset:
        asset = self._asset(asset_id); data = payload.model_dump(exclude_unset=True)
        self._validate_device(data.get("device_id", asset.device_id), asset.client_id)
        for key, value in data.items(): setattr(asset, key, value)
        asset.business_value = max(asset.confidentiality, asset.integrity, asset.availability)
        self.db.commit(); self.db.refresh(asset)
        self.audit.record(self.current_user.organization_id, "risk_asset.updated", "risk_assets", str(asset.id), self.current_user.id)
        return asset

    def delete_asset(self, asset_id: int) -> None:
        asset = self._asset(asset_id); self.db.delete(asset); self.db.commit()
        self.audit.record(self.current_user.organization_id, "risk_asset.deleted", "risk_assets", str(asset_id), self.current_user.id)

    def list_risks(self, client_id: int | None = None) -> list[Risk]:
        stmt = select(Risk).join(Client).where(Client.organization_id == self.current_user.organization_id)
        if client_id is not None:
            self._client(client_id); stmt = stmt.where(Risk.client_id == client_id)
        return list(self.db.scalars(stmt.order_by(Risk.id)).all())

    def get_risk(self, risk_id: int) -> Risk: return self._risk(risk_id)

    def create_risk(self, payload: RiskCreate) -> Risk:
        self._client(payload.client_id); asset = self._asset(payload.asset_id)
        if asset.client_id != payload.client_id: raise HTTPException(422, "El activo no pertenece al cliente")
        data = payload.model_dump(); data["inherent_score"], data["residual_score"] = self._scores(data)
        risk = Risk(**data); self.db.add(risk); self.db.commit(); self.db.refresh(risk)
        self.audit.record(self.current_user.organization_id, "risk.created", "risks", str(risk.id), self.current_user.id)
        return risk

    def update_risk(self, risk_id: int, payload: RiskUpdate) -> Risk:
        risk = self._risk(risk_id); data = payload.model_dump(exclude_unset=True)
        asset = self._asset(data.get("asset_id", risk.asset_id))
        if asset.client_id != risk.client_id: raise HTTPException(422, "El activo no pertenece al cliente")
        data["inherent_score"], data["residual_score"] = self._scores(data, risk)
        for key, value in data.items(): setattr(risk, key, value)
        self.db.commit(); self.db.refresh(risk)
        self.audit.record(self.current_user.organization_id, "risk.updated", "risks", str(risk.id), self.current_user.id)
        return risk

    def delete_risk(self, risk_id: int) -> None:
        risk = self._risk(risk_id); self.db.delete(risk); self.db.commit()
        self.audit.record(self.current_user.organization_id, "risk.deleted", "risks", str(risk_id), self.current_user.id)
