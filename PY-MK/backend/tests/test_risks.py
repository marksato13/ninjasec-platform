"""25-P1: CRUD, cálculo de scores y vínculo opcional de activos de riesgo."""

from app.db.models.client import Client
from app.db.models.device import Device
from app.db.models.integration import Integration

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, organization_id, suffix):
    client = Client(
        organization_id=organization_id,
        company_name=f"Cliente riesgos {suffix}",
    )
    db.add(client)
    db.commit()
    return client


def _device(db, organization_id, client_id):
    integration = Integration(
        organization_id=organization_id,
        client_id=client_id,
        connector_type="manual",
        name="Inventario de prueba",
        base_url="https://inventory.example.test",
    )
    db.add(integration)
    db.flush()
    device = Device(integration_id=integration.id, hostname="srv-riesgos-01")
    db.add(device)
    db.commit()
    return device


def _asset_payload(client_id, **overrides):
    return {
        "client_id": client_id,
        "name": "Información de clientes",
        "asset_type": "information",
        "confidentiality": 5,
        "integrity": 4,
        "availability": 3,
        **overrides,
    }


def _risk_payload(client_id, asset_id, **overrides):
    return {
        "client_id": client_id,
        "asset_id": asset_id,
        "title": "Exposición de datos",
        "likelihood": 4,
        "impact": 5,
        **overrides,
    }


def test_crud_activos_admite_device_id_opcional_y_calcula_valor(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "activos")
    device = _device(db, seed_data["org"].id, client.id)

    intangible = http_client.post(
        f"{API}/risks/assets", headers=_auth(admin_token), json=_asset_payload(client.id)
    )
    assert intangible.status_code == 201, intangible.text
    asset = intangible.json()
    assert asset["device_id"] is None
    assert asset["business_value"] == 5

    linked = http_client.put(
        f"{API}/risks/assets/{asset['id']}",
        headers=_auth(admin_token),
        json={"device_id": device.id, "availability": 5},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["device_id"] == device.id
    assert linked.json()["business_value"] == 5

    unlinked = http_client.put(
        f"{API}/risks/assets/{asset['id']}",
        headers=_auth(admin_token), json={"device_id": None},
    )
    assert unlinked.status_code == 200, unlinked.text
    assert unlinked.json()["device_id"] is None

    listed = http_client.get(
        f"{API}/risks/assets?client_id={client.id}", headers=_auth(admin_token)
    )
    assert [item["id"] for item in listed.json()] == [asset["id"]]
    deleted = http_client.delete(
        f"{API}/risks/assets/{asset['id']}", headers=_auth(admin_token)
    )
    assert deleted.status_code == 204


def test_crud_riesgos_calcula_y_recalcula_score_inherente(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "scores")
    asset = http_client.post(
        f"{API}/risks/assets", headers=_auth(admin_token), json=_asset_payload(client.id)
    ).json()

    created = http_client.post(
        f"{API}/risks/",
        headers=_auth(admin_token),
        json=_risk_payload(
            client.id, asset["id"], inherent_score=1, residual_likelihood=2, residual_impact=3
        ),
    )
    assert created.status_code == 201, created.text
    risk = created.json()
    assert risk["inherent_score"] == 20
    assert risk["residual_score"] == 6

    updated = http_client.put(
        f"{API}/risks/{risk['id']}",
        headers=_auth(admin_token),
        json={
            "likelihood": 2,
            "impact": 3,
            "inherent_score": 25,
            "residual_likelihood": 1,
            "residual_impact": 2,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["inherent_score"] == 6
    assert updated.json()["residual_score"] == 2

    listed = http_client.get(
        f"{API}/risks/?client_id={client.id}", headers=_auth(admin_token)
    )
    assert [item["id"] for item in listed.json()] == [risk["id"]]
    assert http_client.get(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 200
    assert http_client.delete(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 204
    assert http_client.get(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 404


def test_score_residual_igual_o_menor_se_acepta_y_mayor_se_rechaza(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "residual")
    asset = http_client.post(
        f"{API}/risks/assets", headers=_auth(admin_token), json=_asset_payload(client.id)
    ).json()

    equal = http_client.post(
        f"{API}/risks/",
        headers=_auth(admin_token),
        json=_risk_payload(client.id, asset["id"], residual_score=20),
    )
    assert equal.status_code == 201, equal.text
    assert equal.json()["residual_score"] == equal.json()["inherent_score"] == 20

    lower = http_client.put(
        f"{API}/risks/{equal.json()['id']}",
        headers=_auth(admin_token),
        json={"residual_score": 6},
    )
    assert lower.status_code == 200, lower.text
    assert lower.json()["residual_score"] == 6

    invalid_create = http_client.post(
        f"{API}/risks/",
        headers=_auth(admin_token),
        json=_risk_payload(client.id, asset["id"], likelihood=2, impact=2, residual_score=5),
    )
    assert invalid_create.status_code == 422

    invalid_update = http_client.put(
        f"{API}/risks/{equal.json()['id']}",
        headers=_auth(admin_token),
        json={"likelihood": 2, "impact": 2, "residual_score": 5},
    )
    assert invalid_update.status_code == 422
