"""Registro de riesgos ISO 27005 (25-P1).

Revision ID: 20260809_05
Revises: 20260809_04
"""
import sqlalchemy as sa
from alembic import op

revision = "20260809_05"
down_revision = "20260809_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("asset_type", sa.String(30), nullable=False),
        sa.Column("confidentiality", sa.Integer(), nullable=False),
        sa.Column("integrity", sa.Integer(), nullable=False),
        sa.Column("availability", sa.Integer(), nullable=False),
        sa.Column("business_value", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("confidentiality BETWEEN 1 AND 5", name="ck_risk_assets_confidentiality"),
        sa.CheckConstraint("integrity BETWEEN 1 AND 5", name="ck_risk_assets_integrity"),
        sa.CheckConstraint("availability BETWEEN 1 AND 5", name="ck_risk_assets_availability"),
    )
    op.create_table(
        "risks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("threat", sa.String(200)), sa.Column("vulnerability", sa.String(200)),
        sa.Column("likelihood", sa.Integer(), nullable=False), sa.Column("impact", sa.Integer(), nullable=False),
        sa.Column("inherent_score", sa.Integer(), nullable=False), sa.Column("treatment", sa.String(20)),
        sa.Column("residual_likelihood", sa.Integer()), sa.Column("residual_impact", sa.Integer()), sa.Column("residual_score", sa.Integer()),
        sa.Column("status", sa.String(20), nullable=False, server_default="identified"),
        sa.Column("owner_user_id", sa.Integer()), sa.Column("review_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["risk_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("likelihood BETWEEN 1 AND 5 AND impact BETWEEN 1 AND 5", name="ck_risks_inherent_factors"),
        sa.CheckConstraint("inherent_score = likelihood * impact", name="ck_risks_inherent_score"),
        sa.CheckConstraint("residual_score IS NULL OR residual_score <= inherent_score", name="ck_risks_residual_score"),
    )


def downgrade() -> None:
    op.drop_table("risks")
    op.drop_table("risk_assets")
