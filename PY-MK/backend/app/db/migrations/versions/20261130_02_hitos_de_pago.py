"""Hitos de pago por proyecto (C3).

Tabla nueva: el admin registra cuanto se cobra en cada hito y en que estado esta;
el cliente lo ve. Sin pasarela ni datos bancarios. Bajar borra solo esta tabla.

Revision ID: 20261130_02
Revises: 20261130_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261130_02"
down_revision: str | None = "20261130_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'invoiced', 'paid')", name="ck_payment_milestones_status"),
        sa.CheckConstraint("currency IN ('PEN', 'USD')", name="ck_payment_milestones_currency"),
        sa.CheckConstraint("amount > 0", name="ck_payment_milestones_amount"),
    )
    op.create_index("ix_payment_milestones_organization_id", "payment_milestones", ["organization_id"])
    op.create_index("ix_payment_milestones_project", "payment_milestones", ["project_id", "due_date"])


def downgrade() -> None:
    op.drop_index("ix_payment_milestones_project", table_name="payment_milestones")
    op.drop_index("ix_payment_milestones_organization_id", table_name="payment_milestones")
    op.drop_table("payment_milestones")
