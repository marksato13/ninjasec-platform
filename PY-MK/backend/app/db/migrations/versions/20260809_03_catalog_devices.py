"""Tabla catalog_devices — catálogo de equipos (29-P1)

Revision ID: 20260809_03
Revises: 20260809_02
"""

import sqlalchemy as sa
from alembic import op

revision = "20260809_03"
down_revision = "20260809_02"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("catalog_devices"):
        op.create_table(
            "catalog_devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("brand", sa.String(length=80), nullable=False),
            sa.Column("model", sa.String(length=120), nullable=False),
            sa.Column("category", sa.String(length=30), nullable=False),
            sa.Column("subcategory", sa.String(length=30), nullable=True),
            sa.Column("osi_layer", sa.String(length=10), nullable=True),
            sa.Column("segment", sa.String(length=20), nullable=True),
            sa.Column("port_count", sa.Integer(), nullable=True),
            sa.Column("port_speed", sa.String(length=30), nullable=True),
            sa.Column("poe", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("poe_budget_w", sa.Integer(), nullable=True),
            sa.Column("stackable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("rack_mountable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("managed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("switching_capacity_gbps", sa.Float(), nullable=True),
            sa.Column("throughput_mbps", sa.Integer(), nullable=True),
            sa.Column("power_consumption_w", sa.Integer(), nullable=True),
            sa.Column("lifecycle_status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("eos_date", sa.Date(), nullable=True),
            sa.Column("eol_date", sa.Date(), nullable=True),
            sa.Column("price_range_usd", sa.String(length=40), nullable=True),
            sa.Column("use_cases", sa.String(length=500), nullable=True),
            sa.Column("tags", sa.String(length=300), nullable=True),
            sa.Column("datasheet_url", sa.String(length=500), nullable=True),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.UniqueConstraint("slug", name="uq_catalog_devices_slug"),
        )


def downgrade() -> None:
    if _has_table("catalog_devices"):
        op.drop_table("catalog_devices")
