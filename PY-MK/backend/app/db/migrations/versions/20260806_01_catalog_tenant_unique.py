"""Unicidad de catalogos compuesta con organization_id (20-P-09).

`areas.name`, `areas.slug`, `project_types.name`, `project_types.slug` y
`products.slug` eran UNIQUE globales pese a que las tres tablas llevan
`organization_id`. La primera organizacion que creaba un area "Redes" se
la quedaba: ninguna otra podia tener la suya.

Sustituye esas restricciones por otras compuestas con `organization_id`.

Revision ID: 20260806_01
Revises: e1d861bf2ce6
Create Date: 2026-08-06
"""

import sqlalchemy as sa
from alembic import op

revision = "20260806_01"
down_revision = "e1d861bf2ce6"
branch_labels = None
depends_on = None


# (tabla, columnas de la restriccion compuesta, nombre nuevo)
_COMPUESTAS = [
    ("areas", ["organization_id", "name"], "uq_area_org_name"),
    ("areas", ["organization_id", "slug"], "uq_area_org_slug"),
    ("project_types", ["organization_id", "name"], "uq_project_type_org_name"),
    ("project_types", ["organization_id", "slug"], "uq_project_type_org_slug"),
    ("products", ["organization_id", "slug"], "uq_product_org_slug"),
]

# Columnas cuya restriccion UNIQUE de una sola columna hay que retirar.
_ANTIGUAS = [
    ("areas", "name"),
    ("areas", "slug"),
    ("project_types", "name"),
    ("project_types", "slug"),
    ("products", "slug"),
]


def _drop_unique_de_columna(table: str, column: str) -> None:
    """Elimina la restriccion/indice UNIQUE de una sola columna.

    El nombre depende de como se creo la tabla: Alembic, `create_all` o
    SQL a mano generan nombres distintos. Se busca en el catalogo en vez
    de asumirlo, y si no aparece se sigue adelante: significa que esta
    base nunca la tuvo.
    """
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite no soporta DROP CONSTRAINT. Las bases de test se crean
        # desde los modelos ya corregidos, asi que no hay nada que quitar.
        return

    inspector = sa.inspect(bind)

    for uc in inspector.get_unique_constraints(table):
        if uc["column_names"] == [column]:
            op.drop_constraint(uc["name"], table, type_="unique")
            return

    # Algunos motores lo materializan como indice unico, no como constraint.
    for idx in inspector.get_indexes(table):
        if idx.get("unique") and idx["column_names"] == [column]:
            op.drop_index(idx["name"], table_name=table)
            return


def _existe_constraint(inspector, table: str, name: str) -> bool:
    return any(uc["name"] == name for uc in inspector.get_unique_constraints(table))


def upgrade() -> None:
    bind = op.get_bind()

    for table, column in _ANTIGUAS:
        _drop_unique_de_columna(table, column)

    inspector = sa.inspect(bind)
    for table, columns, name in _COMPUESTAS:
        if not _existe_constraint(inspector, table, name):
            op.create_unique_constraint(name, table, columns)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    for table, _columns, name in _COMPUESTAS:
        if _existe_constraint(inspector, table, name):
            op.drop_constraint(name, table, type_="unique")

    # Restaurar la unicidad global solo es seguro si no hay ya duplicados
    # entre organizaciones. Si los hay, esto falla — y es lo correcto:
    # es preferible un error a perder datos silenciosamente.
    for table, column in _ANTIGUAS:
        op.create_unique_constraint(f"uq_{table}_{column}", table, [column])
