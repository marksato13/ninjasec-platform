"""Pruebas aisladas del contrato de topologia (23-P1).

El diagrama se alimenta exclusivamente de este contrato. Estas pruebas fijan
las transformaciones que consume la UI y, sobre todo, su frontera de tenant y
la vista degradada del portal cliente.
"""

from __future__ import annotations

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.device_connection import DeviceConnection
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _topology_data(db, organization_id: int, prefix: str = "Principal"):
    client = Client(organization_id=organization_id, company_name=f"Cliente {prefix}")
    db.add(client)
    db.flush()

    central = ClientSite(client_id=client.id, name=f"Sede {prefix}")
    db.add(central)
    db.flush()

    integration = Integration(
        organization_id=organization_id,
        client_id=client.id,
        connector_type="snmp",
        name=f"Integracion {prefix}",
        base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()

    firewall = Device(
        integration_id=integration.id,
        site_id=central.id,
        hostname=f"fw-{prefix}",
        device_type="firewall",
        vendor="Fortinet",
        model="FG-60F",
        ip_address="192.168.1.1",
        status="online",
        criticality="critical",
    )
    switch = Device(
        integration_id=integration.id,
        site_id=central.id,
        hostname=f"sw-{prefix}",
        device_type="switch",
        vendor="Cisco",
        model="CBS350",
        ip_address="192.168.1.2",
        status="online",
        criticality="high",
    )
    ap = Device(
        integration_id=integration.id,
        hostname=f"ap-{prefix}",
        device_type="access_point",
        ip_address="192.168.1.3",
        status="offline",
        criticality="low",
    )
    db.add_all([firewall, switch, ap])
    db.flush()
    db.add(DeviceConnection(
        source_device_id=firewall.id,
        target_device_id=switch.id,
        link_type="trunk",
        port_source="port1",
        port_target="Gi1/0/24",
        vlan_id=100,
        bandwidth_mbps=1000,
    ))
    db.commit()
    return client, central, firewall, switch, ap


def _client_token(db, http_client, organization_id: int, client_id: int, suffix: str):
    role = db.query(Role).filter(Role.code == RoleCode.CLIENT.value).first()
    if role is None:
        role = Role(code=RoleCode.CLIENT.value, name="Client")
        db.add(role)
        db.flush()
    user = User(
        organization_id=organization_id,
        role_id=role.id,
        full_name=f"Portal {suffix}",
        email=f"portal-{suffix}@ninjasec.local",
        password_hash=hash_password("client-password-123"),
        role_code=RoleCode.CLIENT,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(ClientProfile(client_id=client_id, user_id=user.id))
    db.commit()

    response = http_client.post(f"{API}/auth/login", json={
        "email": user.email,
        "password": "client-password-123",
    })
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_topology_transforms_devices_links_and_site_clusters(
    db, http_client, admin_token, seed_data
):
    client, site, firewall, switch, ap = _topology_data(db, seed_data["org"].id)

    response = http_client.get(
        f"{API}/devices/topology?client_id={client.id}", headers=_auth(admin_token)
    )
    assert response.status_code == 200, response.text
    topology = response.json()

    nodes = {node["id"]: node for node in topology["nodes"]}
    assert nodes[firewall.id] == {
        "id": firewall.id,
        "label": "fw-Principal",
        "device_type": "firewall",
        "vendor": "Fortinet",
        "model": "FG-60F",
        "ip_address": "192.168.1.1",
        "status": "online",
        "criticality": "critical",
        "data_classification": None,
        "site_id": site.id,
        "responsible_user_id": None,
        "responsible_user_name": None,
        "integration_id": firewall.integration_id,
    }
    assert nodes[switch.id]["device_type"] == "switch"
    assert nodes[ap.id]["criticality"] == "low"
    assert topology["edges"] == [{
        "id": topology["edges"][0]["id"], "source": firewall.id, "target": switch.id,
        "link_type": "trunk", "port_source": "port1", "port_target": "Gi1/0/24",
        "vlan_id": 100, "bandwidth_mbps": 1000,
    }]
    assert {cluster["label"]: set(cluster["node_ids"]) for cluster in topology["clusters"]} == {
        "Sede Principal": {firewall.id, switch.id},
        "Sin sede asignada": {ap.id},
    }


def test_topology_empty_state_has_no_nodes_edges_or_clusters(db, http_client, admin_token, seed_data):
    client = Client(organization_id=seed_data["org"].id, company_name="Cliente Vacio")
    db.add(client)
    db.commit()

    response = http_client.get(
        f"{API}/devices/topology?client_id={client.id}", headers=_auth(admin_token)
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "client_id": client.id, "client_name": "Cliente Vacio",
        "nodes": [], "edges": [], "clusters": [],
    }


def test_topology_rejects_client_from_another_organization(db, http_client, admin_token, seed_data):
    foreign_org = Organization(name="Organizacion Topologia Ajena", slug="topologia-ajena")
    db.add(foreign_org)
    db.commit()
    foreign_client, *_ = _topology_data(db, foreign_org.id, "Ajeno")

    response = http_client.get(
        f"{API}/devices/topology?client_id={foreign_client.id}", headers=_auth(admin_token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_client_topology_hides_ips_and_ports_and_cannot_select_other_client(
    db, http_client, seed_data
):
    own_client, _, firewall, switch, ap = _topology_data(db, seed_data["org"].id, "Portal")
    other_client, *_ = _topology_data(db, seed_data["org"].id, "Otro")
    token = _client_token(db, http_client, seed_data["org"].id, own_client.id, "topologia")

    response = http_client.get(
        f"{API}/devices/topology?client_id={own_client.id}", headers=_auth(token)
    )
    assert response.status_code == 200, response.text
    topology = response.json()
    assert {node["id"] for node in topology["nodes"]} == {firewall.id, switch.id, ap.id}
    assert all(node["ip_address"] is None for node in topology["nodes"])
    assert all(edge["port_source"] is None and edge["port_target"] is None for edge in topology["edges"])
    assert "192.168.1.1" not in response.text
    assert "Gi1/0/24" not in response.text

    forbidden = http_client.get(
        f"{API}/devices/topology?client_id={other_client.id}", headers=_auth(token)
    )
    assert forbidden.status_code == 404


def test_client_cannot_create_or_list_connections(db, http_client, seed_data):
    client, _, firewall, switch, _ = _topology_data(db, seed_data["org"].id, "SinEdicion")
    token = _client_token(db, http_client, seed_data["org"].id, client.id, "sin-edicion")

    listed = http_client.get(f"{API}/device-connections/?client_id={client.id}", headers=_auth(token))
    created = http_client.post(f"{API}/device-connections/", headers=_auth(token), json={
        "source_device_id": firewall.id,
        "target_device_id": switch.id,
        "link_type": "ethernet",
    })
    assert listed.status_code == 403
    assert created.status_code == 403
