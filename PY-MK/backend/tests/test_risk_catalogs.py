"""25-P2: catálogo reutilizable de amenazas/vulnerabilidades y mapa de calor.

Estos casos son independientes de test_risks.py (25-P1): cubren la
reutilización N:N del catálogo, el aislamiento por organización de las
entradas propias vs. globales y la agregación en el mapa de calor 5x5.
"""

from app.db.models.client import Client
from app.db.models.organization import Organization
from app.db.models.risk import Threat, Vulnerability, risk_threats, risk_vulnerabilities

API = "/api/v1/risks"


def _other_org(db):
    org = db.query(Organization).filter(Organization.slug == "org-ajena-riesgos").first()
    if org is None:
        org = Organization(name="Organizacion Ajena Riesgos", slug="org-ajena-riesgos")
        db.add(org)
        db.commit()
    return org


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, organization_id, suffix):
    client = Client(organization_id=organization_id, company_name=f"Cliente catálogo {suffix}")
    db.add(client)
    db.commit()
    return client


def _asset_payload(client_id, **overrides):
    return {
        "client_id": client_id,
        "name": "Servidor de aplicaciones",
        "asset_type": "hardware",
        "confidentiality": 4,
        "integrity": 4,
        "availability": 4,
        **overrides,
    }


def _global_catalog(db):
    threat = Threat(code="T-TEST-01", name="Acceso no autorizado", category="Deliberada", is_global=True)
    vulnerability = Vulnerability(code="V-TEST-01", name="Control de acceso débil", category="Técnica", is_global=True)
    db.add_all([threat, vulnerability])
    db.commit()
    db.refresh(threat)
    db.refresh(vulnerability)
    return threat, vulnerability


def _create_asset(http_client, token, client_id):
    response = http_client.post(f"{API}/assets", headers=_auth(token), json=_asset_payload(client_id))
    assert response.status_code == 201, response.text
    return response.json()


def _create_risk(http_client, token, client_id, asset_id, likelihood, impact, threat_id=None, vulnerability_id=None, title=None):
    payload = {
        "client_id": client_id,
        "asset_id": asset_id,
        "title": title or f"Riesgo L{likelihood}-I{impact}",
        "likelihood": likelihood,
        "impact": impact,
        "threat_ids": [threat_id, threat_id] if threat_id else [],
        "vulnerability_ids": [vulnerability_id] if vulnerability_id else [],
    }
    response = http_client.post(f"{API}/", headers=_auth(token), json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_riesgos_reutilizan_catalogo_sin_duplicar_su_texto(db, http_client, admin_token, seed_data):
    """Las asociaciones guardan referencias, no copias de amenazas o vulnerabilidades."""
    client = _client(db, seed_data["org"].id, "reuso")
    asset = _create_asset(http_client, admin_token, client.id)
    threat, vulnerability = _global_catalog(db)

    first = _create_risk(http_client, admin_token, client.id, asset["id"], 1, 1, threat.id, vulnerability.id)
    second = _create_risk(http_client, admin_token, client.id, asset["id"], 2, 2, threat.id, vulnerability.id)

    assert db.query(Threat).filter_by(name="Acceso no autorizado").count() == 1
    assert db.query(Vulnerability).filter_by(name="Control de acceso débil").count() == 1
    assert set(db.execute(risk_threats.select()).all()) == {
        (first["id"], threat.id),
        (second["id"], threat.id),
    }
    assert set(db.execute(risk_vulnerabilities.select()).all()) == {
        (first["id"], vulnerability.id),
        (second["id"], vulnerability.id),
    }
    for risk in (first, second):
        assert [item["id"] for item in risk["threats"]] == [threat.id]
        assert [item["id"] for item in risk["vulnerabilities"]] == [vulnerability.id]
        assert risk["threats"][0]["is_global"] is True


def test_catalogo_de_otra_organizacion_no_es_visible(db, http_client, admin_token, seed_data):
    """Una entrada creada por una organización no aparece en el catálogo de otra."""
    own = http_client.post(
        f"{API}/threats", headers=_auth(admin_token),
        json={"code": "T-ORG-01", "name": "Amenaza propia", "category": "Deliberada"},
    )
    assert own.status_code == 201, own.text
    assert own.json()["is_global"] is False

    ajena = _other_org(db)
    db.add(Threat(organization_id=ajena.id, code="T-ORG-01", name="Amenaza ajena", category="Deliberada", is_global=False))
    db.commit()

    listed = http_client.get(f"{API}/threats", headers=_auth(admin_token))
    assert listed.status_code == 200, listed.text
    names = {item["name"] for item in listed.json()}
    assert "Amenaza propia" in names
    assert "Amenaza ajena" not in names


def test_crear_entrada_duplicada_en_la_misma_org_se_rechaza(http_client, admin_token):
    first = http_client.post(
        f"{API}/vulnerabilities", headers=_auth(admin_token),
        json={"code": "v-dup-01", "name": "Primera", "category": "Técnica"},
    )
    assert first.status_code == 201, first.text

    duplicate = http_client.post(
        f"{API}/vulnerabilities", headers=_auth(admin_token),
        json={"code": "V-DUP-01", "name": "Segunda", "category": "Técnica"},
    )
    assert duplicate.status_code == 409


def test_actualizar_asociaciones_reutiliza_entradas_del_catalogo(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "asociaciones")
    asset = _create_asset(http_client, admin_token, client.id)
    threat, vulnerability = _global_catalog(db)
    risk = _create_risk(http_client, admin_token, client.id, asset["id"], 3, 3, threat.id, vulnerability.id)

    replacement = Threat(code="T-TEST-02", name="Malware", category="Deliberada", is_global=True)
    db.add(replacement)
    db.commit()
    db.refresh(replacement)

    updated = http_client.put(
        f"{API}/{risk['id']}/associations",
        headers=_auth(admin_token),
        json={"threat_ids": [replacement.id, replacement.id], "vulnerability_ids": []},
    )
    assert updated.status_code == 200, updated.text
    assert [item["id"] for item in updated.json()["threats"]] == [replacement.id]
    assert updated.json()["vulnerabilities"] == []
    assert db.query(Threat).filter_by(name="Malware").count() == 1


def test_asociar_entrada_de_catalogo_inexistente_devuelve_404(http_client, admin_token, db, seed_data):
    client = _client(db, seed_data["org"].id, "inexistente")
    asset = _create_asset(http_client, admin_token, client.id)
    response = http_client.post(
        f"{API}/", headers=_auth(admin_token),
        json={"client_id": client.id, "asset_id": asset["id"], "title": "X", "likelihood": 1, "impact": 1, "threat_ids": [999999]},
    )
    assert response.status_code == 404


def test_riesgos_ocupan_cada_una_de_las_25_celdas_del_mapa(db, http_client, admin_token, seed_data):
    """Cada combinación likelihood x impact queda en su celda del mapa 5x5."""
    client = _client(db, seed_data["org"].id, "mapa")
    asset = _create_asset(http_client, admin_token, client.id)

    created = [
        _create_risk(http_client, admin_token, client.id, asset["id"], likelihood, impact)
        for likelihood in range(1, 6)
        for impact in range(1, 6)
    ]
    assert len(created) == 25

    heatmap = http_client.get(f"{API}/heatmap?client_id={client.id}", headers=_auth(admin_token))
    assert heatmap.status_code == 200, heatmap.text
    cells = heatmap.json()
    assert len(cells) == 25
    by_position = {(cell["likelihood"], cell["impact"]): cell for cell in cells}
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            cell = by_position[(likelihood, impact)]
            assert len(cell["risks"]) == 1
            assert cell["risks"][0]["inherent_score"] == likelihood * impact


def test_mover_riesgo_de_celda_actualiza_el_mapa(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "mover")
    asset = _create_asset(http_client, admin_token, client.id)
    risk = _create_risk(http_client, admin_token, client.id, asset["id"], 2, 4)

    updated = http_client.put(
        f"{API}/{risk['id']}",
        headers=_auth(admin_token),
        json={"likelihood": 5, "impact": 3},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["inherent_score"] == 15

    heatmap = http_client.get(f"{API}/heatmap?client_id={client.id}", headers=_auth(admin_token)).json()
    by_position = {(cell["likelihood"], cell["impact"]): cell for cell in heatmap}
    assert by_position[(2, 4)]["risks"] == []
    assert [r["id"] for r in by_position[(5, 3)]["risks"]] == [risk["id"]]
