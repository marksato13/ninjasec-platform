"""Aplica Alembic antes de iniciar la API.

Las instalaciones anteriores creaban el esquema con ``create_all`` y no
tenían ``alembic_version``. Se adoptan solo cuando conservan todas las tablas
del esquema base; una base parcial falla de forma explícita.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


BASE_REVISION = "20260807_00"
_ALEMBIC_TABLE = "alembic_version"
_POST_BASE_TABLES = {"device_connections"}


def _config() -> Config:
    backend_dir = Path(__file__).resolve().parents[2]
    return Config(str(backend_dir / "alembic.ini"))


def _adopt_legacy_database(config: Config) -> None:
    """Marca una base de ``create_all`` tras validar su esquema mínimo."""

    existing_tables = set(inspect(engine).get_table_names())
    application_tables = existing_tables - {_ALEMBIC_TABLE}
    if not application_tables or _ALEMBIC_TABLE in existing_tables:
        return

    baseline_tables = set(Base.metadata.tables) - _POST_BASE_TABLES
    missing_tables = sorted(baseline_tables - application_tables)
    if missing_tables:
        missing = ", ".join(missing_tables)
        raise RuntimeError(
            "La base existente no tiene control de Alembic y su esquema está "
            f"incompleto. Faltan tablas base: {missing}"
        )

    command.stamp(config, BASE_REVISION)


def upgrade_database() -> None:
    config = _config()
    _adopt_legacy_database(config)
    command.upgrade(config, "head")


if __name__ == "__main__":
    upgrade_database()
