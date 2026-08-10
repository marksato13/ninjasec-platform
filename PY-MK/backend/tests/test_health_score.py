"""30-P3: índice de salud de seguridad -- "SOC as a report".

Combina cuatro señales reales ya construidas en la plataforma (hallazgos
de revisiones, hardening, riesgo de hosts, CVEs de alta explotabilidad).
Cada deducción tiene un tope, verificado explícitamente."""

from app.db.models.client import Client
from app.db.models.enums import FindingSeverity, FindingStatus, ReviewStatus
from app.db.models.integration import Integration
from app.db.models.security_review import ReviewFinding, SecurityReview
from app.db.seed import seed_hardening_catalog

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, organization_id, suffix):
    seed_hardening_catalog(db)
    client = Client(organization_id=organization_id, company_name=f"Cliente salud {suffix}")
    db.add(client)
    db.commit()
    return client


def test_cliente_sin_integraciones_arrastra_el_gap_de_hardening_base(db, http_client, admin_token, seed_data):
    """Un cliente sin ninguna integración configurada falla H-01/H-02 de
    hardening (sin firewall ni SIEM integrado) -- eso es honesto, no un
    bug: no tener nada integrado es en sí mismo una brecha real."""
    client = _client(db, seed_data["org"].id, "perfecto")
    response = http_client.get(f"{API}/health-score?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    data = response.json()
    hardening_item = next(b for b in data["breakdown"] if "hardening" in b["category"])
    assert hardening_item["deduction"] == 20  # H-01 (high=10) + H-02 (high=10)
    assert data["score"] == 80
    other_items = [b for b in data["breakdown"] if "hardening" not in b["category"]]
    assert all(item["deduction"] == 0 for item in other_items)


def test_hallazgo_critico_abierto_resta_puntos_pero_resuelto_no(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "hallazgos")
    integration = Integration(organization_id=seed_data["org"].id, client_id=client.id, connector_type="manual", name="Integ", base_url="https://example.test")
    db.add(integration)
    db.commit()
    review = SecurityReview(organization_id=seed_data["org"].id, client_id=client.id, integration_id=integration.id, status=ReviewStatus.CLOSED)
    db.add(review)
    db.commit()
    db.add_all([
        ReviewFinding(review_id=review.id, severity=FindingSeverity.CRITICAL, title="Abierto crítico", status=FindingStatus.OPEN),
        ReviewFinding(review_id=review.id, severity=FindingSeverity.HIGH, title="Resuelto", status=FindingStatus.RESOLVED),
    ])
    db.commit()

    response = http_client.get(f"{API}/health-score?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    data = response.json()
    findings_item = next(b for b in data["breakdown"] if "Hallazgos" in b["category"])
    assert findings_item["count"] == 1  # solo el abierto cuenta
    assert findings_item["deduction"] == 15  # peso de severidad critical
    # La integración de este test es connector_type="manual" (no pfSense/FortiGate/Wazuh)
    # y no tiene ninguna recolección de datos -- H-01 (10) + H-02 (10) + H-03 (5) = 25.
    assert data["score"] == 60


def test_deduccion_de_hallazgos_tiene_tope_30(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "topefindings")
    integration = Integration(organization_id=seed_data["org"].id, client_id=client.id, connector_type="manual", name="Integ", base_url="https://example.test")
    db.add(integration)
    db.commit()
    review = SecurityReview(organization_id=seed_data["org"].id, client_id=client.id, integration_id=integration.id, status=ReviewStatus.CLOSED)
    db.add(review)
    db.commit()
    db.add_all([ReviewFinding(review_id=review.id, severity=FindingSeverity.CRITICAL, title=f"F{i}", status=FindingStatus.OPEN) for i in range(5)])
    db.commit()  # 5 x 15 = 75 puntos crudos, tope real es 30

    response = http_client.get(f"{API}/health-score?client_id={client.id}", headers=_auth(admin_token))
    data = response.json()
    findings_item = next(b for b in data["breakdown"] if "Hallazgos" in b["category"])
    assert findings_item["deduction"] == 30


def test_export_pdf_genera_documento_valido(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "pdf")
    response = http_client.get(f"{API}/health-score/export/pdf?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 500


def test_rechaza_cliente_de_otra_organizacion(db, http_client, admin_token, seed_data):
    from app.db.models.organization import Organization

    foreign_org = Organization(name="Organizacion Salud Ajena", slug="salud-ajena")
    db.add(foreign_org)
    db.commit()
    foreign_client = _client(db, foreign_org.id, "ajeno")

    response = http_client.get(f"{API}/health-score?client_id={foreign_client.id}", headers=_auth(admin_token))
    assert response.status_code == 404
