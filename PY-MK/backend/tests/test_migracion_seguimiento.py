"""La migracion del seguimiento de proyectos declara lo mismo que los modelos.

Mismo metodo que las otras pruebas de migracion: se ejecuta `upgrade()` contra un `op`
falso que apunta lo que le piden y se compara con `Base.metadata`, sin base de datos.
"""

from __future__ import annotations

import importlib

import pytest

from app.db import models  # noqa: F401
from app.db.base import Base

MIGRACION = "app.db.migrations.versions.20261125_01_seguimiento_de_proyectos"
TABLAS = ("project_updates", "project_devices")


class _OpFalso:
    def __init__(self) -> None:
        self.tablas: dict[str, dict] = {}
        self.columnas_nuevas: dict[tuple[str, str], object] = {}
        self.indices: list[tuple[str, str]] = []

    def add_column(self, tabla, columna, **_):
        self.columnas_nuevas[(tabla, columna.name)] = columna

    def create_table(self, nombre, *elementos, **_):
        cols, unicas = {}, []
        for e in elementos:
            clase = e.__class__.__name__
            if clase == "Column":
                cols[e.name] = e
            elif clase == "UniqueConstraint":
                c = tuple(x.name for x in e.columns) or tuple(
                    x if isinstance(x, str) else x.name for x in getattr(e, "_pending_colargs", ()))
                unicas.append((e.name, c))
        self.tablas[nombre] = {"columnas": cols, "unicas": unicas}

    def create_index(self, nombre, tabla, columnas, **_):
        self.indices.append((nombre, tabla))

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
    m = importlib.import_module(MIGRACION)
    assert (m.revision, m.down_revision) == ("20261125_01", "20261124_01")


def test_hay_una_sola_cabeza():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cabezas = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    assert len(cabezas) == 1, cabezas


def test_crea_las_dos_tablas(migracion):
    assert set(migracion.tablas) == set(TABLAS)


@pytest.mark.parametrize("tabla", TABLAS)
def test_las_columnas_coinciden_con_el_modelo(migracion, tabla):
    assert set(Base.metadata.tables[tabla].columns.keys()) == set(migracion.tablas[tabla]["columnas"])


@pytest.mark.parametrize("tabla", TABLAS)
def test_la_nulabilidad_coincide(migracion, tabla):
    en_migracion = migracion.tablas[tabla]["columnas"]
    malas = [(c.name, c.nullable, en_migracion[c.name].nullable)
             for c in Base.metadata.tables[tabla].columns if c.nullable != en_migracion[c.name].nullable]
    assert not malas, malas


def test_los_indices_coinciden(migracion):
    de_migracion = {i for i in migracion.indices}
    del_modelo = {(i.name, t) for t in TABLAS for i in Base.metadata.tables[t].indexes}
    assert de_migracion == del_modelo, (de_migracion ^ del_modelo)


def test_las_restricciones_unicas_coinciden(migracion):
    de_migracion = {x for t in TABLAS for x in migracion.tablas[t]["unicas"]}
    del_modelo = {(c.name, tuple(x.name for x in c.columns))
                  for t in TABLAS for c in Base.metadata.tables[t].constraints
                  if c.__class__.__name__ == "UniqueConstraint"}
    assert de_migracion == del_modelo


def test_las_columnas_nuevas_coinciden_con_los_modelos(migracion):
    fase_proyecto = migracion.columnas_nuevas[("projects", "phase")]
    fase_tarea = migracion.columnas_nuevas[("project_tasks", "phase")]
    assert fase_proyecto.nullable is False and Base.metadata.tables["projects"].c.phase.nullable is False
    assert fase_tarea.nullable is True and Base.metadata.tables["project_tasks"].c.phase.nullable is True


def test_los_proyectos_que_ya_existen_reciben_una_fase(migracion):
    """NOT NULL sin default tumbaria la migracion sobre una base con proyectos."""
    col = migracion.columnas_nuevas[("projects", "phase")]
    assert col.server_default is not None and str(col.server_default.arg) == "diagnostico"


def test_la_bitacora_lleva_organizacion_y_visibilidad(migracion):
    cols = migracion.tablas["project_updates"]["columnas"]
    assert cols["organization_id"].nullable is False
    assert cols["visible_to_client"].nullable is False
