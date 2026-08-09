"""30-P1: conector Wazuh y esquema normalizado común (ECS-lite) entre fuentes.

Antes de este cambio, pfSense y FortiGate tenían normalized_payload con
formatos completamente distintos, sin ninguna clave en común -- imposible
correlacionar eventos entre fuentes. Estas pruebas fijan el contrato: las
tres fuentes devuelven `{"events": [...]}`, y cada evento trae
event.category, event.severity, source.ip y rule.description.
"""

import json

from sqlalchemy import select

from app.db.models.client import Client
from app.db.models.integration import Integration

API = "/api/v1"
ECS_CONNECTORS = ["pfSense", "FortiGate", "Wazuh"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _assert_ecs_shape(normalized_payload_json: str):
    payload = json.loads(normalized_payload_json)
    assert "events" in payload
    assert len(payload["events"]) >= 1
    for event in payload["events"]:
        assert "@timestamp" in event
        assert set(event["event"].keys()) == {"category", "severity"}
        assert "ip" in event["source"]
        assert "description" in event["rule"]


def test_wazuh_connector_test_connection_es_alcanzable(http_client, admin_token):
    response = http_client.post(
        f"{API}/integrations/test-connection",
        headers=_auth(admin_token),
        json={"connector_type": "wazuh", "base_url": "https://wazuh.example.test"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["reachable"] is True


def test_conector_no_soportado_no_es_alcanzable(http_client, admin_token):
    response = http_client.post(
        f"{API}/integrations/test-connection",
        headers=_auth(admin_token),
        json={"connector_type": "cisco-ise", "base_url": "https://ise.example.test"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["reachable"] is False


def test_las_tres_fuentes_comparten_el_mismo_esquema_normalizado(db, http_client, admin_token, seed_data):
    from app.db.models.collection_snapshot import CollectionSnapshot

    client = Client(organization_id=seed_data["org"].id, company_name="Cliente conectores ECS")
    db.add(client)
    db.commit()

    for connector_type in ECS_CONNECTORS:
        integration = Integration(
            organization_id=seed_data["org"].id,
            client_id=client.id,
            connector_type=connector_type,
            name=f"Integracion {connector_type}",
            base_url=f"https://{connector_type.lower()}.example.test",
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)

        response = http_client.post(f"{API}/integrations/{integration.id}/collect", headers=_auth(admin_token))
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "connected"

        snapshots = list(db.scalars(select(CollectionSnapshot).where(CollectionSnapshot.integration_id == integration.id)))
        assert len(snapshots) >= 1
        _assert_ecs_shape(snapshots[0].normalized_payload)


def test_wazuh_genera_dispositivo_y_eventos_de_severidad_critica(db, http_client, admin_token, seed_data):
    from app.db.models.collection_snapshot import CollectionSnapshot
    from app.db.models.device import Device

    client = Client(organization_id=seed_data["org"].id, company_name="Cliente Wazuh")
    db.add(client)
    db.commit()

    integration = Integration(
        organization_id=seed_data["org"].id,
        client_id=client.id,
        connector_type="wazuh",
        name="Wazuh Manager",
        base_url="https://wazuh.example.test",
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)

    response = http_client.post(f"{API}/integrations/{integration.id}/collect", headers=_auth(admin_token))
    assert response.status_code == 200, response.text

    device = db.scalar(select(Device).where(Device.integration_id == integration.id, Device.hostname == "wazuh-manager"))
    assert device is not None
    assert device.vendor == "Wazuh"

    snapshot = db.scalar(select(CollectionSnapshot).where(CollectionSnapshot.integration_id == integration.id))
    payload = json.loads(snapshot.normalized_payload)
    severities = {event["event"]["severity"] for event in payload["events"]}
    assert "critical" in severities
