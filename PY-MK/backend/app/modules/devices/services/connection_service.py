from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.device_connection import DeviceConnection
from app.db.models.integration import Integration
from app.modules.audit.services.audit_service import AuditService
from app.modules.devices.schemas import DeviceConnectionCreate


class DeviceConnectionService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self._audit = AuditService(db)

    def _device_or_404(self, device_id: int) -> Device:
        """Devuelve el dispositivo solo si pertenece a la organizacion.

        Parte de `permitido = False` y exige una ruta explicita, en vez de
        permitir por defecto y buscar motivos para negar.

        La version anterior era `if integration and integration.organization_id
        != org: 404`. Con `devices.integration_id` nullable desde la migracion
        20260522_01, un equipo sin integracion hacia que la condicion fuera
        falsa y se devolviera el dispositivo **de cualquier organizacion**.
        Eso permitia crear conexiones de topologia cruzadas entre tenants.
        """
        device = self.db.get(Device, device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        org_id = self.current_user.organization_id
        integration = (
            self.db.get(Integration, device.integration_id) if device.integration_id else None
        )
        site = self.db.get(ClientSite, device.site_id) if device.site_id else None

        permitido = False
        if integration and integration.organization_id == org_id:
            permitido = True
        elif site and site.client and site.client.organization_id == org_id:
            permitido = True

        if not permitido:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        return device

    def list_for_client(self, client_id: int) -> list[DeviceConnection]:
        from app.modules.devices.services.topology_service import equipos_del_cliente

        device_ids = [
            d.id for d in self.db.scalars(
                equipos_del_cliente(client_id, self.current_user.organization_id)
            ).unique().all()
        ]
        if not device_ids:
            return []
        return list(self.db.scalars(
            select(DeviceConnection).where(
                DeviceConnection.source_device_id.in_(device_ids),
                DeviceConnection.target_device_id.in_(device_ids),
            )
        ).all())

    def create(self, payload: DeviceConnectionCreate) -> DeviceConnection:
        if payload.source_device_id == payload.target_device_id:
            raise HTTPException(status_code=400, detail="source and target must be different devices")

        self._device_or_404(payload.source_device_id)
        self._device_or_404(payload.target_device_id)

        # 23-P2: una conexión duplicada (mismo origen/destino/tipo) se
        # rechaza con un mensaje claro -- antes se devolvía la existente en
        # silencio, lo que en la UI se veía indistinguible de un éxito real.
        existing = self.db.scalar(
            select(DeviceConnection).where(
                DeviceConnection.source_device_id == payload.source_device_id,
                DeviceConnection.target_device_id == payload.target_device_id,
                DeviceConnection.link_type == payload.link_type,
            )
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Ya existe una conexión de este tipo entre estos dos dispositivos",
            )

        conn = DeviceConnection(**payload.model_dump())
        self.db.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        self._audit.record(
            self.current_user.organization_id,
            "device_connection.created",
            "device_connections",
            str(conn.id),
            self.current_user.id,
        )
        return conn

    def delete(self, connection_id: int) -> None:
        conn = self.db.get(DeviceConnection, connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")

        self._device_or_404(conn.source_device_id)

        self.db.delete(conn)
        self.db.commit()
        self._audit.record(
            self.current_user.organization_id,
            "device_connection.deleted",
            "device_connections",
            str(connection_id),
            self.current_user.id,
        )
