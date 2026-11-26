"""Un ticket solo enlaza cosas de su organización y de su cliente.

Antes, el alta y la importación aceptaban cualquier `client_id`,
`integration_id`, `device_id`, `review_id`, `finding_id` o `assigned_to`:
se podía abrir un ticket contra el cliente o el equipo de otra organización, y
un cliente podía enlazar la revisión de otro cliente. Lo ajeno da 404.
"""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from openpyxl import Workbook

from app.db.models.client import Client
from app.db.models.device import Device
from app.db.models.enums import FindingSeverity, FindingStatus, RoleCode
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.security_review import ReviewFinding, SecurityReview
from app.db.models.support_ticket import SupportTicket
from app.db.models.user import User
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _proyecto_del_cliente

URL = f"{API}/support-tickets"


def _recursos(db, org_id: int, client_id: int, sufijo: str) -> dict:
    integ = Integration(organization_id=org_id, client_id=client_id, connector_type="manual",
                        name=f"Integ {sufijo}", base_url="https://ejemplo.invalid")
    db.add(integ)
    db.flush()
    equipo = Device(hostname=f"fw-{sufijo}", integration_id=integ.id, status="up")
    revision = SecurityReview(organization_id=org_id, client_id=client_id, integration_id=integ.id)
    db.add_all([equipo, revision])
    db.flush()
    hallazgo = ReviewFinding(review_id=revision.id, severity=FindingSeverity.HIGH, title="H", status=FindingStatus.OPEN)
    db.add(hallazgo)
    db.commit()
    return {"integration_id": integ.id, "device_id": equipo.id, "review_id": revision.id, "finding_id": hallazgo.id}


@pytest.fixture
def ajena(db):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    cliente = Client(organization_id=org.id, company_name=f"Cliente ajeno {sufijo}")
    db.add(cliente)
    db.flush()
    rol = db.query(Role).filter(Role.code == RoleCode.ADMIN.value).first()
    gente = User(organization_id=org.id, role_id=rol.id, email=f"ajeno-{sufijo}@otra.invalid", full_name="Ajeno",
                 password_hash="x", role_code=RoleCode.ADMIN)
    db.add(gente)
    db.commit()
    return {"cliente": cliente, "usuario": gente, **_recursos(db, org.id, cliente.id, sufijo)}


@pytest.fixture
def propio(db, seed_data):
    sufijo = uuid4().hex[:8]
    cliente = Client(organization_id=seed_data["org"].id, company_name=f"Cliente propio {sufijo}")
    db.add(cliente)
    db.commit()
    return {"cliente": cliente, **_recursos(db, seed_data["org"].id, cliente.id, sufijo)}


def _alta(http_client, token, **campos):
    cuerpo = {"title": "Algo falla", "priority": "medium", **campos}
    return http_client.post(f"{URL}/", json=cuerpo, headers=_auth(token))


def test_lo_propio_se_acepta(http_client, admin_token, propio, seed_data):
    r = _alta(http_client, admin_token, client_id=propio["cliente"].id, integration_id=propio["integration_id"],
              device_id=propio["device_id"], review_id=propio["review_id"], finding_id=propio["finding_id"],
              assigned_to=seed_data["collab"].id)
    assert r.status_code == 201, r.text


def test_cliente_de_otra_organizacion_da_404(http_client, admin_token, ajena, db):
    antes = db.query(SupportTicket).count()
    r = _alta(http_client, admin_token, client_id=ajena["cliente"].id)
    assert r.status_code == 404, r.text
    assert db.query(SupportTicket).count() == antes


@pytest.mark.parametrize("campo", ["integration_id", "device_id", "review_id", "finding_id"])
def test_recurso_de_otra_organizacion_da_404(http_client, admin_token, propio, ajena, campo):
    r = _alta(http_client, admin_token, client_id=propio["cliente"].id, **{campo: ajena[campo]})
    assert r.status_code == 404, (campo, r.text)


def test_recurso_de_otro_cliente_de_la_misma_organizacion_da_404(http_client, admin_token, propio, db, seed_data):
    otro = Client(organization_id=seed_data["org"].id, company_name=f"Otro {uuid4().hex[:6]}")
    db.add(otro)
    db.commit()
    for campo in ("integration_id", "device_id", "review_id", "finding_id"):
        r = _alta(http_client, admin_token, client_id=otro.id, **{campo: propio[campo]})
        assert r.status_code == 404, (campo, r.text)


def test_el_cliente_no_enlaza_la_revision_de_otro_cliente(db, http_client, seed_data, propio):
    sufijo = f"rev-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    _proyecto_del_cliente(db, seed_data["org"].id, sufijo)
    r = _alta(http_client, token, review_id=propio["review_id"])
    assert r.status_code == 404, r.text


def test_asignar_a_alguien_de_otra_organizacion_da_404(http_client, admin_token, propio, ajena):
    r = _alta(http_client, admin_token, client_id=propio["cliente"].id, assigned_to=ajena["usuario"].id)
    assert r.status_code == 404, r.text
    tid = _alta(http_client, admin_token, client_id=propio["cliente"].id).json()["id"]
    r = http_client.patch(f"{URL}/{tid}", json={"assigned_to": ajena["usuario"].id}, headers=_auth(admin_token))
    assert r.status_code == 404, r.text


def test_la_importacion_salta_la_fila_ajena(http_client, admin_token, propio, ajena, db):
    libro = Workbook()
    hoja = libro.active
    hoja.append(["client_id", "title", "priority"])
    hoja.append([propio["cliente"].id, "Propio", "low"])
    hoja.append([ajena["cliente"].id, "Infiltrado", "low"])
    buf = io.BytesIO()
    libro.save(buf)
    r = http_client.post(f"{URL}/import", headers=_auth(admin_token),
                         files={"file": ("t.xlsx", buf.getvalue(),
                                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 1 and r.json()["skipped"] == 1, r.json()
    assert db.query(SupportTicket).filter(SupportTicket.title == "Infiltrado").count() == 0
