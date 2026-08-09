"""23-P3: Config Visualizer -- persistencia opcional de configs parseadas."""

from __future__ import annotations

import json

from app.db.models.device import Device
from app.db.models.integration import Integration
from app.db.models.organization import Organization

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _device(db, org_id, suffix="1"):
    integration = Integration(
        organization_id=org_id,
        connector_type="snmp",
        name=f"Integracion config {suffix}",
        base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()
    device = Device(
        integration_id=integration.id,
        hostname=f"sw-config-{suffix}",
        status="active",
    )
    db.add(device)
    db.commit()
    return device


def test_admin_guarda_configuracion_parseada_y_la_lista(
    db, http_client, admin_token, seed_data
):
    org_id = seed_data["org"].id
    device = _device(db, org_id, "guardar")

    parsed = {"vendor": "cisco_ios", "interfaces": [{"name": "Gi0/1"}], "warnings": []}
    created = http_client.post(
        f"{API}/device-configs/",
        headers=_auth(admin_token),
        json={
            "device_id": device.id,
            "vendor_detected": "cisco_ios",
            "parsed_json": json.dumps(parsed),
            "parse_warnings": None,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["vendor_detected"] == "cisco_ios"
    assert body["has_raw_config"] is False

    listed = http_client.get(
        f"{API}/device-configs/?device_id={device.id}", headers=_auth(admin_token)
    )
    assert listed.status_code == 200, listed.text
    assert any(c["id"] == body["id"] for c in listed.json())


def test_vendor_no_soportado_es_rechazado(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    device = _device(db, org_id, "rechazo")

    response = http_client.post(
        f"{API}/device-configs/",
        headers=_auth(admin_token),
        json={
            "device_id": device.id,
            "vendor_detected": "mikrotik",
            "parsed_json": "{}",
        },
    )
    assert response.status_code == 400
    assert "no soportado" in response.text.lower()


def test_configuracion_de_dispositivo_de_otra_organizacion_no_es_visible(
    db, http_client, admin_token, seed_data
):
    other_org = Organization(name="Tenant configs ajeno", slug="tenant-configs-ajeno")
    db.add(other_org)
    db.flush()
    other_device = _device(db, other_org.id, "otra-org")

    denied_create = http_client.post(
        f"{API}/device-configs/",
        headers=_auth(admin_token),
        json={
            "device_id": other_device.id,
            "vendor_detected": "cisco_ios",
            "parsed_json": "{}",
        },
    )
    assert denied_create.status_code == 404

    denied_list = http_client.get(
        f"{API}/device-configs/?device_id={other_device.id}", headers=_auth(admin_token)
    )
    assert denied_list.status_code == 404


def test_raw_config_no_se_expone_por_defecto(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    device = _device(db, org_id, "raw")

    created = http_client.post(
        f"{API}/device-configs/",
        headers=_auth(admin_token),
        json={
            "device_id": device.id,
            "vendor_detected": "cisco_ios",
            "parsed_json": "{}",
            "raw_config": "hostname SECRET-DEVICE\nenable secret 5 $1$abcd",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_raw_config"] is True
    assert "raw_config" not in body
    assert "SECRET-DEVICE" not in json.dumps(body)
