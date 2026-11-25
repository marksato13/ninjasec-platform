"""Ventanas de trabajo: el cliente autoriza por escrito antes de tocar su infraestructura.

Auditoria funcional del 2026-11-25 (C2). Tabla nueva; no toca datos existentes, asi que
subir y bajar son seguros (bajar borra solo las ventanas registradas).

Revision ID: 20261128_02
Revises: 20261128_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261128_02"
down_revision: str | None = "20261128_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_windows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=False),
        sa.Column("systems_affected", sa.String(500), nullable=True),
        sa.Column("impact", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("rollback_plan", sa.Text(), nullable=False),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column(
            "client_decision_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("client_decision_at", sa.DateTime(), nullable=True),
        sa.Column("client_comment", sa.String(1000), nullable=True),
        sa.Column("execution_note", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_work_windows_org", "work_windows", ["organization_id"])
    op.create_index("ix_work_windows_project", "work_windows", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_work_windows_project", table_name="work_windows")
    op.drop_index("ix_work_windows_org", table_name="work_windows")
    op.drop_table("work_windows")
