"""Catálogo de reglas de hardening técnico (31-P1).

Revision ID: 20260809_10
Revises: 20260809_09
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_10"
down_revision = "20260809_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hardening_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("verification_method", sa.String(10), nullable=False),
        sa.Column("check_key", sa.String(60), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("hardening_rules")
