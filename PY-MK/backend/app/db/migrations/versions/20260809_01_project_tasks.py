"""Tabla project_tasks (22-P-01)

Revision ID: 20260809_01
Revises: 20260808_04
"""

import sqlalchemy as sa
from alembic import op

revision = "20260809_01"
down_revision = "20260808_04"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("project_tasks"):
        status_enum = sa.Enum(
            "PENDING", "IN_PROGRESS", "DONE", name="project_task_status_enum"
        )
        op.create_table(
            "project_tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("assigned_user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column(
                "status",
                status_enum,
                nullable=False,
                server_default="PENDING",
            ),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
            sa.ForeignKeyConstraint(
                ["organization_id"], ["organizations.id"], ondelete="CASCADE",
                name="fk_project_tasks_organization_id_organizations",
            ),
            sa.ForeignKeyConstraint(
                ["project_id"], ["projects.id"], ondelete="CASCADE",
                name="fk_project_tasks_project_id_projects",
            ),
            sa.ForeignKeyConstraint(
                ["assigned_user_id"], ["users.id"], ondelete="CASCADE",
                name="fk_project_tasks_assigned_user_id_users",
            ),
        )


def downgrade() -> None:
    if _has_table("project_tasks"):
        op.drop_table("project_tasks")
