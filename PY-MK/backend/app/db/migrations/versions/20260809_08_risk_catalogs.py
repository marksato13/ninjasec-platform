"""Catálogos reutilizables de amenazas/vulnerabilidades y su asociación N:N con riesgos (25-P2).

Revision ID: 20260809_08
Revises: 20260809_07
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_08"
down_revision = "20260809_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, constraint_name in (
        ("threats", "uq_threat_org_code"),
        ("vulnerabilities", "uq_vulnerability_org_code"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(40), nullable=False),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
            sa.UniqueConstraint("organization_id", "code", name=constraint_name),
        )
    op.create_table(
        "risk_threats",
        sa.Column("risk_id", sa.Integer(), primary_key=True),
        sa.Column("threat_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["risk_id"], ["risks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["threat_id"], ["threats.id"], ondelete="RESTRICT"),
    )
    op.create_table(
        "risk_vulnerabilities",
        sa.Column("risk_id", sa.Integer(), primary_key=True),
        sa.Column("vulnerability_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["risk_id"], ["risks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vulnerability_id"], ["vulnerabilities.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("risk_vulnerabilities")
    op.drop_table("risk_threats")
    op.drop_table("vulnerabilities")
    op.drop_table("threats")
