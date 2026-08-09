"""24-P1: catálogo ISO 27001:2022 y Declaración de Aplicabilidad (SoA)."""

from __future__ import annotations

import pytest

from app.db.models.client import Client
from app.db.models.compliance import ComplianceControl, ComplianceFramework
from app.db.models.organization import Organization
from app.db.seed import seed_compliance_catalog

API = "/api/v1"


@pytest.fixture(autouse=True)
def _seeded_catalog(db):
    # conftest.py no ejecuta el seed de la app (SEED_ON_STARTUP=false) --
    # se llama acá a la función real para probar el camino de siembra en
    # sí, no solo insertar datos de prueba a mano.
    seed_compliance_catalog(db)


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, org_id, suffix):
    client = Client(organization_id=org_id, company_name=f"Cliente cumplimiento {suffix}")
    db.add(client)
    db.commit()
    return client


def _framework_and_first_control(db):
    framework = db.query(ComplianceFramework).filter(
        ComplianceFramework.slug == "iso-27001-2022"
    ).one()
    control = db.query(ComplianceControl).filter(
        ComplianceControl.framework_id == framework.id, ComplianceControl.code == "A.5.1"
    ).one()
    return framework, control


def test_seed_carga_exactamente_93_controles(db, seed_data):
    framework = db.query(ComplianceFramework).filter(
        ComplianceFramework.slug == "iso-27001-2022"
    ).one()
    count = db.query(ComplianceControl).filter(
        ComplianceControl.framework_id == framework.id
    ).count()
    assert count == 93

    codes = {
        c.code for c in db.query(ComplianceControl).filter(
            ComplianceControl.framework_id == framework.id
        ).all()
    }
    assert {"A.5.1", "A.5.37", "A.6.1", "A.6.8", "A.7.1", "A.7.14", "A.8.1", "A.8.34"} <= codes


def test_listar_controles_sin_estado_devuelve_defaults(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "defaults")

    response = http_client.get(
        f"{API}/compliance/controls?client_id={client.id}", headers=_auth(admin_token)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 93
    first = next(c for c in body if c["code"] == "A.5.1")
    assert first["applicability"] == "applicable"
    assert first["implementation_status"] == "not_implemented"
    assert first["maturity_level"] == 0


def test_actualizar_estado_persiste_los_campos(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "persistencia")
    _, control = _framework_and_first_control(db)

    response = http_client.put(
        f"{API}/compliance/controls/{control.id}?client_id={client.id}",
        headers=_auth(admin_token),
        json={
            "implementation_status": "partial",
            "maturity_level": 3,
            "applicability": "applicable",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["implementation_status"] == "partial"
    assert body["maturity_level"] == 3

    listed = http_client.get(
        f"{API}/compliance/controls?client_id={client.id}", headers=_auth(admin_token)
    ).json()
    updated = next(c for c in listed if c["control_id"] == control.id)
    assert updated["implementation_status"] == "partial"
    assert updated["maturity_level"] == 3


def test_not_applicable_sin_justificacion_falla(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "justificacion")
    _, control = _framework_and_first_control(db)

    response = http_client.put(
        f"{API}/compliance/controls/{control.id}?client_id={client.id}",
        headers=_auth(admin_token),
        json={"applicability": "not_applicable"},
    )
    assert response.status_code == 422

    with_justification = http_client.put(
        f"{API}/compliance/controls/{control.id}?client_id={client.id}",
        headers=_auth(admin_token),
        json={"applicability": "not_applicable", "justification": "Cliente no usa la nube."},
    )
    assert with_justification.status_code == 200, with_justification.text


def test_porcentaje_excluye_no_aplicables(db, http_client, admin_token, seed_data):
    client = _client(db, seed_data["org"].id, "porcentaje")
    framework = db.query(ComplianceFramework).filter(
        ComplianceFramework.slug == "iso-27001-2022"
    ).one()
    controls = db.query(ComplianceControl).filter(
        ComplianceControl.framework_id == framework.id
    ).order_by(ComplianceControl.code).limit(3).all()

    # 1 implementado, 1 not_applicable, 1 sin tocar (not_implemented)
    http_client.put(
        f"{API}/compliance/controls/{controls[0].id}?client_id={client.id}",
        headers=_auth(admin_token), json={"implementation_status": "implemented"},
    )
    http_client.put(
        f"{API}/compliance/controls/{controls[1].id}?client_id={client.id}",
        headers=_auth(admin_token),
        json={"applicability": "not_applicable", "justification": "No aplica"},
    )

    summary = http_client.get(
        f"{API}/compliance/soa?client_id={client.id}", headers=_auth(admin_token)
    )
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["total_controls"] == 93
    assert body["applicable_controls"] == 92  # 93 - 1 not_applicable
    assert body["implemented_controls"] == 1
    assert body["compliance_percentage"] == round(100 * 1 / 92, 1)


def test_cliente_de_otra_organizacion_no_es_visible(db, http_client, admin_token, seed_data):
    other_org = Organization(name="Tenant compliance ajeno", slug="tenant-compliance-ajeno")
    db.add(other_org)
    db.flush()
    other_client = _client(db, other_org.id, "otra-org")

    response = http_client.get(
        f"{API}/compliance/controls?client_id={other_client.id}", headers=_auth(admin_token)
    )
    assert response.status_code == 404


def test_colaborador_consulta_pero_no_edita(db, http_client, collaborator_token, seed_data):
    client = _client(db, seed_data["org"].id, "colaborador")
    _, control = _framework_and_first_control(db)

    listed = http_client.get(
        f"{API}/compliance/controls?client_id={client.id}", headers=_auth(collaborator_token)
    )
    assert listed.status_code == 200

    denied = http_client.put(
        f"{API}/compliance/controls/{control.id}?client_id={client.id}",
        headers=_auth(collaborator_token),
        json={"implementation_status": "implemented"},
    )
    assert denied.status_code == 403
