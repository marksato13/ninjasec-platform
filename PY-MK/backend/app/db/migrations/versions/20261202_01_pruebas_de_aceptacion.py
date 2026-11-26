"""Pruebas de aceptación (UAT) por proyecto (35-P-05).

Una tabla nueva. Bajar borra solo esa tabla.

Revision ID: 20261202_01
Revises: 20261201_03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261202_01"
down_revision: str | None = "20261201_03"
branch_labels = None
depends_on = None

_T = "acceptance_cases"


def upgrade() -> None:
    op.create_table(
        _T,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("steps", sa.Text(), nullable=False),
        sa.Column("expected", sa.Text(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("client_note", sa.String(1000), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('pendiente', 'aprobado', 'observado')", name="status"),
    )
    op.create_index(f"ix_{_T}_organization_id", _T, ["organization_id"])
    op.create_index(f"ix_{_T}_project", _T, ["project_id", "position"])


def downgrade() -> None:
    op.drop_index(f"ix_{_T}_project", table_name=_T)
    op.drop_index(f"ix_{_T}_organization_id", table_name=_T)
    op.drop_table(_T)
