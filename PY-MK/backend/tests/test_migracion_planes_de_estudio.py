"""La migración de planes de estudio declara lo mismo que los modelos.

Esta prueba existe por un fallo concreto que ya ocurrió: una migración creó
23 índices que no estaban en los modelos. Lo cazó
`test_alembic_bootstrap`, pero ese necesita PostgreSQL de verdad y solo
corre en CI, así que el descuadre viajó hasta allí.

Aquí se comprueba **sin base de datos**: se ejecuta `upgrade()` contra un
`op` falso que anota las llamadas, y se compara lo anotado con
`Base.metadata`. Corre en cualquier sitio, en milisegundos, y falla donde se
escribe el error en lugar de tres pasos después.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from app.db import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.db.base import Base


MIGRACION = "app.db.migrations.versions.20261123_01_planes_de_estudio"

TABLAS = ("study_plans", "study_modules", "study_enrollments", "study_progress")


class _OpFalso:
    """Un `op` que no toca nada: solo apunta lo que le piden."""

    def __init__(self) -> None:
        self.tablas: dict[str, dict] = {}
        self.indices: list[tuple[str, str, tuple[str, ...]]] = []

    def create_table(self, nombre, *elementos, **_):
        columnas: dict[str, object] = {}
        unicas: list[tuple[str, tuple[str, ...]]] = []
        for elemento in elementos:
            clase = elemento.__class__.__name__
            if clase == "Column":
                columnas[elemento.name] = elemento
            elif clase == "UniqueConstraint":
                # Una restriccion que todavia NO esta unida a una Table guarda
                # sus columnas como cadenas en _pending_colargs; .columns esta
                # vacio. Leer solo .columns daba una tupla vacia y hacia que
                # esta prueba fallara por su propia culpa, no por la migracion.
                cols_unica = tuple(c.name for c in elemento.columns)
                if not cols_unica:
                    cols_unica = tuple(
                        c if isinstance(c, str) else c.name
                        for c in getattr(elemento, "_pending_colargs", ())
                    )
                unicas.append((elemento.name, cols_unica))
        self.tablas[nombre] = {"columnas": columnas, "unicas": unicas}

    def create_index(self, nombre, tabla, columnas, **_):
        self.indices.append((nombre, tabla, tuple(columnas)))

    def __getattr__(self, _nombre):  # pragma: no cover - cualquier otra llamada
        return lambda *a, **k: None


@pytest.fixture(scope="module")
def migracion_ejecutada() -> _OpFalso:
    modulo = importlib.import_module(MIGRACION)
    falso = _OpFalso()
    original = modulo.op
    modulo.op = falso
    try:
        modulo.upgrade()
    finally:
        modulo.op = original
    return falso


# --------------------------------------------------------------------------
# La cadena de revisiones
# --------------------------------------------------------------------------


def test_la_migracion_encadena_con_la_cabeza_anterior():
    modulo = importlib.import_module(MIGRACION)

    assert modulo.revision == "20261123_01"
    assert modulo.down_revision == "20261121_01", (
        "Si esto falla, la cadena se partió: habrá dos cabezas y Alembic se "
        "negará a aplicar nada."
    )


def test_hay_una_sola_cabeza():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cabezas = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()

    assert len(cabezas) == 1, f"Alembic tiene varias cabezas: {cabezas}"


# --------------------------------------------------------------------------
# Migración frente a modelos
# --------------------------------------------------------------------------


def test_crea_exactamente_las_cuatro_tablas(migracion_ejecutada):
    assert set(migracion_ejecutada.tablas) == set(TABLAS)


@pytest.mark.parametrize("tabla", TABLAS)
def test_las_columnas_coinciden_con_el_modelo(migracion_ejecutada, tabla):
    del_modelo = set(Base.metadata.tables[tabla].columns.keys())
    de_la_migracion = set(migracion_ejecutada.tablas[tabla]["columnas"])

    faltan = del_modelo - de_la_migracion
    sobran = de_la_migracion - del_modelo

    assert not faltan, f"{tabla}: el modelo tiene columnas que la migración no crea: {sorted(faltan)}"
    assert not sobran, f"{tabla}: la migración crea columnas que el modelo no tiene: {sorted(sobran)}"


@pytest.mark.parametrize("tabla", TABLAS)
def test_la_nulabilidad_coincide(migracion_ejecutada, tabla):
    """Una columna NOT NULL en el modelo y nullable en la migración revienta
    al insertar, no al migrar. Es de las que se descubren tarde."""
    modelo = Base.metadata.tables[tabla]
    migracion = migracion_ejecutada.tablas[tabla]["columnas"]

    discrepancias = [
        (c.name, c.nullable, migracion[c.name].nullable)
        for c in modelo.columns
        if c.name in migracion and c.nullable != migracion[c.name].nullable
    ]

    assert not discrepancias, (
        f"{tabla}: nulabilidad distinta entre modelo y migración "
        f"(columna, modelo, migración): {discrepancias}"
    )


def test_los_indices_coinciden(migracion_ejecutada):
    """El fallo exacto que ya ocurrió: índices en la migración y no en los
    modelos. Se comprueba en los dos sentidos."""
    de_la_migracion = {
        (nombre, tabla) for nombre, tabla, _ in migracion_ejecutada.indices
    }
    del_modelo = {
        (idx.name, tabla)
        for tabla in TABLAS
        for idx in Base.metadata.tables[tabla].indexes
    }

    assert de_la_migracion == del_modelo, (
        "Índices descuadrados.\n"
        f"  Solo en la migración: {sorted(de_la_migracion - del_modelo)}\n"
        f"  Solo en los modelos:  {sorted(del_modelo - de_la_migracion)}"
    )


def test_las_restricciones_unicas_coinciden(migracion_ejecutada):
    de_la_migracion = {
        (nombre, columnas)
        for tabla in TABLAS
        for nombre, columnas in migracion_ejecutada.tablas[tabla]["unicas"]
    }
    del_modelo = {
        (con.name, tuple(c.name for c in con.columns))
        for tabla in TABLAS
        for con in Base.metadata.tables[tabla].constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }

    assert de_la_migracion == del_modelo, (
        "Restricciones únicas descuadradas.\n"
        f"  Solo en la migración: {sorted(de_la_migracion - del_modelo)}\n"
        f"  Solo en los modelos:  {sorted(del_modelo - de_la_migracion)}"
    )


# --------------------------------------------------------------------------
# Decisiones de diseño que no se pueden perder en un refactor
# --------------------------------------------------------------------------


def test_el_slug_es_unico_por_organizacion_no_globalmente():
    """`services.slug` era única en toda la tabla y eso dejaba que una
    organización le bloqueara el nombre a otra, confirmándole de paso que
    existe. Aquí se fija que no se repita."""
    constraints = {
        con.name: tuple(c.name for c in con.columns)
        for con in Base.metadata.tables["study_plans"].constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }

    assert constraints.get("uq_study_plan_org_slug") == ("organization_id", "slug"), (
        "El slug del plan debe ser único POR ORGANIZACIÓN, no globalmente."
    )
    assert not any(
        columnas == ("slug",) for columnas in constraints.values()
    ), "Hay una unicidad global sobre slug: es exactamente el fallo de services.slug."


def test_las_tablas_con_tenant_llevan_organization_id_propio():
    """No derivado por clave foránea.

    `recruitment` no tiene `organization_id` y por eso los datos de los
    candidatos son globales. Colgar el plan de estudio de ahí habría heredado
    esa fuga; estas tablas llevan el suyo.
    """
    for tabla in ("study_plans", "study_enrollments"):
        columnas = Base.metadata.tables[tabla].columns.keys()
        assert "organization_id" in columnas, (
            f"{tabla} no tiene organization_id propio"
        )


def test_las_tablas_hijas_se_borran_en_cascada():
    """Borrar un plan no puede dejar módulos huérfanos ni reventar con un 500.

    Es el mismo fallo que hoy impide borrar un usuario: claves foráneas sin
    `ondelete`.
    """
    esperado = {
        ("study_modules", "plan_id"),
        ("study_progress", "enrollment_id"),
        ("study_progress", "module_id"),
    }

    sin_cascada = []
    for tabla, columna in esperado:
        for fk in Base.metadata.tables[tabla].foreign_keys:
            if fk.parent.name == columna and fk.ondelete != "CASCADE":
                sin_cascada.append((tabla, columna, fk.ondelete))

    assert not sin_cascada, (
        f"Claves foráneas sin ON DELETE CASCADE: {sin_cascada}"
    )
