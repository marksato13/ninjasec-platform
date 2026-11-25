"""Una solicitud de servicio aprobada se convierte en proyecto.

Auditoria funcional del 2026-11-25 (A6): el embudo lead -> cliente -> solicitud ->
proyecto se cortaba en la solicitud; el admin creaba el proyecto a mano y nada los
enlazaba.
"""

from __future__ import annotations

import importlib
from uuid import uuid4

import pytest

from app.db.models.area import Area
from app.db.models.client import Client
from app.db.models.enums import ServiceRequestStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_type import ProjectType
from app.db.models.service import Service
from app.db.models.service_request import ServiceRequest
from tests.conftest import API

MIGRACION = "app.db.migrations.versions.20261128_01_solicitud_a_proyecto"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _escenario(db, organization_id: int, *, con_area: bool = True, con_cliente: bool = True) -> dict:
    s = uuid4().hex[:8]
    area = Area(organization_id=organization_id, name=f"Ninja Sec {s}", slug=f"sec-{s}")
    db.add(area)
    db.flush()
    servicio = Service(
        organization_id=organization_id,
        area_id=area.id if con_area else None,
        title=f"Diagnostico {s}",
        slug=f"diagnostico-{s}",
    )
    cliente = Client(organization_id=organization_id, company_name=f"Pyme {s}")
    tipo = ProjectType(organization_id=organization_id, name=f"Consultoria {s}", slug=f"consultoria-{s}")
    db.add_all([servicio, cliente, tipo])
    db.flush()
    solicitud = ServiceRequest(
        service_id=servicio.id,
        client_id=cliente.id if con_cliente else None,
        requester_name="Gerente",
        requester_email="gerente@example.com",
        message="Necesitamos revisar el firewall",
        status=ServiceRequestStatus.REVIEW,
    )
    db.add(solicitud)
    db.commit()
    return {"area": area, "servicio": servicio, "cliente": cliente, "tipo": tipo, "solicitud": solicitud}


@pytest.fixture
def propio(db, seed_data):
    return _escenario(db, seed_data["org"].id)


def _convertir(http_client, token, solicitud_id, **cuerpo):
    return http_client.post(
        f"{API}/services/requests/{solicitud_id}/convert", json=cuerpo, headers=_auth(token)
    )


def test_crea_el_proyecto_con_servicio_area_y_cliente_y_cierra_la_solicitud(http_client, admin_token, propio, db):
    r = _convertir(http_client, admin_token, propio["solicitud"].id, project_type_id=propio["tipo"].id)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["status"] == "CLOSED" and cuerpo["project_id"]
    proyecto = db.get(Project, cuerpo["project_id"])
    assert proyecto.client_id == propio["cliente"].id
    assert proyecto.service_id == propio["servicio"].id
    assert proyecto.area_id == propio["area"].id
    assert str(proyecto.status) == "planning"


def test_convertir_dos_veces_da_409_y_no_duplica(http_client, admin_token, propio, db):
    primero = _convertir(http_client, admin_token, propio["solicitud"].id, project_type_id=propio["tipo"].id)
    assert primero.status_code == 201
    antes = db.query(Project).count()
    r = _convertir(http_client, admin_token, propio["solicitud"].id, project_type_id=propio["tipo"].id)
    assert r.status_code == 409
    assert db.query(Project).count() == antes


def test_solicitud_publica_sin_cliente_exige_uno(http_client, admin_token, db, seed_data):
    e = _escenario(db, seed_data["org"].id, con_cliente=False)
    r = _convertir(http_client, admin_token, e["solicitud"].id, project_type_id=e["tipo"].id)
    assert r.status_code == 422
    r = _convertir(
        http_client, admin_token, e["solicitud"].id, project_type_id=e["tipo"].id, client_id=e["cliente"].id
    )
    assert r.status_code == 201, r.text


def test_servicio_sin_area_da_400(http_client, admin_token, db, seed_data):
    e = _escenario(db, seed_data["org"].id, con_area=False)
    r = _convertir(http_client, admin_token, e["solicitud"].id, project_type_id=e["tipo"].id)
    assert r.status_code == 400


def test_solicitud_de_otra_organizacion_da_404(http_client, admin_token, db):
    s = uuid4().hex[:8]
    org = Organization(name=f"Ajena {s}", slug=f"ajena-{s}")
    db.add(org)
    db.commit()
    e = _escenario(db, org.id)
    r = _convertir(http_client, admin_token, e["solicitud"].id, project_type_id=e["tipo"].id)
    assert r.status_code == 404
    db.expire_all()
    assert db.get(ServiceRequest, e["solicitud"].id).project_id is None


def test_cliente_o_tipo_de_otra_organizacion_dan_404(http_client, admin_token, propio, db):
    s = uuid4().hex[:8]
    org = Organization(name=f"Ajena {s}", slug=f"ajena-{s}")
    db.add(org)
    db.commit()
    ajeno = _escenario(db, org.id, con_cliente=False)
    publica = _escenario(db, propio["servicio"].organization_id, con_cliente=False)
    r = _convertir(
        http_client, admin_token, publica["solicitud"].id,
        project_type_id=publica["tipo"].id, client_id=ajeno["cliente"].id,
    )
    assert r.status_code == 404
    r = _convertir(http_client, admin_token, propio["solicitud"].id, project_type_id=ajeno["tipo"].id)
    assert r.status_code == 404


def test_el_colaborador_no_puede_convertir(http_client, collaborator_token, propio):
    r = _convertir(http_client, collaborator_token, propio["solicitud"].id, project_type_id=propio["tipo"].id)
    assert r.status_code == 403


# --- La migracion ------------------------------------------------------------


def test_la_migracion_encadena_con_la_cabeza_anterior():
    m = importlib.import_module(MIGRACION)
    assert (m.revision, m.down_revision) == ("20261128_01", "20261127_01")


def test_la_columna_coincide_con_el_modelo():
    from app.db.base import Base

    col = Base.metadata.tables["service_requests"].c.project_id
    assert col.nullable is True
    assert {fk.column.table.name for fk in col.foreign_keys} == {"projects"}
