"""Caché de reputación externa de IPs (30-P2).

Revision ID: 20260809_09
Revises: 20260809_08
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_09"
down_revision = "20260809_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ip_reputation_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("checked_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("ip_address", "source", name="uq_ip_reputation_ip_source"),
    )


def downgrade() -> None:
    op.drop_table("ip_reputation_cache")
