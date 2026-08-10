"""Tablas catalog_device_links y catalog_device_summaries (29-P2)

Revision ID: 20260810_01
Revises: 20260809_12
"""

import sqlalchemy as sa
from alembic import op

revision = "20260810_01"
down_revision = "20260809_12"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("catalog_device_links"):
        op.create_table(
            "catalog_device_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "catalog_device_id",
                sa.Integer(),
                sa.ForeignKey("catalog_devices.id"),
                nullable=False,
            ),
            sa.Column("link_type", sa.String(length=30), nullable=False),
            sa.Column("url", sa.String(length=500), nullable=False),
            sa.Column("archive_url", sa.String(length=500), nullable=True),
            sa.Column("last_checked_at", sa.DateTime(), nullable=True),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
        )

    if not _has_table("catalog_device_summaries"):
        op.create_table(
            "catalog_device_summaries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "catalog_device_id",
                sa.Integer(),
                sa.ForeignKey("catalog_devices.id"),
                nullable=False,
            ),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("source_note", sa.String(length=300), nullable=True),
            sa.Column(
                "updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.UniqueConstraint(
                "catalog_device_id", name="uq_catalog_device_summaries_catalog_device_id"
            ),
        )


def downgrade() -> None:
    if _has_table("catalog_device_summaries"):
        op.drop_table("catalog_device_summaries")
    if _has_table("catalog_device_links"):
        op.drop_table("catalog_device_links")
