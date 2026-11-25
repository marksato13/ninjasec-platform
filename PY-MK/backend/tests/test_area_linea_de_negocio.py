"""Cada area declara su linea de negocio: Ninja Sec, Ninja Dev o las dos.

Plan 34 (modos Ninja Sec y Ninja Dev). Antes el panel adivinaba la linea por el
texto del slug.
"""

from __future__ import annotations

import importlib
from uuid import uuid4

from sqlalchemy import inspect

from app.db.models.area import Area
from tests.conftest import API

MIGRACION = "app.db.migrations.versions.20261128_03_linea_de_negocio_por_area"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _crear(http_client, token, **cuerpo):
    cuerpo.setdefault("name", f"Area {uuid4().hex[:8]}")
    return http_client.post(f"{API}/areas", json=cuerpo, headers=_auth(token))


def test_crear_con_linea_y_leerla(http_client, admin_token):
    r = _crear(http_client, admin_token, business_line="dev")
    assert r.status_code == 201, r.text
    assert r.json()["business_line"] == "dev"


def test_sin_linea_queda_vacia(http_client, admin_token):
    r = _crear(http_client, admin_token)
    assert r.status_code == 201, r.text
    assert r.json()["business_line"] is None


def test_cambiar_y_vaciar_la_linea(http_client, admin_token):
    area = _crear(http_client, admin_token, business_line="sec").json()
    r = http_client.put(f"{API}/areas/{area['id']}", json={"business_line": "dev"}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["business_line"] == "dev"
    r = http_client.put(f"{API}/areas/{area['id']}", json={"business_line": None}, headers=_auth(admin_token))
    assert r.json()["business_line"] is None


def test_editar_otro_campo_no_borra_la_linea(http_client, admin_token):
    area = _crear(http_client, admin_token, business_line="sec").json()
    r = http_client.put(f"{API}/areas/{area['id']}", json={"name": f"Renombrada {uuid4().hex[:6]}"}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["business_line"] == "sec"


def test_una_linea_desconocida_da_422(http_client, admin_token):
    assert _crear(http_client, admin_token, business_line="marketing").status_code == 422


def test_el_colaborador_no_puede_cambiarla(http_client, admin_token, collaborator_token):
    area = _crear(http_client, admin_token, business_line="sec").json()
    r = http_client.put(f"{API}/areas/{area['id']}", json={"business_line": "dev"}, headers=_auth(collaborator_token))
    assert r.status_code in (403, 404)


def test_la_migracion_encadena_con_ventanas_de_trabajo():
    m = importlib.import_module(MIGRACION)
    assert m.down_revision == "20261128_02"


def test_la_columna_coincide_con_el_modelo():
    col = Area.__table__.c.business_line
    assert col.nullable is True
    assert col.type.length == 10
    assert "business_line" in {c.key for c in inspect(Area).columns}
