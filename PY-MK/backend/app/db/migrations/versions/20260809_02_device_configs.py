"""Tabla device_configs — Config Visualizer (23-P3)

Revision ID: 20260809_02
Revises: 20260809_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260809_02"
down_revision = "20260809_01"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("device_configs"):
        op.create_table(
            "device_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("device_id", sa.Integer(), nullable=False),
            sa.Column("vendor_detected", sa.String(length=30), nullable=False),
            sa.Column("raw_config", sa.Text(), nullable=True),
            sa.Column("parsed_json", sa.Text(), nullable=False),
            sa.Column("parse_warnings", sa.Text(), nullable=True),
            sa.Column("uploaded_by", sa.Integer(), nullable=False),
            sa.Column(
                "uploaded_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.ForeignKeyConstraint(
                ["device_id"], ["devices.id"], ondelete="CASCADE",
                name="fk_device_configs_device_id_devices",
            ),
            sa.ForeignKeyConstraint(
                ["uploaded_by"], ["users.id"], ondelete="CASCADE",
                name="fk_device_configs_uploaded_by_users",
            ),
        )


def downgrade() -> None:
    if _has_table("device_configs"):
        op.drop_table("device_configs")
