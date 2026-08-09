from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.device_config import DeviceConfig
from app.db.models.integration import Integration
from app.modules.audit.services.audit_service import AuditService
from app.modules.devices.schemas import DeviceConfigCreate

SUPPORTED_VENDORS = {"cisco_ios"}


class DeviceConfigService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self._audit = AuditService(db)

    def _device_or_404(self, device_id: int) -> Device:
        device = self.db.get(Device, device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        integration = (
            self.db.get(Integration, device.integration_id) if device.integration_id else None
        )
        site = self.db.get(ClientSite, device.site_id) if device.site_id else None
        org_allowed = False
        if integration and integration.organization_id == self.current_user.organization_id:
            org_allowed = True
        elif site and site.client and site.client.organization_id == self.current_user.organization_id:
            org_allowed = True
        if not org_allowed:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        return device

    def list_for_device(self, device_id: int) -> list[DeviceConfig]:
        self._device_or_404(device_id)
        return list(
            self.db.scalars(
                select(DeviceConfig)
                .where(DeviceConfig.device_id == device_id)
                .order_by(DeviceConfig.uploaded_at.desc())
            ).all()
        )

    def create(self, payload: DeviceConfigCreate) -> DeviceConfig:
        self._device_or_404(payload.device_id)

        if payload.vendor_detected not in SUPPORTED_VENDORS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Vendor '{payload.vendor_detected}' no soportado por el parser. "
                    f"Soportados: {', '.join(sorted(SUPPORTED_VENDORS))}"
                ),
            )

        config = DeviceConfig(
            device_id=payload.device_id,
            vendor_detected=payload.vendor_detected,
            raw_config=payload.raw_config,
            parsed_json=payload.parsed_json,
            parse_warnings=payload.parse_warnings,
            uploaded_by=self.current_user.id,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        self._audit.record(
            self.current_user.organization_id,
            "device_config.uploaded",
            "device_configs",
            str(config.id),
            self.current_user.id,
            metadata_json=f'{{"device_id":{config.device_id},"vendor":"{config.vendor_detected}"}}',
        )
        return config
