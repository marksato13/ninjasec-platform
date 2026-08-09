"""Guarda el motivo de rechazo de skills y certificaciones (17-P-02).

Revision ID: 20260808_04
Revises: 20260808_03
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_04"
down_revision = "20260808_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_skills", sa.Column("rejection_reason", sa.String(500), nullable=True)
    )
    op.add_column(
        "user_certifications",
        sa.Column("rejection_reason", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_certifications", "rejection_reason")
    op.drop_column("user_skills", "rejection_reason")
