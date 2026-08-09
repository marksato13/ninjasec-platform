"""25-P1: activos y CRUD del registro de riesgos."""
from app.db.models.client import Client

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _asset(http_client, token, client_id):
    response = http_client.post(f"{API}/risks/assets", headers=_auth(token), json={
        "client_id": client_id, "name": "Información de clientes", "asset_type": "information",
        "confidentiality": 5, "integrity": 4, "availability": 3,
    })
    assert response.status_code == 201, response.text
    assert response.json()["business_value"] == 5
    return response.json()


def test_crud_calcula_score_e_ignora_score_del_cliente(db, http_client, admin_token, seed_data):
    client = Client(organization_id=seed_data["org"].id, company_name="Cliente riesgos")
    db.add(client); db.commit()
    asset = _asset(http_client, admin_token, client.id)
    created = http_client.post(f"{API}/risks/", headers=_auth(admin_token), json={
        "client_id": client.id, "asset_id": asset["id"], "title": "Exposición de datos",
        "likelihood": 4, "impact": 5, "inherent_score": 1,
        "residual_likelihood": 2, "residual_impact": 3,
    })
    assert created.status_code == 201, created.text
    risk = created.json()
    assert risk["inherent_score"] == 20
    assert risk["residual_score"] == 6

    updated = http_client.put(f"{API}/risks/{risk['id']}", headers=_auth(admin_token), json={
        "likelihood": 2, "impact": 3, "inherent_score": 25,
        "residual_likelihood": 1, "residual_impact": 2,
    })
    assert updated.status_code == 200, updated.text
    assert updated.json()["inherent_score"] == 6
    assert updated.json()["residual_score"] == 2
    assert http_client.get(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 200
    assert http_client.delete(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 204
    assert http_client.get(f"{API}/risks/{risk['id']}", headers=_auth(admin_token)).status_code == 404


def test_rechaza_residual_mayor_al_inherente(db, http_client, admin_token, seed_data):
    client = Client(organization_id=seed_data["org"].id, company_name="Cliente residual")
    db.add(client); db.commit()
    asset = _asset(http_client, admin_token, client.id)
    response = http_client.post(f"{API}/risks/", headers=_auth(admin_token), json={
        "client_id": client.id, "asset_id": asset["id"], "title": "Riesgo inválido",
        "likelihood": 2, "impact": 2, "residual_score": 5,
    })
    assert response.status_code == 422


def test_aislamiento_por_organizacion(db, http_client, admin_token, seed_data):
    from app.db.models.organization import Organization
    other = Organization(name="Otra org riesgos", slug="otra-org-riesgos")
    db.add(other); db.flush()
    client = Client(organization_id=other.id, company_name="Cliente externo")
    db.add(client); db.commit()
    response = http_client.post(f"{API}/risks/assets", headers=_auth(admin_token), json={
        "client_id": client.id, "name": "Ajeno", "asset_type": "service",
        "confidentiality": 1, "integrity": 1, "availability": 1,
    })
    assert response.status_code == 404
