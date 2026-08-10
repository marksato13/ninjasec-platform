"""Caché de CVEs por producto (32-P1).

Revision ID: 20260809_11
Revises: 20260809_10
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_11"
down_revision = "20260809_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cve_inventory_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_key", sa.String(160), nullable=False, unique=True),
        sa.Column("cves_json", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("cve_inventory_cache")
