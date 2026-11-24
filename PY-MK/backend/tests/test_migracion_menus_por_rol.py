"""La migración de los menús por rol declara lo mismo que el modelo.

Mismo método que `test_migracion_planes_de_estudio.py`, y por la misma razón:
`test_alembic_bootstrap` caza los descuadres, pero necesita PostgreSQL y solo
corre en CI. Aquí se ejecuta `upgrade()` contra un `op` falso que apunta lo
que le piden, y se compara con `Base.metadata`, sin base de datos.
"""

from __future__ import annotations

import importlib

import pytest

from app.db import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.db.base import Base

MIGRACION = "app.db.migrations.versions.20261124_01_menus_por_rol"
TABLA = "nav_visibility"


class _OpFalso:
    def __init__(self) -> None:
        self.tablas: dict[str, dict] = {}
        self.indices: list[tuple[str, str, tuple[str, ...]]] = []

    def create_table(self, nombre, *elementos, **_):
        columnas, unicas = {}, []
        for e in elementos:
            clase = e.__class__.__name__
            if clase == "Column":
                columnas[e.name] = e
            elif clase == "UniqueConstraint":
                # Aun sin unir a una Table, sus columnas estan en _pending_colargs.
                cols = tuple(c.name for c in e.columns) or tuple(
                    c if isinstance(c, str) else c.name
                    for c in getattr(e, "_pending_colargs", ())
                )
                unicas.append((e.name, cols))
        self.tablas[nombre] = {"columnas": columnas, "unicas": unicas}

    def create_index(self, nombre, tabla, columnas, **_):
        self.indices.append((nombre, tabla, tuple(columnas)))

    def __getattr__(self, _):
        return lambda *a, **k: None


@pytest.fixture(scope="module")
def migracion() -> _OpFalso:
    modulo = importlib.import_module(MIGRACION)
    falso, original = _OpFalso(), modulo.op
    modulo.op = falso
    try:
        modulo.upgrade()
    finally:
        modulo.op = original
    return falso


def test_encadena_con_la_cabeza_anterior():
    modulo = importlib.import_module(MIGRACION)
    assert modulo.revision == "20261124_01"
    assert modulo.down_revision == "20261123_01", "Si falla, la cadena se partió: dos cabezas."


def test_hay_una_sola_cabeza():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cabezas = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    assert len(cabezas) == 1, f"Alembic tiene varias cabezas: {cabezas}"


def test_crea_solo_la_tabla_de_excepciones(migracion):
    assert set(migracion.tablas) == {TABLA}


def test_las_columnas_coinciden_con_el_modelo(migracion):
    modelo = set(Base.metadata.tables[TABLA].columns.keys())
    assert modelo == set(migracion.tablas[TABLA]["columnas"])


def test_la_nulabilidad_coincide(migracion):
    en_migracion = migracion.tablas[TABLA]["columnas"]
    discrepancias = [
        (c.name, c.nullable, en_migracion[c.name].nullable)
        for c in Base.metadata.tables[TABLA].columns
        if c.nullable != en_migracion[c.name].nullable
    ]
    assert not discrepancias, discrepancias


def test_los_indices_coinciden(migracion):
    de_la_migracion = {(n, t) for n, t, _ in migracion.indices}
    del_modelo = {(i.name, TABLA) for i in Base.metadata.tables[TABLA].indexes}
    assert de_la_migracion == del_modelo


def test_la_unicidad_incluye_la_organizacion(migracion):
    """Sin `organization_id` en la restriccion, una organizacion le bloquearia
    el menu a otra, y de paso le confirmaria que existe."""
    (nombre, columnas), = migracion.tablas[TABLA]["unicas"]
    assert columnas == ("organization_id", "surface", "item_key", "audience")
    del_modelo = {
        (c.name, tuple(x.name for x in c.columns))
        for c in Base.metadata.tables[TABLA].constraints
        if c.__class__.__name__ == "UniqueConstraint"
    }
    assert (nombre, columnas) in del_modelo


def test_la_organizacion_es_obligatoria(migracion):
    assert migracion.tablas[TABLA]["columnas"]["organization_id"].nullable is False
