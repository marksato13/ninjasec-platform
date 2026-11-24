"""Menus editables por rol: una tabla de excepciones.

Una sola tabla nueva, `nav_visibility`. No toca nada de lo que ya existe, asi
que bajar es seguro: se pierde lo que se haya editado y el menu vuelve a los
valores por defecto del codigo.

Decisiones que quedan fijadas aqui:

- Solo se guardan las DIFERENCIAS respecto a los valores por defecto
  (`app/core/navegacion.py`). Una instalacion sin ediciones tiene la tabla
  vacia, y un cambio en los valores por defecto llega a quien no los toco.
- `organization_id` es NOT NULL y forma parte de la restriccion unica: cada
  organizacion edita sus menus sin ver los de otra.
- `surface` y `audience` son String y no Enum de PostgreSQL. Anadir una
  superficie o un rol a un Enum nativo exige otra migracion, y este conjunto
  todavia puede moverse. La validacion vive en `app/core/navegacion.py`.

Revision ID: 20261124_01
Revises: 20261123_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261124_01"
down_revision: str | None = "20261123_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nav_visibility",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("surface", sa.String(length=20), nullable=False),
        sa.Column("item_key", sa.String(length=120), nullable=False),
        sa.Column("audience", sa.String(length=20), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_nav_visibility_organization_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["users.id"],
            name="fk_nav_visibility_updated_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_nav_visibility"),
        sa.UniqueConstraint(
            "organization_id", "surface", "item_key", "audience",
            name="uq_nav_visibility_org_surface_item_audience",
        ),
    )
    op.create_index(
        "ix_nav_visibility_organization_id", "nav_visibility", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_nav_visibility_organization_id", table_name="nav_visibility")
    op.drop_table("nav_visibility")
