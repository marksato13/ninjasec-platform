"""El slug de un servicio es unico POR ORGANIZACION, no globalmente.

`services.slug` tenia `unique=True` de una sola columna sobre una tabla con
`organization_id NOT NULL`. Consecuencia: el primer cliente que creara el
servicio "pentest-web" se quedaba ese slug para toda la plataforma, y
ninguna otra organizacion podia volver a usarlo nunca.

Es el mismo fallo que la migracion 20260806_01 corrigio para `areas`,
`project_types` y `products`, y al que `services` se le paso.

Estos tests validan el MODELO (`__table_args__`), que es lo que define la
restriccion. La migracion `20261121_01` la aplica sobre PostgreSQL; eso lo
cubre `test_alembic_bootstrap.py` contra un motor real.
"""

from sqlalchemy import UniqueConstraint

from app.db.models.service import Service


def _restricciones_unicas(modelo) -> list[UniqueConstraint]:
    return [c for c in modelo.__table__.constraints if isinstance(c, UniqueConstraint)]


def test_el_slug_no_tiene_unicidad_global():
    """Un `unique=True` en la columna seria el bug original."""
    assert Service.__table__.c.slug.unique is not True, (
        "services.slug volvio a ser unico globalmente: el segundo cliente no "
        "podra dar de alta un servicio con un slug que ya use el primero"
    )


def test_existe_la_unicidad_compuesta_con_organizacion():
    combinaciones = [
        tuple(c.name for c in r.columns) for r in _restricciones_unicas(Service)
    ]
    assert ("organization_id", "slug") in combinaciones, (
        f"Falta UniqueConstraint(organization_id, slug). Hay: {combinaciones}"
    )


def test_ninguna_restriccion_unica_es_solo_el_slug():
    for r in _restricciones_unicas(Service):
        columnas = [c.name for c in r.columns]
        assert columnas != ["slug"], (
            f"La restriccion {r.name} vuelve a hacer el slug global"
        )


def test_la_misma_regla_se_cumple_en_los_otros_catalogos_multitenant():
    """Vigila que no se repita el olvido en los que ya estaban bien.

    `areas`, `project_types` y `products` se arreglaron en 20260806_01. Si
    alguien reintroduce un unique de una sola columna en cualquiera de
    ellos, esta prueba lo caza.
    """
    from app.db.models.area import Area
    from app.db.models.product import Product
    from app.db.models.project_type import ProjectType

    for modelo in (Area, ProjectType, Product, Service):
        for restriccion in _restricciones_unicas(modelo):
            columnas = [c.name for c in restriccion.columns]
            if "organization_id" in columnas:
                continue
            assert columnas not in (["slug"], ["name"]), (
                f"{modelo.__tablename__}.{columnas} es unico sin incluir "
                "organization_id: bloquea al segundo tenant"
            )
