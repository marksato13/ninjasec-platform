"""31-P1: gap analysis de hardening -- reglas auto-verificables cruzando
datos reales de integraciones/eventos, y reglas manuales que nunca se
reportan como pass/fail sin evidencia."""

import json

from app.db.models.client import Client
from app.db.models.collection_snapshot import CollectionSnapshot
from app.db.models.integration import Integration
from app.db.seed import seed_hardening_catalog

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, organization_id, suffix):
    seed_hardening_catalog(db)
    client = Client(organization_id=organization_id, company_name=f"Cliente hardening {suffix}")
    db.add(client)
    db.commit()
    return client


def test_catalogo_tiene_12_reglas_con_metodo_de_verificacion(db, http_client, admin_token):
    seed_hardening_catalog(db)
    response = http_client.get(f"{API}/hardening/rules", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    rules = response.json()
    assert len(rules) == 12
    assert {r["verification_method"] for r in rules} == {"auto", "manual"}


def test_reglas_manuales_nunca_se_reportan_como_pass_o_fail(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "manual")
    response = http_client.get(f"{API}/hardening/evaluate?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    manual_results = [e for e in response.json() if e["rule"]["verification_method"] == "manual"]
    assert len(manual_results) == 7
    assert all(e["result"] == "manual" for e in manual_results)


def test_sin_integraciones_las_reglas_auto_fallan_o_no_aplican_pero_nunca_pasan_sin_evidencia(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "sinintegraciones")
    response = http_client.get(f"{API}/hardening/evaluate?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    by_code = {e["rule"]["code"]: e for e in response.json()}
    assert by_code["H-01"]["result"] == "fail"
    assert by_code["H-02"]["result"] == "fail"
    assert by_code["H-03"]["result"] == "not_applicable"
    assert by_code["H-04"]["result"] == "not_applicable"
    assert by_code["H-05"]["result"] == "not_applicable"


def test_firewall_conectado_hace_pasar_h01(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "firewall")
    integration = Integration(
        organization_id=seed_data["org"].id, client_id=client.id, connector_type="pfSense",
        name="pfSense conectado", base_url="https://pfsense.example.test", status="connected",
    )
    db.add(integration)
    db.commit()

    response = http_client.get(f"{API}/hardening/evaluate?client_id={client.id}", headers=_auth(admin_token))
    by_code = {e["rule"]["code"]: e for e in response.json()}
    assert by_code["H-01"]["result"] == "pass"


def test_evento_critico_de_autenticacion_hace_fallar_h04(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "bruteforce")
    integration = Integration(
        organization_id=seed_data["org"].id, client_id=client.id, connector_type="wazuh",
        name="Wazuh conectado", base_url="https://wazuh.example.test", status="connected",
    )
    db.add(integration)
    db.commit()
    db.add(CollectionSnapshot(
        integration_id=integration.id, snapshot_type="security_alerts", raw_payload="{}",
        normalized_payload=json.dumps({"events": [
            {"event": {"category": "authentication", "severity": "critical"}, "source": {"ip": "198.51.100.1"}, "rule": {"description": "fuerza bruta"}},
        ]}),
    ))
    db.commit()

    response = http_client.get(f"{API}/hardening/evaluate?client_id={client.id}", headers=_auth(admin_token))
    by_code = {e["rule"]["code"]: e for e in response.json()}
    assert by_code["H-02"]["result"] == "pass"
    assert by_code["H-04"]["result"] == "fail"


def test_resumen_calcula_porcentaje_solo_sobre_reglas_evaluables(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "resumen")
    response = http_client.get(f"{API}/hardening/summary?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total"] == 12
    assert summary["manual"] == 7
    # sin integraciones: H-01/H-02 fallan, H-03/H-04/H-05 no aplican -> 0 pasan de 2 evaluables
    assert summary["passed"] == 0
    assert summary["failed"] == 2
    assert summary["compliance_percent"] == 0.0


def test_exportar_pdf_genera_documento_valido(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "pdf")
    response = http_client.get(f"{API}/hardening/export/pdf?client_id={client.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 500


def test_rechaza_cliente_de_otra_organizacion(db, http_client, admin_token, seed_data):
    from app.db.models.organization import Organization

    foreign_org = Organization(name="Organizacion Hardening Ajena", slug="hardening-ajena")
    db.add(foreign_org)
    db.commit()
    foreign_client = _client(db, foreign_org.id, "ajeno")

    response = http_client.get(f"{API}/hardening/evaluate?client_id={foreign_client.id}", headers=_auth(admin_token))
    assert response.status_code == 404
