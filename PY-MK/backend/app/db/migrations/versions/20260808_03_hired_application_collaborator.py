"""Convierte postulaciones contratadas en colaboradores (15-P-01).

Revision ID: 20260808_03
Revises: 20260808_02
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_03"
down_revision = "20260808_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "collaborator_profiles", sa.Column("phone", sa.String(50), nullable=True)
    )
    op.add_column(
        "collaborator_profiles", sa.Column("cv_url", sa.String(255), nullable=True)
    )
    op.add_column(
        "collaborator_profiles",
        sa.Column("source_application_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_collaborator_profiles_source_application_id_job_applications",
        "collaborator_profiles",
        "job_applications",
        ["source_application_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_collaborator_profiles_source_application_id",
        "collaborator_profiles",
        ["source_application_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_collaborator_profiles_source_application_id",
        "collaborator_profiles",
        type_="unique",
    )
    op.drop_constraint(
        "fk_collaborator_profiles_source_application_id_job_applications",
        "collaborator_profiles",
        type_="foreignkey",
    )
    op.drop_column("collaborator_profiles", "source_application_id")
    op.drop_column("collaborator_profiles", "cv_url")
    op.drop_column("collaborator_profiles", "phone")
