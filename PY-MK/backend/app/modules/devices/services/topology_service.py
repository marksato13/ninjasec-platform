from __future__ import annotations

import ipaddress
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.device_connection import DeviceConnection
from app.db.models.enums import RoleCode
from app.db.models.integration import Integration
from app.db.models.user import User
from app.modules.devices.schemas import (
    CandidateConnection,
    DeduceConnectionsRequest,
    TopologyCluster,
    TopologyEdge,
    TopologyNode,
    TopologyResponse,
)


def equipos_del_cliente(client_id: int, organization_id: int):
    """Equipos de un cliente: por su integracion o por su sede.

    Los registrados a mano no tienen integracion (y con la capsula de
    telemetria apagada no hay ninguna): cuelgan de una sede del cliente.
    La misma regla que usa DeviceService.list, para que el inventario y la
    topologia cuenten los mismos equipos.
    """
    return (
        select(Device)
        .outerjoin(Integration, Device.integration_id == Integration.id)
        .outerjoin(ClientSite, Device.site_id == ClientSite.id)
        .where(
            or_(
                and_(Integration.client_id == client_id, Integration.organization_id == organization_id),
                and_(ClientSite.client_id == client_id, ClientSite.client.has(organization_id=organization_id)),
            )
        )
    )


class TopologyService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def build(self, client_id: int) -> TopologyResponse:
        client = self.db.get(Client, client_id)
        if not client or client.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Client not found")

        is_client = self.current_user.role == RoleCode.CLIENT.value
        if is_client:
            profile = self.db.scalar(
                select(ClientProfile).where(ClientProfile.user_id == self.current_user.id)
            )
            if not profile or profile.client_id != client_id:
                raise HTTPException(status_code=404, detail="Client not found")

        devices = list(self.db.scalars(
            equipos_del_cliente(client_id, self.current_user.organization_id)
            .options(selectinload(Device.responsible_user))
        ).unique().all())

        device_ids = [d.id for d in devices]
        nodes: list[TopologyNode] = []
        for d in devices:
            owner_name: str | None = None
            if d.responsible_user_id:
                user = self.db.get(User, d.responsible_user_id)
                owner_name = user.full_name if user else None
            nodes.append(TopologyNode(
                id=d.id,
                label=d.hostname,
                device_type=d.device_type,
                vendor=d.vendor,
                model=d.model,
                ip_address=None if is_client else d.ip_address,
                status=d.status,
                criticality=d.criticality,
                data_classification=d.data_classification,
                site_id=d.site_id,
                responsible_user_id=d.responsible_user_id,
                responsible_user_name=owner_name,
                integration_id=d.integration_id,
            ))

        edges: list[TopologyEdge] = []
        if device_ids:
            conns = self.db.scalars(
                select(DeviceConnection).where(
                    DeviceConnection.source_device_id.in_(device_ids),
                    DeviceConnection.target_device_id.in_(device_ids),
                )
            ).all()
            for c in conns:
                edges.append(TopologyEdge(
                    id=c.id,
                    source=c.source_device_id,
                    target=c.target_device_id,
                    link_type=c.link_type,
                    port_source=None if is_client else c.port_source,
                    port_target=None if is_client else c.port_target,
                    vlan_id=c.vlan_id,
                    bandwidth_mbps=c.bandwidth_mbps,
                ))

        # Cluster por sede
        by_site: dict[int | None, list[int]] = defaultdict(list)
        for d in devices:
            by_site[d.site_id].append(d.id)
        sites = {
            s.id: s for s in self.db.scalars(
                select(ClientSite).where(ClientSite.client_id == client_id)
            ).all()
        }
        clusters: list[TopologyCluster] = []
        for site_id, node_ids in by_site.items():
            if site_id is None:
                clusters.append(TopologyCluster(label="Sin sede asignada", site_id=None, node_ids=node_ids))
            else:
                site = sites.get(site_id)
                label = site.name if site else f"Sede #{site_id}"
                clusters.append(TopologyCluster(label=label, site_id=site_id, node_ids=node_ids))

        return TopologyResponse(
            client_id=client.id,
            client_name=client.company_name,
            nodes=nodes,
            edges=edges,
            clusters=clusters,
        )

    def deduce_connections(self, device_id: int, payload: DeduceConnectionsRequest) -> list[CandidateConnection]:
        """23-P4: propone `device_connections` a partir de lo que el parser extrajo
        de un running-config, cruzando contra los demás dispositivos del mismo
        cliente. El parser no extrae vecinos (no hay CDP/LLDP) -- se usan dos
        heurísticas honestas, ambas documentadas en la respuesta vía `reason`:

        1. Misma subred: la IP de un dispositivo hermano cae dentro de la red
           de una interfaz local con IP configurada.
        2. Next-hop de ruta estática: el next-hop coincide exactamente con la
           IP de un dispositivo hermano.

        Es una propuesta para revisión humana, no una verdad de topología --
        el endpoint que la aplica (`POST /device-connections`) exige
        confirmación explícita por cada candidato.
        """
        source = self.db.get(Device, device_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        integration = self.db.get(Integration, source.integration_id) if source.integration_id else None
        if not integration or integration.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        siblings = list(self.db.scalars(
            select(Device)
            .join(Integration, Device.integration_id == Integration.id)
            .where(
                Integration.client_id == integration.client_id,
                Integration.organization_id == self.current_user.organization_id,
                Device.id != device_id,
                Device.ip_address.is_not(None),
            )
        ).all())

        candidates: dict[int, CandidateConnection] = {}

        for iface in payload.interfaces:
            if not iface.ip_address or not iface.subnet_mask:
                continue
            try:
                network = ipaddress.ip_network(f"{iface.ip_address}/{iface.subnet_mask}", strict=False)
            except ValueError:
                continue
            for sibling in siblings:
                if sibling.id in candidates or not sibling.ip_address:
                    continue
                try:
                    sibling_ip = ipaddress.ip_address(sibling.ip_address)
                except ValueError:
                    continue
                if sibling_ip in network:
                    candidates[sibling.id] = CandidateConnection(
                        target_device_id=sibling.id,
                        target_hostname=sibling.hostname,
                        reason=f"{iface.name} ({iface.ip_address}/{iface.subnet_mask}) está en la misma subred que {sibling.hostname} ({sibling.ip_address})",
                        source_ip=iface.ip_address,
                        target_ip=sibling.ip_address,
                    )

        for route in payload.static_routes:
            try:
                next_hop = ipaddress.ip_address(route.next_hop)
            except ValueError:
                continue
            for sibling in siblings:
                if sibling.id in candidates or not sibling.ip_address:
                    continue
                if sibling.ip_address == str(next_hop):
                    candidates[sibling.id] = CandidateConnection(
                        target_device_id=sibling.id,
                        target_hostname=sibling.hostname,
                        reason=f"Ruta estática {route.destination}/{route.mask} apunta a {sibling.hostname} ({sibling.ip_address}) como next-hop",
                        source_ip=None,
                        target_ip=sibling.ip_address,
                    )

        return list(candidates.values())
