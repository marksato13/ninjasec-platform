"""Aislamiento multi-tenant en equipos y hallazgos de revision.

Encontrado en la auditoria de seguridad del 2026-11-25:

- `PATCH /devices/{id}` no comprobaba la organizacion del equipo, y crear o
  editar un equipo aceptaba la sede (`site_id`) de otra organizacion.
- `PATCH /security-reviews/findings/{id}` editaba hallazgos de cualquier
  organizacion, tambien con rol colaborador.

Regla de AGENTS.md: datos de otra organizacion devuelven 404, para no
confirmar que existen.
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import FindingSeverity, FindingStatus, SiteStatus
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from app.db.models.security_review import ReviewFinding, SecurityReview
from tests.conftest import API


def _org_con_datos(db: Session, nombre: str, org: Organization | None = None) -> dict:
    """Cliente, sede, integracion, equipo y una revision con un hallazgo."""
    sufijo = uuid4().hex[:8]
    if org is None:
        org = Organization(name=f"{nombre} {sufijo}", slug=f"{nombre.lower()}-{sufijo}")
        db.add(org)
        db.flush()
    cliente = Client(organization_id=org.id, company_name=f"Cliente {nombre} {sufijo}")
    db.add(cliente)
    db.flush()
    sede = ClientSite(client_id=cliente.id, name=f"Sede {nombre}", address="x", status=SiteStatus.ACTIVE)
    integracion = Integration(
        organization_id=org.id,
        client_id=cliente.id,
        connector_type="manual",
        name=f"Integracion {nombre}",
        base_url="https://ejemplo.invalid",
    )
    db.add_all([sede, integracion])
    db.flush()
    equipo = Device(hostname=f"fw-{sufijo}", integration_id=integracion.id, site_id=sede.id, status="up")
    revision = SecurityReview(organization_id=org.id, client_id=cliente.id, integration_id=integracion.id)
    db.add_all([equipo, revision])
    db.flush()
    hallazgo = ReviewFinding(
        review_id=revision.id, severity=FindingSeverity.HIGH, title="Original", status=FindingStatus.OPEN
    )
    db.add(hallazgo)
    db.commit()
    return {"org": org, "sede": sede, "equipo": equipo, "revision": revision, "hallazgo": hallazgo}


@pytest.fixture
def ajena(db: Session):
    return _org_con_datos(db, "Ajena")


@pytest.fixture
def propia(db: Session, seed_data):
    org = db.get(Organization, seed_data["org"].id)
    return _org_con_datos(db, "Propia", org=org)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Equipos -----------------------------------------------------------------


def test_no_se_puede_editar_un_equipo_ajeno(http_client, admin_token, ajena, db):
    equipo_id = ajena["equipo"].id
    r = http_client.patch(f"{API}/devices/{equipo_id}", json={"hostname": "secuestrado"}, headers=_auth(admin_token))
    assert r.status_code == 404, f"Editar un equipo ajeno devolvio {r.status_code}; debe ser 404"
    db.expire_all()
    assert db.get(Device, equipo_id).hostname != "secuestrado", "El equipo ajeno se modifico"


def test_un_colaborador_tampoco_edita_un_equipo_ajeno(http_client, collaborator_token, ajena):
    r = http_client.patch(
        f"{API}/devices/{ajena['equipo'].id}", json={"hostname": "x"}, headers=_auth(collaborator_token)
    )
    assert r.status_code == 404


def test_no_se_puede_mover_un_equipo_propio_a_una_sede_ajena(http_client, admin_token, propia, ajena):
    r = http_client.patch(
        f"{API}/devices/{propia['equipo'].id}", json={"site_id": ajena["sede"].id}, headers=_auth(admin_token)
    )
    assert r.status_code == 404


def test_no_se_puede_crear_un_equipo_en_una_sede_ajena(http_client, admin_token, ajena):
    r = http_client.post(
        f"{API}/devices/", json={"hostname": "infiltrado", "site_id": ajena["sede"].id}, headers=_auth(admin_token)
    )
    assert r.status_code == 404, f"Crear en sede ajena devolvio {r.status_code}"


def test_el_equipo_propio_sigue_siendo_editable(http_client, admin_token, propia):
    """Control: el arreglo no puede romper el caso legitimo."""
    r = http_client.patch(
        f"{API}/devices/{propia['equipo'].id}",
        json={"hostname": "fw-renombrado", "site_id": propia["sede"].id},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["hostname"] == "fw-renombrado"


# --- Hallazgos de revision ---------------------------------------------------


def test_no_se_puede_editar_un_hallazgo_ajeno(http_client, admin_token, ajena, db):
    hallazgo_id = ajena["hallazgo"].id
    r = http_client.patch(
        f"{API}/security-reviews/findings/{hallazgo_id}", json={"title": "secuestrado"}, headers=_auth(admin_token)
    )
    assert r.status_code == 404, f"Editar un hallazgo ajeno devolvio {r.status_code}; debe ser 404"
    db.expire_all()
    assert db.get(ReviewFinding, hallazgo_id).title == "Original", "El hallazgo ajeno se modifico"


def test_un_colaborador_no_edita_hallazgos_de_una_revision_que_no_es_suya(
    http_client, collaborator_token, propia
):
    r = http_client.patch(
        f"{API}/security-reviews/findings/{propia['hallazgo'].id}",
        json={"title": "x"},
        headers=_auth(collaborator_token),
    )
    assert r.status_code == 403


def test_el_admin_edita_un_hallazgo_propio(http_client, admin_token, propia):
    r = http_client.patch(
        f"{API}/security-reviews/findings/{propia['hallazgo'].id}",
        json={"title": "Corregido"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Corregido"
