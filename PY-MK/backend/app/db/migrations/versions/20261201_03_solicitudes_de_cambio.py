"""Solicitudes de cambio como tipo de ticket (35-P-03).

Un ticket es una incidencia o un cambio. El cambio se estima, el cliente lo
aprueba o lo rechaza, y el admin lo convierte en tareas de un proyecto. Los
tickets existentes quedan como "incidencia", que es lo que son. Bajar borra
solo estas columnas.

Revision ID: 20261201_03
Revises: 20261201_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261201_03"
# Al integrar con 35-P-02 (20261201_02) esta revisión pasa a colgar de ella.
down_revision: str | None = "20261201_01"
branch_labels = None
depends_on = None

_COLUMNAS = (
    "converted_project_id", "client_decision_at", "client_decision_by", "client_decision_note",
    "client_decision", "estimated_at", "estimated_by", "estimate_note", "estimate_hours", "system_id", "kind",
)


def upgrade() -> None:
    op.add_column("support_tickets", sa.Column("kind", sa.String(12), nullable=False, server_default="incidencia"))
    op.add_column(
        "support_tickets",
        sa.Column("system_id", sa.Integer(), sa.ForeignKey("client_systems.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("support_tickets", sa.Column("estimate_hours", sa.Numeric(7, 2), nullable=True))
    op.add_column("support_tickets", sa.Column("estimate_note", sa.String(1000), nullable=True))
    op.add_column("support_tickets", sa.Column("estimated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("support_tickets", sa.Column("estimated_at", sa.DateTime(), nullable=True))
    op.add_column("support_tickets", sa.Column("client_decision", sa.String(20), nullable=True))
    op.add_column("support_tickets", sa.Column("client_decision_note", sa.String(1000), nullable=True))
    op.add_column(
        "support_tickets", sa.Column("client_decision_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True)
    )
    op.add_column("support_tickets", sa.Column("client_decision_at", sa.DateTime(), nullable=True))
    op.add_column(
        "support_tickets",
        sa.Column("converted_project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"),
                  nullable=True),
    )
    op.create_index("ix_support_tickets_system_id", "support_tickets", ["system_id"])
    op.create_check_constraint("ck_support_tickets_kind", "support_tickets", "kind IN ('incidencia', 'cambio')")
    op.create_check_constraint(
        "ck_support_tickets_estimate_hours", "support_tickets", "estimate_hours IS NULL OR estimate_hours > 0"
    )
    op.create_check_constraint(
        "ck_support_tickets_client_decision",
        "support_tickets",
        "client_decision IS NULL OR client_decision IN ('approved', 'rejected')",
    )


def downgrade() -> None:
    for nombre in ("ck_support_tickets_client_decision", "ck_support_tickets_estimate_hours",
                   "ck_support_tickets_kind"):
        op.drop_constraint(nombre, "support_tickets", type_="check")
    op.drop_index("ix_support_tickets_system_id", table_name="support_tickets")
    for columna in _COLUMNAS:
        op.drop_column("support_tickets", columna)
