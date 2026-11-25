"""El proyecto queda en un area (Ninja Sec / Ninja Dev) al crearlo.

Auditoria funcional del 2026-11-25 (A5): el alta ignoraba el `area_id` elegido y
solo lo derivaba del servicio; con un servicio sin area, el proyecto no se podia
crear. Ahora el area elegida manda, se valida contra la organizacion (la ajena da
404) y, si no viene, se sigue derivando del servicio.
"""

from uuid import uuid4

import pytest

from app.db.models.area import Area
from app.db.models.client import Client
from app.db.models.organization import Organization
from app.db.models.project_type import ProjectType
from app.db.models.service import Service
from tests.conftest import API


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def base(db, seed_data):
    org_id = seed_data["org"].id
    sufijo = uuid4().hex[:8]
    sec = Area(organization_id=org_id, name=f"Ninja Sec {sufijo}", slug=f"sec-{sufijo}")
    dev = Area(organization_id=org_id, name=f"Ninja Dev {sufijo}", slug=f"dev-{sufijo}")
    tipo = ProjectType(organization_id=org_id, name=f"Tipo {sufijo}", slug=f"tipo-{sufijo}")
    cliente = Client(organization_id=org_id, company_name=f"Cliente {sufijo}")
    db.add_all([sec, dev, tipo, cliente])
    db.flush()
    con_area = Service(
        organization_id=org_id, area_id=sec.id, project_type_id=tipo.id,
        title=f"Con area {sufijo}", slug=f"con-area-{sufijo}",
    )
    sin_area = Service(
        organization_id=org_id, area_id=None, project_type_id=tipo.id,
        title=f"Sin area {sufijo}", slug=f"sin-area-{sufijo}",
    )
    db.add_all([con_area, sin_area])
    db.commit()
    return {"org": org_id, "sec": sec, "dev": dev, "tipo": tipo, "cliente": cliente,
            "con_area": con_area, "sin_area": sin_area}


def _crear(http_client, token, b, servicio, **extra):
    return http_client.post(
        f"{API}/projects/",
        headers=_auth(token),
        json={
            "organization_id": b["org"],
            "client_id": b["cliente"].id,
            "project_type_id": b["tipo"].id,
            "service_id": servicio.id,
            "name": "Proyecto por area",
            "status": "planning",
            **extra,
        },
    )


def test_sin_area_elegida_se_deriva_del_servicio(http_client, admin_token, base):
    r = _crear(http_client, admin_token, base, base["con_area"])
    assert r.status_code == 201, r.text
    assert r.json()["area_id"] == base["sec"].id


def test_el_area_elegida_manda_sobre_la_del_servicio(http_client, admin_token, base):
    r = _crear(http_client, admin_token, base, base["con_area"], area_id=base["dev"].id)
    assert r.status_code == 201, r.text
    assert r.json()["area_id"] == base["dev"].id


def test_con_servicio_sin_area_basta_con_elegirla(http_client, admin_token, base):
    r = _crear(http_client, admin_token, base, base["sin_area"], area_id=base["dev"].id)
    assert r.status_code == 201, r.text
    assert r.json()["area_id"] == base["dev"].id


def test_un_area_de_otra_organizacion_da_404(http_client, admin_token, base, db):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    ajena = Area(organization_id=org.id, name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(ajena)
    db.commit()
    r = _crear(http_client, admin_token, base, base["con_area"], area_id=ajena.id)
    assert r.status_code == 404, r.text
