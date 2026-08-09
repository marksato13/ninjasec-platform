"""Repositorio de arquitectura empresarial (27-P1).

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
    op.create_table("architecture_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("version", sa.String(40), nullable=False, server_default="1.0"),
        sa.Column("state", sa.String(20), nullable=False), sa.Column("adm_phase", sa.String(20)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]), sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
    )
    op.create_index("ix_architecture_models_organization_id", "architecture_models", ["organization_id"])
    op.create_index("ix_architecture_models_client_id", "architecture_models", ["client_id"])
    op.create_table("architecture_elements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("layer", sa.String(24), nullable=False), sa.Column("element_type", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("source_module", sa.String(80)), sa.Column("source_id", sa.String(80)), sa.Column("properties_json", sa.JSON()),
        sa.ForeignKeyConstraint(["model_id"], ["architecture_models.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_architecture_elements_model_id", "architecture_elements", ["model_id"])
    op.create_table("architecture_relationships",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("source_element_id", sa.Integer(), nullable=False), sa.Column("target_element_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(24), nullable=False), sa.Column("label", sa.String(160)),
        sa.ForeignKeyConstraint(["model_id"], ["architecture_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_element_id"], ["architecture_elements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_element_id"], ["architecture_elements.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_architecture_relationships_model_id", "architecture_relationships", ["model_id"])


def downgrade() -> None:
    op.drop_table("architecture_relationships")
    op.drop_table("architecture_elements")
    op.drop_table("architecture_models")
