"""Decision del cliente sobre un documento entregado (C1).

El cliente aprueba un entregable o un acta, o pide cambios con un motivo. Hasta
ahora solo podia verlos. La decision es lo que cierra una fase y, mas adelante,
dispara el cobro de su hito.

Columnas nuevas y opcionales: los documentos existentes quedan "sin decision",
que es lo que son. Bajar borra solo estas columnas.

Revision ID: 20261130_01
Revises: 20261129_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261130_01"
down_revision: str | None = "20261129_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project_docs", sa.Column("client_decision", sa.String(20), nullable=True))
    op.add_column("project_docs", sa.Column("client_decision_note", sa.String(1000), nullable=True))
    op.add_column(
        "project_docs",
        sa.Column("client_decision_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column("project_docs", sa.Column("client_decision_at", sa.DateTime(), nullable=True))
    op.create_check_constraint(
        "ck_project_docs_client_decision",
        "project_docs",
        "client_decision IS NULL OR client_decision IN ('approved', 'changes_requested')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_project_docs_client_decision", "project_docs", type_="check")
    for columna in ("client_decision_at", "client_decision_by", "client_decision_note", "client_decision"):
        op.drop_column("project_docs", columna)
