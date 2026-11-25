"""Una solicitud de servicio se convierte en proyecto.

Auditoria funcional del 2026-11-25 (A6 y D6): la solicitud aprobada solo cambiaba de
estado; el proyecto se creaba a mano y nada los enlazaba. Columna nueva, opcional:
las solicitudes existentes quedan sin proyecto, que es lo que son.

Revision ID: 20261128_01
Revises: 20261127_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261128_01"
down_revision: str | None = "20261127_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("service_requests", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_service_requests_project_id",
        "service_requests",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_service_requests_project_id", "service_requests", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_service_requests_project_id", table_name="service_requests")
    op.drop_constraint("fk_service_requests_project_id", "service_requests", type_="foreignkey")
    op.drop_column("service_requests", "project_id")
