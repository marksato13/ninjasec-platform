"""Tablas de cumplimiento ISO 27001 (24-P1)

Revision ID: 20260809_04
Revises: 20260809_03
"""

import sqlalchemy as sa
from alembic import op

revision = "20260809_04"
down_revision = "20260809_03"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("compliance_frameworks"):
        op.create_table(
            "compliance_frameworks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("version", sa.String(length=20), nullable=False),
            sa.Column("slug", sa.String(length=60), nullable=False),
            sa.UniqueConstraint("slug", name="uq_compliance_frameworks_slug"),
        )

    if not _has_table("compliance_controls"):
        op.create_table(
            "compliance_controls",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("framework_id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=20), nullable=False),
            sa.Column("parent_code", sa.String(length=10), nullable=False),
            sa.Column("category", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=300), nullable=False),
            sa.ForeignKeyConstraint(
                ["framework_id"], ["compliance_frameworks.id"], ondelete="CASCADE",
                name="fk_compliance_controls_framework_id",
            ),
            sa.UniqueConstraint(
                "framework_id", "code", name="uq_compliance_control_framework_code"
            ),
        )

    if not _has_table("client_control_status"):
        op.create_table(
            "client_control_status",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("control_id", sa.Integer(), nullable=False),
            sa.Column("applicability", sa.String(length=20), nullable=False, server_default="applicable"),
            sa.Column("implementation_status", sa.String(length=20), nullable=False, server_default="not_implemented"),
            sa.Column("maturity_level", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("justification", sa.Text(), nullable=True),
            sa.Column("responsible_user_id", sa.Integer(), nullable=True),
            sa.Column("target_date", sa.Date(), nullable=True),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.ForeignKeyConstraint(
                ["client_id"], ["clients.id"], ondelete="CASCADE",
                name="fk_client_control_status_client_id",
            ),
            sa.ForeignKeyConstraint(
                ["control_id"], ["compliance_controls.id"], ondelete="CASCADE",
                name="fk_client_control_status_control_id",
            ),
            sa.ForeignKeyConstraint(
                ["responsible_user_id"], ["users.id"],
                name="fk_client_control_status_responsible_user_id",
            ),
            sa.UniqueConstraint(
                "client_id", "control_id", name="uq_client_control_status_pair"
            ),
        )


def downgrade() -> None:
    if _has_table("client_control_status"):
        op.drop_table("client_control_status")
    if _has_table("compliance_controls"):
        op.drop_table("compliance_controls")
    if _has_table("compliance_frameworks"):
        op.drop_table("compliance_frameworks")
