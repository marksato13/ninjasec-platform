"""Tabla audits — auditorías formales COBIT/ISO 19011 (26-P1)

Revision ID: 20260809_05
Revises: 20260809_04
"""

import sqlalchemy as sa
from alembic import op

revision = "20260809_05"
down_revision = "20260809_04"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("audits"):
        op.create_table(
            "audits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=30), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("objective", sa.Text(), nullable=True),
            sa.Column("scope", sa.Text(), nullable=True),
            sa.Column("framework", sa.String(length=20), nullable=False),
            sa.Column("audit_type", sa.String(length=20), nullable=False),
            sa.Column("lead_auditor_id", sa.Integer(), nullable=False),
            sa.Column("planned_start", sa.Date(), nullable=True),
            sa.Column("planned_end", sa.Date(), nullable=True),
            sa.Column("actual_end", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
            sa.Column("opinion", sa.String(length=30), nullable=True),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.ForeignKeyConstraint(
                ["organization_id"], ["organizations.id"], ondelete="CASCADE",
                name="fk_audits_organization_id",
            ),
            sa.ForeignKeyConstraint(
                ["client_id"], ["clients.id"], ondelete="CASCADE",
                name="fk_audits_client_id",
            ),
            sa.ForeignKeyConstraint(
                ["lead_auditor_id"], ["users.id"],
                name="fk_audits_lead_auditor_id",
            ),
            sa.UniqueConstraint("organization_id", "code", name="uq_audits_organization_code"),
        )


def downgrade() -> None:
    if _has_table("audits"):
        op.drop_table("audits")
