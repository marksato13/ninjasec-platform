"""Aplica Alembic antes de iniciar la API.

Las instalaciones anteriores creaban el esquema con ``create_all`` y no
tenían ``alembic_version``. Se adoptan solo cuando conservan todas las tablas
del esquema base; una base parcial falla de forma explícita.
"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


_ALEMBIC_TABLE = "alembic_version"


def _config() -> Config:
    backend_dir = Path(__file__).resolve().parents[2]
    return Config(str(backend_dir / "alembic.ini"))


def _adopt_legacy_database(config: Config) -> None:
    """Adopta solo un esquema ``create_all`` equivalente al modelo actual."""

    existing_tables = set(inspect(engine).get_table_names())
    application_tables = existing_tables - {_ALEMBIC_TABLE}
    if not application_tables or _ALEMBIC_TABLE in existing_tables:
        return

    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection,
            opts={"compare_type": True, "compare_server_default": True},
        )
        differences = compare_metadata(context, Base.metadata)

    if differences:
        operation_types = sorted({str(difference[0]) for difference in differences})
        raise RuntimeError(
            "La base existente no tiene control de Alembic y no equivale al "
            "modelo actual. No se aplicará stamp automáticamente. Revisa el "
            "runbook de adopción. Diferencias detectadas: "
            + ", ".join(operation_types)
        )

    command.stamp(config, "head")


def upgrade_database() -> None:
    config = _config()
    _adopt_legacy_database(config)
    command.upgrade(config, "head")


if __name__ == "__main__":
    upgrade_database()
