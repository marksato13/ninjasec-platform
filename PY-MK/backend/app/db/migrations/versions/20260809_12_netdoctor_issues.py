"""Catálogo de problemas comunes de networking (28-P1, NetDoctor).

Revision ID: 20260809_12
Revises: 20260809_11
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_12"
down_revision = "20260809_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "netdoctor_issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("probable_causes", sa.Text(), nullable=False),
        sa.Column("diagnostic_commands", sa.JSON(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("netdoctor_issues")
