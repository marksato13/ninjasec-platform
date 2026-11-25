"""Certificaciones con archivo adjunto y area (Ninja Sec / Ninja Dev).

La formacion se hace en plataformas externas (Fortinet NSE, Cisco NetAcad, AWS
Skill Builder...). Aqui solo se registra el resultado: el certificado, para que
un administrador lo valide y el cliente vea al personal capacitado.

Columnas nuevas y opcionales: las certificaciones existentes quedan sin archivo y
sin area, que es lo que son. Bajar borra solo esas columnas (y la referencia a los
archivos; los archivos en disco no se tocan).

Revision ID: 20261129_01
Revises: 20261128_03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261129_01"
down_revision: str | None = "20261128_03"
branch_labels = None
depends_on = None

_COLUMNAS = ("area", "file_key", "file_name", "file_type", "file_size")


def upgrade() -> None:
    op.add_column("user_certifications", sa.Column("area", sa.String(10), nullable=True))
    op.add_column("user_certifications", sa.Column("file_key", sa.String(500), nullable=True))
    op.add_column("user_certifications", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("user_certifications", sa.Column("file_type", sa.String(120), nullable=True))
    op.add_column("user_certifications", sa.Column("file_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    for columna in reversed(_COLUMNAS):
        op.drop_column("user_certifications", columna)
