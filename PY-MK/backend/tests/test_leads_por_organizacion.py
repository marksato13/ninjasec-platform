"""Los leads son de una organizacion (auditoria de seguridad 2026-11-25, A4).

Antes `leads` no tenia `organization_id` y `GET /leads` devolvia todos: el admin de
cualquier organizacion veia, editaba, borraba y convertia los leads de las demas.
"""

from __future__ import annotations

import importlib
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models.enums import LeadStatus
from app.db.models.lead import Lead
from app.db.models.organization import Organization
from tests.conftest import API

MIGRACION = "app.db.migrations.versions.20261127_01_leads_por_organizacion"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def lead_ajeno(db):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    lead = Lead(
        organization_id=org.id,
        contact_name="Persona Ajena",
        email="ajena@example.com",
        status=LeadStatus.NEW,
    )
    db.add(lead)
    db.commit()
    return lead


def test_el_listado_no_incluye_leads_de_otra_organizacion(http_client, admin_token, lead_ajeno):
    r = http_client.get(f"{API}/leads/", headers=_auth(admin_token))
    assert r.status_code == 200
    assert lead_ajeno.id not in {x["id"] for x in r.json()}, "El listado expone leads de otra organizacion"


@pytest.mark.parametrize(
    ("metodo", "sufijo", "cuerpo"),
    [
        ("put", "", {"contact_name": "Secuestrado"}),
        ("patch", "", {"status": "CONTACTED"}),
        ("post", "/convert", None),
    ],
)
def test_un_lead_ajeno_no_existe_para_este_admin(http_client, admin_token, lead_ajeno, db, metodo, sufijo, cuerpo):
    kwargs = {"headers": _auth(admin_token)}
    if cuerpo is not None:
        kwargs["json"] = cuerpo
    r = getattr(http_client, metodo)(f"{API}/leads/{lead_ajeno.id}{sufijo}", **kwargs)
    assert r.status_code == 404, f"{metodo.upper()} {sufijo or '/'} sobre un lead ajeno devolvio {r.status_code}"
    db.expire_all()
    sigue = db.get(Lead, lead_ajeno.id)
    assert sigue is not None and sigue.contact_name == "Persona Ajena" and sigue.converted_client_id is None


def test_borrar_un_lead_ajeno_da_404_aunque_seas_super_admin(db, lead_ajeno, seed_data):
    """DELETE es solo de super_admin (sin token de prueba): se prueba en el servicio."""
    from types import SimpleNamespace

    from fastapi import HTTPException

    from app.modules.leads.services.lead_service import LeadService

    jefe = SimpleNamespace(id=seed_data["admin"].id, organization_id=seed_data["org"].id, role="super_admin")
    with pytest.raises(HTTPException) as e:
        LeadService(db, jefe).delete(lead_ajeno.id)
    assert e.value.status_code == 404
    assert db.get(Lead, lead_ajeno.id) is not None


def test_el_lead_publico_es_de_la_organizacion_duena_del_sitio(http_client, db):
    r = http_client.post(
        f"{API}/leads/",
        json={"contact_name": "Visitante", "email": "visitante@example.com", "message": "Hola"},
    )
    assert r.status_code == 201, r.text
    duena = db.scalar(select(func.min(Organization.id)))
    assert db.get(Lead, r.json()["id"]).organization_id == duena


# --- La migracion ------------------------------------------------------------


class _OpFalso:
    def __init__(self) -> None:
        self.pasos: list[tuple] = []

    def add_column(self, tabla, columna, **_):
        self.pasos.append(("add_column", tabla, columna.name, columna.nullable))

    def execute(self, sql, *_, **__):
        self.pasos.append(("execute", str(sql)))

    def alter_column(self, tabla, columna, **kw):
        self.pasos.append(("alter_column", tabla, columna, kw.get("nullable")))

    def __getattr__(self, nombre):
        return lambda *a, **k: self.pasos.append((nombre, *a))


def _pasos(funcion: str) -> list[tuple]:
    modulo = importlib.import_module(MIGRACION)
    falso, original = _OpFalso(), modulo.op
    modulo.op = falso
    try:
        getattr(modulo, funcion)()
    finally:
        modulo.op = original
    return falso.pasos


def test_la_migracion_encadena_con_la_cabeza_anterior():
    m = importlib.import_module(MIGRACION)
    assert (m.revision, m.down_revision) == ("20261127_01", "20261126_01")


def test_rellena_antes_de_exigir_el_valor():
    """Si `NOT NULL` fuera antes que el UPDATE, fallaria en cuanto haya un lead."""
    nombres = [p[0] for p in _pasos("upgrade")]
    assert nombres.index("add_column") < nombres.index("execute") < nombres.index("alter_column")
    alter = next(p for p in _pasos("upgrade") if p[0] == "alter_column")
    assert alter[3] is False


def test_la_columna_coincide_con_el_modelo():
    modelo = Base.metadata.tables["leads"].c.organization_id
    assert modelo.nullable is False
    assert {fk.column.table.name for fk in modelo.foreign_keys} == {"organizations"}


def test_bajar_quita_la_columna():
    assert ("drop_column", "leads", "organization_id") in _pasos("downgrade")
