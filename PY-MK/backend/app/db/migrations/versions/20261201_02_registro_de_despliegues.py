"""Registro de despliegues de los sistemas del cliente (35-P-02).

Una tabla nueva. Bajar borra solo esa tabla.

Revision ID: 20261201_02
Revises: 20261201_01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261201_02"
down_revision: str | None = "20261201_01"
branch_labels = None
depends_on = None

_T = "client_system_deployments"


def upgrade() -> None:
    op.create_table(
        _T,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("system_id", sa.Integer(), sa.ForeignKey("client_systems.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("environment_id", sa.Integer(),
                  sa.ForeignKey("client_system_environments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("environment_kind", sa.String(10), nullable=False),
        sa.Column("version", sa.String(60), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("deployed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("deployed_at", sa.DateTime(), nullable=False),
        sa.Column("backup_done", sa.Boolean(), nullable=False),
        sa.Column("smoke_test_passed", sa.Boolean(), nullable=False),
        sa.Column("rollback_plan_written", sa.Boolean(), nullable=False),
        sa.Column("rollback_plan", sa.String(500), nullable=True),
        sa.Column("result", sa.String(12), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_update_id", sa.Integer(),
                  sa.ForeignKey("project_updates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("result IN ('ok', 'fallido', 'revertido')", name="result"),
        sa.CheckConstraint("environment_kind IN ('dev', 'staging', 'prod')", name="environment_kind"),
    )
    op.create_index(f"ix_{_T}_organization_id", _T, ["organization_id"])
    op.create_index(f"ix_{_T}_system_id", _T, ["system_id"])
    op.create_index(f"ix_{_T}_environment_id", _T, ["environment_id"])
    op.create_index(f"ix_{_T}_project_id", _T, ["project_id"])
    op.create_index(f"ix_{_T}_system_at", _T, ["system_id", "deployed_at"])


def downgrade() -> None:
    for ix in ("system_at", "project_id", "environment_id", "system_id", "organization_id"):
        op.drop_index(f"ix_{_T}_{ix}", table_name=_T)
    op.drop_table(_T)
