"""Umbrales de alertas configurables por organizacion (18-P-02, 20-P-05).

Revision ID: 20260808_02
Revises: 20260808_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_02"
down_revision = "20260808_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_alert_thresholds",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("overdue_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("no_review_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "overdue_days > 0",
            name="ck_organization_alert_thresholds_overdue_days_positive",
        ),
        sa.CheckConstraint(
            "no_review_days > 0",
            name="ck_organization_alert_thresholds_no_review_days_positive",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_alert_thresholds_organization_id_organizations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "organization_id", name="pk_organization_alert_thresholds"
        ),
    )


def downgrade() -> None:
    op.drop_table("organization_alert_thresholds")
