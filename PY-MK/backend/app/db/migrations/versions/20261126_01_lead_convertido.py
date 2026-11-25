"""Un lead convertido queda enlazado a su cliente.

La conversion ya existia, pero la hacia el navegador en dos pasos y el lead no quedaba
marcado: pulsar dos veces creaba dos clientes. Esta columna es lo que lo impide.

`leads.converted_client_id` es NULL: los leads que ya existen no estan convertidos, o no hay
forma de saberlo, y no se inventa un enlace. Bajar es seguro: se pierde el enlace, no los clientes.

Revision ID: 20261126_01
Revises: 20261125_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261126_01"
down_revision: str | None = "20261125_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("converted_client_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_leads_converted_client_id", "leads", "clients", ["converted_client_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_leads_converted_client_id", "leads", type_="foreignkey")
    op.drop_column("leads", "converted_client_id")
