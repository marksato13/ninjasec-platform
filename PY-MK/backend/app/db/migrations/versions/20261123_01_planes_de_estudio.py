"""Planes de estudio: rutas de aprendizaje hacia una certificacion.

Cuatro tablas nuevas. Ninguna toca lo que ya existe, asi que bajar es seguro.

Decisiones que quedan fijadas aqui:

- `study_plans` y `study_enrollments` llevan `organization_id` PROPIO. No se
  deriva de `users` ni se cuelga de `recruitment`, que no tiene tenant y
  heredaria esa fuga.
- La unicidad del slug es COMPUESTA con la organizacion. `services.slug` era
  unica en toda la tabla y eso dejaba que una organizacion le bloqueara el
  nombre a otra, y de paso le confirmara que existe. No se repite.
- `study_progress.status` es String y no un Enum de PostgreSQL: anadir un
  valor a un Enum nativo exige otra migracion, y este conjunto todavia puede
  moverse. La validacion va en Pydantic.

Revision ID: 20261123_01
Revises: 20261121_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261123_01"
down_revision: str | None = "20261121_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("area", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_certification", sa.String(length=150), nullable=True),
        sa.Column("vendor", sa.String(length=80), nullable=True),
        sa.Column("exam_code", sa.String(length=40), nullable=True),
        sa.Column("estimated_hours", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_study_plans_organization_id_organizations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_study_plans"),
        sa.UniqueConstraint(
            "organization_id", "slug", name="uq_study_plan_org_slug"
        ),
    )
    op.create_index("ix_study_plans_org", "study_plans", ["organization_id"])

    op.create_table(
        "study_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("topics", sa.Text(), nullable=True),
        sa.Column("lab", sa.Text(), nullable=True),
        sa.Column("estimated_hours", sa.Integer(), nullable=True),
        sa.Column("weight_percent", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["study_plans.id"],
            name="fk_study_modules_plan_id_study_plans",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_study_modules"),
        sa.UniqueConstraint("plan_id", "position", name="uq_study_module_plan_pos"),
    )
    op.create_index("ix_study_modules_plan", "study_modules", ["plan_id"])

    op.create_table(
        "study_enrollments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("weekly_hours", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_study_enrollments_organization_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_study_enrollments_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["study_plans.id"],
            name="fk_study_enrollments_plan_id_study_plans",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_study_enrollments"),
        sa.UniqueConstraint(
            "user_id", "plan_id", name="uq_study_enrollment_user_plan"
        ),
    )
    op.create_index(
        "ix_study_enrollments_org", "study_enrollments", ["organization_id"]
    )
    op.create_index("ix_study_enrollments_user", "study_enrollments", ["user_id"])
    op.create_index("ix_study_enrollments_plan", "study_enrollments", ["plan_id"])

    op.create_table(
        "study_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enrollment_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("hours_spent", sa.Integer(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("validated_by", sa.Integer(), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["study_enrollments.id"],
            name="fk_study_progress_enrollment_id_study_enrollments",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["study_modules.id"],
            name="fk_study_progress_module_id_study_modules",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["validated_by"],
            ["users.id"],
            name="fk_study_progress_validated_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_study_progress"),
        sa.UniqueConstraint(
            "enrollment_id",
            "module_id",
            name="uq_study_progress_enrollment_module",
        ),
    )
    op.create_index(
        "ix_study_progress_enrollment", "study_progress", ["enrollment_id"]
    )
    op.create_index("ix_study_progress_module", "study_progress", ["module_id"])


def downgrade() -> None:
    # En orden inverso: las hijas primero, o las claves foraneas lo impiden.
    op.drop_index("ix_study_progress_module", table_name="study_progress")
    op.drop_index("ix_study_progress_enrollment", table_name="study_progress")
    op.drop_table("study_progress")

    op.drop_index("ix_study_enrollments_plan", table_name="study_enrollments")
    op.drop_index("ix_study_enrollments_user", table_name="study_enrollments")
    op.drop_index("ix_study_enrollments_org", table_name="study_enrollments")
    op.drop_table("study_enrollments")

    op.drop_index("ix_study_modules_plan", table_name="study_modules")
    op.drop_table("study_modules")

    op.drop_index("ix_study_plans_org", table_name="study_plans")
    op.drop_table("study_plans")
