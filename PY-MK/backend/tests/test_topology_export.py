"""23-P4: deducción de device_connections desde un parseo y exportación PDF."""

from __future__ import annotations

from app.db.models.client import Client
from app.db.models.device import Device
from app.db.models.integration import Integration
from app.db.models.organization import Organization

API = "/api/v1"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _client_with_devices(db, organization_id: int, suffix: str):
    client = Client(organization_id=organization_id, company_name=f"Cliente export {suffix}")
    db.add(client)
    db.flush()

    integration = Integration(
        organization_id=organization_id,
        client_id=client.id,
        connector_type="manual",
        name=f"Integracion export {suffix}",
        base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()

    router = Device(
        integration_id=integration.id, hostname=f"rtr-{suffix}",
        device_type="router", ip_address="10.10.0.1", status="online",
    )
    same_subnet = Device(
        integration_id=integration.id, hostname=f"sw-{suffix}",
        device_type="switch", ip_address="10.10.0.5", status="online",
    )
    next_hop_target = Device(
        integration_id=integration.id, hostname=f"fw-{suffix}",
        device_type="firewall", ip_address="192.168.99.1", status="online",
    )
    unrelated = Device(
        integration_id=integration.id, hostname=f"ap-{suffix}",
        device_type="ap", ip_address="172.16.5.5", status="online",
    )
    db.add_all([router, same_subnet, next_hop_target, unrelated])
    db.commit()
    return client, router, same_subnet, next_hop_target, unrelated


def test_deducir_conexiones_detecta_misma_subred_y_next_hop(db, http_client, admin_token, seed_data):
    _, router, same_subnet, next_hop_target, unrelated = _client_with_devices(db, seed_data["org"].id, "subred")

    response = http_client.post(
        f"{API}/devices/{router.id}/topology/deduce-connections",
        headers=_auth(admin_token),
        json={
            "interfaces": [{"name": "Gi0/0", "ip_address": "10.10.0.1", "subnet_mask": "255.255.255.0"}],
            "static_routes": [{"destination": "0.0.0.0", "mask": "0.0.0.0", "next_hop": "192.168.99.1"}],
        },
    )
    assert response.status_code == 200, response.text
    candidates = {c["target_device_id"]: c for c in response.json()}

    assert same_subnet.id in candidates
    assert "misma subred" in candidates[same_subnet.id]["reason"]
    assert next_hop_target.id in candidates
    assert "next-hop" in candidates[next_hop_target.id]["reason"]
    assert unrelated.id not in candidates


def test_deducir_conexiones_sin_coincidencias_devuelve_lista_vacia(db, http_client, admin_token, seed_data):
    _, router, *_ = _client_with_devices(db, seed_data["org"].id, "sinmatch")

    response = http_client.post(
        f"{API}/devices/{router.id}/topology/deduce-connections",
        headers=_auth(admin_token),
        json={"interfaces": [{"name": "Gi0/0", "ip_address": "203.0.113.1", "subnet_mask": "255.255.255.252"}], "static_routes": []},
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_deducir_conexiones_rechaza_dispositivo_de_otra_organizacion(db, http_client, admin_token, seed_data):
    foreign_org = Organization(name="Organizacion Deduce Ajena", slug="deduce-ajena")
    db.add(foreign_org)
    db.commit()
    _, foreign_router, *_ = _client_with_devices(db, foreign_org.id, "ajeno")

    response = http_client.post(
        f"{API}/devices/{foreign_router.id}/topology/deduce-connections",
        headers=_auth(admin_token),
        json={"interfaces": [], "static_routes": []},
    )
    assert response.status_code == 404


def test_deducir_conexiones_ignora_ip_o_mascara_invalida_sin_romper(db, http_client, admin_token, seed_data):
    _, router, *_ = _client_with_devices(db, seed_data["org"].id, "invalido")

    response = http_client.post(
        f"{API}/devices/{router.id}/topology/deduce-connections",
        headers=_auth(admin_token),
        json={
            "interfaces": [{"name": "Gi0/1", "ip_address": "no-es-una-ip", "subnet_mask": "255.255.255.0"}],
            "static_routes": [{"destination": "0.0.0.0", "mask": "0.0.0.0", "next_hop": "tampoco-es-ip"}],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_exportar_topologia_pdf_genera_documento_valido(db, http_client, admin_token, seed_data):
    client, *_ = _client_with_devices(db, seed_data["org"].id, "pdf")

    response = http_client.get(f"{API}/devices/topology/export/pdf?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 500
