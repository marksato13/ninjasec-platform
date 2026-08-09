"""18-P-04: alerta inmediata de dispositivo crítico caído."""

from app.db.models.device import Device
from app.db.models.integration import Integration

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _integration(db, org_id):
    integration = Integration(
        organization_id=org_id,
        connector_type="pfsense",
        name="Consola de prueba",
        base_url="https://pfsense.local",
    )
    db.add(integration)
    db.flush()
    return integration


def test_dispositivo_critico_offline_genera_alerta_inmediata(
    db, http_client, admin_token, seed_data
):
    integration = _integration(db, seed_data["org"].id)
    device = Device(
        integration_id=integration.id,
        hostname="fw-critico-01",
        status="offline",
        criticality="critical",
    )
    db.add(device)
    db.commit()

    response = http_client.get(f"{API}/alerts/active", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    alerts = response.json()

    match = next(
        (a for a in alerts if a["type"] == "critical_device_offline" and a["entity_id"] == device.id),
        None,
    )
    assert match is not None
    assert match["severity"] == "critical"
    assert match["entity_type"] == "device"
    assert alerts[0]["severity"] == "critical"


def test_dispositivo_no_critico_offline_no_dispara_la_alerta_especial(
    db, http_client, admin_token, seed_data
):
    integration = _integration(db, seed_data["org"].id)
    device = Device(
        integration_id=integration.id,
        hostname="ap-no-critico",
        status="offline",
        criticality="low",
    )
    db.add(device)
    db.commit()

    response = http_client.get(f"{API}/alerts/active", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    alerts = response.json()

    assert not any(
        a["type"] == "critical_device_offline" and a["entity_id"] == device.id
        for a in alerts
    )


def test_dispositivo_critico_online_no_dispara_alerta(
    db, http_client, admin_token, seed_data
):
    integration = _integration(db, seed_data["org"].id)
    device = Device(
        integration_id=integration.id,
        hostname="fw-critico-online",
        status="active",
        criticality="critical",
    )
    db.add(device)
    db.commit()

    response = http_client.get(f"{API}/alerts/active", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    alerts = response.json()

    assert not any(
        a["type"] == "critical_device_offline" and a["entity_id"] == device.id
        for a in alerts
    )
