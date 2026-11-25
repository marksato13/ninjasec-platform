"""Linea de negocio por area: Ninja Sec o Ninja Dev.

Plan 34 (modos Ninja Sec y Ninja Dev). El panel filtra menu, dashboard y
proyectos por linea; hasta ahora se adivinaba por el texto del slug, lo que
falla con un area llamada "Redes" o "Software".

Columna nueva y nullable: vacia significa "de las dos lineas", asi que nada
desaparece por falta de datos. El relleno inicial solo marca un area cuando su
nombre o slug apunta a UNA sola linea; si coincide con las dos o con ninguna,
queda vacia y la decide el administrador.

Bajar quita la columna; no toca ninguna otra tabla.

Revision ID: 20261128_03
Revises: 20261128_02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261128_03"
down_revision: str | None = "20261128_02"
branch_labels = None
depends_on = None

_SEC = ("sec", "segur", "ciber", "red", "infra", "firewall", "soc", "riesgo", "audit")
_DEV = ("dev", "desarr", "softw", "web", "app", "sistema", "integra", "automat")


def _algun(patrones: tuple[str, ...]) -> str:
    texto = "lower(coalesce(name, '') || ' ' || coalesce(slug, ''))"
    return "(" + " OR ".join(f"{texto} LIKE '%{p}%'" for p in patrones) + ")"


def upgrade() -> None:
    op.add_column("areas", sa.Column("business_line", sa.String(10), nullable=True))
    sec, dev = _algun(_SEC), _algun(_DEV)
    op.execute(f"UPDATE areas SET business_line = 'sec' WHERE {sec} AND NOT {dev}")
    op.execute(f"UPDATE areas SET business_line = 'dev' WHERE {dev} AND NOT {sec}")


def downgrade() -> None:
    op.drop_column("areas", "business_line")
