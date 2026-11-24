"""Seguimiento de proyectos: fase, bitacora y equipos.

Dos tablas nuevas (`project_updates`, `project_devices`) y dos columnas (`projects.phase`,
`project_tasks.phase`). Bajar es seguro: se pierde la bitacora y la fase, y el resto sigue.

Decisiones que quedan fijadas aqui:

- `projects.phase` es NOT NULL con server_default 'diagnostico': los proyectos que ya
  existen reciben una fase sin que haya que rellenarla a mano, y el default vive en la
  base y no solo en el modelo, para que un INSERT directo tampoco se quede sin ella.
- `project_tasks.phase` es NULL: una tarea antigua no pertenece a ninguna fase conocida y
  no se inventa una.
- `project_updates` lleva `organization_id` propio y `visible_to_client`: lo que ve el
  cliente es una decision explicita, no un efecto secundario.
- `kind` y `phase` son String, no Enum nativo: anadir un valor a un Enum de PostgreSQL
  exige otra migracion.

Revision ID: 20261125_01
Revises: 20261124_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261125_01"
down_revision: str | None = "20261124_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("phase", sa.String(length=20), nullable=False, server_default="diagnostico"),
    )
    op.add_column("project_tasks", sa.Column("phase", sa.String(length=20), nullable=True))

    op.create_table(
        "project_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("phase", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("visible_to_client", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_project_updates_organization_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_project_updates_project_id_projects", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"], ["users.id"],
            name="fk_project_updates_author_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_updates"),
    )
    op.create_index("ix_project_updates_organization_id", "project_updates", ["organization_id"])
    op.create_index(
        "ix_project_updates_project_created", "project_updates", ["project_id", "created_at"]
    )

    op.create_table(
        "project_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_project_devices_project_id_projects", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"],
            name="fk_project_devices_device_id_devices", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_devices"),
        sa.UniqueConstraint("project_id", "device_id", name="uq_project_device"),
    )
    op.create_index("ix_project_devices_project_id", "project_devices", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_devices_project_id", table_name="project_devices")
    op.drop_table("project_devices")
    op.drop_index("ix_project_updates_project_created", table_name="project_updates")
    op.drop_index("ix_project_updates_organization_id", table_name="project_updates")
    op.drop_table("project_updates")
    op.drop_column("project_tasks", "phase")
    op.drop_column("projects", "phase")
