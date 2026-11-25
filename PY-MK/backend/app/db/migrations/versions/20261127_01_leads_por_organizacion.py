"""Cada lead pertenece a una organizacion.

Auditoria de seguridad del 2026-11-25 (A4): `leads` no tenia `organization_id` y
`GET /leads` devolvia todos, asi que el admin de cualquier organizacion veia, editaba y
convertia los leads (nombre, correo, telefono) de las demas.

Los leads llegan por el formulario publico del sitio, que es de la organizacion duena:
la primera que se creo (la de menor id). Los que ya existen se le asignan a ella.

Si hubiera leads y ninguna organizacion, el `NOT NULL` falla y la migracion entera se
deshace (en PostgreSQL el DDL es transaccional): no se pierde nada.
Bajar es seguro: se pierde la columna, no los leads.

Revision ID: 20261127_01
Revises: 20261126_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261127_01"
down_revision: str | None = "20261126_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE leads SET organization_id = (SELECT MIN(id) FROM organizations) "
        "WHERE organization_id IS NULL"
    )
    op.alter_column("leads", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_leads_organization_id", "leads", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_leads_org", "leads", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_leads_org", table_name="leads")
    op.drop_constraint("fk_leads_organization_id", "leads", type_="foreignkey")
    op.drop_column("leads", "organization_id")
