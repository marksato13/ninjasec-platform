"""Storage local para documentos, CV y fotos (10-P-05, 15-P-02, 19-P-01).

Revision ID: 20260808_01
Revises: 20260806_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_01"
down_revision = "20260806_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project_docs", sa.Column("file_url", sa.String(500), nullable=True))
    op.add_column("project_docs", sa.Column("file_key", sa.String(500), nullable=True))
    op.add_column("project_docs", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("project_docs", sa.Column("file_type", sa.String(120), nullable=True))
    op.add_column("project_docs", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("application_attachments", sa.Column("file_key", sa.String(500), nullable=True))
    op.add_column("application_attachments", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("application_attachments", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("collaborator_profiles", sa.Column("photo_storage_key", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("collaborator_profiles", "photo_storage_key")
    op.drop_column("application_attachments", "file_size")
    op.drop_column("application_attachments", "file_name")
    op.drop_column("application_attachments", "file_key")
    op.drop_column("project_docs", "file_size")
    op.drop_column("project_docs", "file_type")
    op.drop_column("project_docs", "file_name")
    op.drop_column("project_docs", "file_key")
    op.drop_column("project_docs", "file_url")
