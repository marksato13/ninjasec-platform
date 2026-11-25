"""El catalogo de servicios solo muestra lo que cada quien debe ver.

Revision del portal del 2026-11-25 (Codex): `GET /services` devolvia todos los
servicios de TODAS las organizaciones, incluidos los inactivos y los no
publicos, a cualquiera, con o sin sesion.
"""

from __future__ import annotations

from uuid import uuid4

from app.db.models.organization import Organization
from app.db.models.service import Service
from tests.conftest import API


def _servicio(db, organization_id: int, *, activo: bool = True, publico: bool = True) -> Service:
    s = uuid4().hex[:8]
    servicio = Service(
        organization_id=organization_id,
        title=f"Servicio {s}",
        slug=f"servicio-{s}",
        active=activo,
        is_public=publico,
    )
    db.add(servicio)
    db.commit()
    return servicio


def _ids(respuesta) -> set[int]:
    assert respuesta.status_code == 200, respuesta.text
    return {item["id"] for item in respuesta.json()}


def _escenario(db, seed_data):
    otra = Organization(name=f"Otra {uuid4().hex[:8]}", slug=f"otra-{uuid4().hex[:8]}")
    db.add(otra)
    db.commit()
    org = seed_data["org"].id
    return {
        "publico": _servicio(db, org),
        "inactivo": _servicio(db, org, activo=False),
        "privado": _servicio(db, org, publico=False),
        "ajeno": _servicio(db, otra.id),
    }


def test_sin_sesion_solo_activos_y_publicos(http_client, db, seed_data):
    e = _escenario(db, seed_data)
    ids = _ids(http_client.get(f"{API}/services/"))
    assert e["publico"].id in ids
    assert e["inactivo"].id not in ids
    assert e["privado"].id not in ids


def test_el_staff_ve_toda_su_organizacion_y_nada_ajeno(http_client, admin_token, db, seed_data):
    e = _escenario(db, seed_data)
    ids = _ids(http_client.get(f"{API}/services/", headers={"Authorization": f"Bearer {admin_token}"}))
    assert {e["publico"].id, e["inactivo"].id, e["privado"].id} <= ids
    assert e["ajeno"].id not in ids


def test_un_token_invalido_se_trata_como_anonimo(http_client, db, seed_data):
    e = _escenario(db, seed_data)
    ids = _ids(http_client.get(f"{API}/services/", headers={"Authorization": "Bearer no-vale"}))
    assert e["inactivo"].id not in ids
    assert e["privado"].id not in ids
