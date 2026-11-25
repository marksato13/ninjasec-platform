"""La migracion del enlace lead -> cliente declara lo mismo que el modelo."""

from __future__ import annotations

import importlib

import pytest

from app.db import models  # noqa: F401
from app.db.base import Base

MIGRACION = "app.db.migrations.versions.20261126_01_lead_convertido"


class _OpFalso:
    def __init__(self) -> None:
        self.columnas: dict[tuple[str, str], object] = {}
        self.claves: list[tuple] = []
        self.quitadas: list[tuple] = []

    def add_column(self, tabla, columna, **_):
        self.columnas[(tabla, columna.name)] = columna

    def create_foreign_key(self, nombre, origen, destino, locales, remotas, **_):
        self.claves.append((nombre, origen, destino, tuple(locales), tuple(remotas)))

    def drop_constraint(self, nombre, tabla, **_):
        self.quitadas.append(("constraint", nombre, tabla))

    def drop_column(self, tabla, columna, **_):
        self.quitadas.append(("column", tabla, columna))

    def __getattr__(self, _):
        return lambda *a, **k: None


@pytest.fixture
def migracion():
    modulo = importlib.import_module(MIGRACION)
    falso, original = _OpFalso(), modulo.op
    modulo.op = falso
    try:
        modulo.upgrade()
        subida = (dict(falso.columnas), list(falso.claves))
        modulo.downgrade()
    finally:
        modulo.op = original
    return falso, subida


def test_encadena_con_la_cabeza_anterior():
    m = importlib.import_module(MIGRACION)
    assert (m.revision, m.down_revision) == ("20261126_01", "20261125_01")


def test_hay_una_sola_cabeza():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cabezas = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    assert len(cabezas) == 1, cabezas


def test_la_columna_coincide_con_el_modelo(migracion):
    _, (columnas, _) = migracion
    col = columnas[("leads", "converted_client_id")]
    modelo = Base.metadata.tables["leads"].c.converted_client_id
    assert col.nullable is True and modelo.nullable is True, "Los leads que ya existen no estan convertidos"


def test_apunta_a_clientes(migracion):
    _, (_, claves) = migracion
    assert claves == [("fk_leads_converted_client_id", "leads", "clients", ("converted_client_id",), ("id",))]
    fk = next(iter(Base.metadata.tables["leads"].c.converted_client_id.foreign_keys))
    assert fk.target_fullname == "clients.id"


def test_bajar_deshace_lo_que_subio(migracion):
    falso, _ = migracion
    assert ("constraint", "fk_leads_converted_client_id", "leads") in falso.quitadas
    assert ("column", "leads", "converted_client_id") in falso.quitadas
