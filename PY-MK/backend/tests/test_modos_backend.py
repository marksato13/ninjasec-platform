"""Lo que el backend aporta a los modos Ninja Sec / Ninja Dev (plan 34)."""

from __future__ import annotations

from uuid import uuid4

from app.core.navegacion import opcion
from app.db.models.area import Area
from app.db.models.service import Service
from tests.conftest import API


def test_la_guia_ninja_dev_esta_en_el_menu_del_equipo():
    o = opcion("staff", "/dashboard/ninja-dev")
    assert o is not None
    assert o.grupo == "Herramientas Ninja Dev"
    assert set(o.permitidas) == {"super_admin", "admin", "collaborator"}
    assert o.capsula is None


def test_el_catalogo_devuelve_el_area_de_cada_servicio(http_client, admin_token, db, seed_data):
    s = uuid4().hex[:8]
    area = Area(organization_id=seed_data["org"].id, name=f"Dev {s}", slug=f"dev-{s}", business_line="dev")
    db.add(area)
    db.flush()
    servicio = Service(organization_id=seed_data["org"].id, area_id=area.id, title=f"Web {s}", slug=f"web-{s}")
    db.add(servicio)
    db.commit()

    r = http_client.get(f"{API}/services/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text
    fila = next(x for x in r.json() if x["id"] == servicio.id)
    assert fila["area_id"] == area.id
