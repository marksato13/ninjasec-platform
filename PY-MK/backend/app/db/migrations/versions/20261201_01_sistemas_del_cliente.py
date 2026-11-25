"""Sistemas del cliente y sus entornos (35-P-01).

Dos tablas nuevas: la ficha de cada sistema que Ninja Dev entregó o mantiene,
y sus entornos dev/staging/prod. Sin secretos: solo dónde están. Bajar borra
solo estas dos tablas.

Revision ID: 20261201_01
Revises: 20261130_02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261201_01"
down_revision: str | None = "20261130_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_systems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("stack", sa.String(160), nullable=True),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("support_plan", sa.String(20), nullable=False),
        sa.Column("origin_project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('en_construccion', 'en_produccion', 'en_mantenimiento', 'retirado')",
            name="status",
        ),
        sa.CheckConstraint(
            "support_plan IN ('ninguno', 'basico', 'profesional', 'a_medida')",
            name="support_plan",
        ),
    )
    op.create_index("ix_client_systems_organization_id", "client_systems", ["organization_id"])
    op.create_index("ix_client_systems_client", "client_systems", ["organization_id", "client_id"])
    op.create_index("ix_client_systems_origin_project_id", "client_systems", ["origin_project_id"])

    op.create_table(
        "client_system_environments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("system_id", sa.Integer(), sa.ForeignKey("client_systems.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("hosting", sa.String(120), nullable=True),
        sa.Column("domain_expires_at", sa.Date(), nullable=True),
        sa.Column("certificate_expires_at", sa.Date(), nullable=True),
        sa.Column("secrets_location", sa.String(300), nullable=True),
        sa.Column("visible_to_client", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("kind IN ('dev', 'staging', 'prod')", name="kind"),
        sa.UniqueConstraint("system_id", "kind", name="uq_client_system_environments_kind"),
    )
    op.create_index("ix_client_system_environments_organization_id", "client_system_environments",
                    ["organization_id"])
    op.create_index("ix_client_system_environments_system_id", "client_system_environments", ["system_id"])


def downgrade() -> None:
    op.drop_index("ix_client_system_environments_system_id", table_name="client_system_environments")
    op.drop_index("ix_client_system_environments_organization_id", table_name="client_system_environments")
    op.drop_table("client_system_environments")
    op.drop_index("ix_client_systems_origin_project_id", table_name="client_systems")
    op.drop_index("ix_client_systems_client", table_name="client_systems")
    op.drop_index("ix_client_systems_organization_id", table_name="client_systems")
    op.drop_table("client_systems")
