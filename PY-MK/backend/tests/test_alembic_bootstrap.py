"""Pruebas de regresión para que Alembic sea la fuente del esquema.

La prueba de integración requiere una base PostgreSQL vacía y desechable. Se
activa definiendo ``ALEMBIC_TEST_DATABASE_URL``; nunca reutiliza ni limpia una
base que ya contenga tablas.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db import models  # noqa: F401
from app.db.base import Base


BACKEND_DIR = Path(__file__).resolve().parents[1]
MAIN_FILE = BACKEND_DIR / "app" / "main.py"


def _run_alembic(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "testing",
            "DATABASE_URL": database_url,
            "SEED_ON_STARTUP": "false",
            "PYTHONPATH": str(BACKEND_DIR),
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _run_migration_entrypoint(database_url: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "testing",
            "DATABASE_URL": database_url,
            "SEED_ON_STARTUP": "false",
            "PYTHONPATH": str(BACKEND_DIR),
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "app.db.migrate"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
def _assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"Alembic terminó con código {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_main_no_crea_el_esquema_con_create_all() -> None:
    """El arranque de FastAPI no debe evadir el historial de migraciones."""

    tree = ast.parse(MAIN_FILE.read_text(encoding="utf-8"), filename=str(MAIN_FILE))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create_all"
    ]

    assert not calls, "app.main no debe llamar Base.metadata.create_all(); usa Alembic"


@pytest.mark.integration
def test_alembic_levanta_postgres_vacio_y_upgrade_es_idempotente() -> None:
    """Una base vacía llega a head y un segundo upgrade no cambia el esquema."""

    database_url = os.getenv("ALEMBIC_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("ALEMBIC_TEST_DATABASE_URL no apunta a PostgreSQL efímero")

    engine = sa.create_engine(database_url)
    try:
        inspector = sa.inspect(engine)
        existing_tables = set(inspector.get_table_names())
        assert not existing_tables, (
            "La base de migraciones debe estar vacía y ser desechable; "
            f"se encontraron: {sorted(existing_tables)}"
        )

        first_upgrade = _run_alembic(database_url, "upgrade", "head")
        _assert_success(first_upgrade)

        inspector = sa.inspect(engine)
        migrated_tables = set(inspector.get_table_names())
        expected_tables = set(Base.metadata.tables)
        assert migrated_tables == expected_tables | {"alembic_version"}

        config = Config(str(BACKEND_DIR / "alembic.ini"))
        expected_head = ScriptDirectory.from_config(config).get_current_head()
        with engine.connect() as connection:
            current_revision = connection.scalar(sa.text("SELECT version_num FROM alembic_version"))
        assert current_revision == expected_head

        schema_before = {
            table: tuple(column["name"] for column in inspector.get_columns(table))
            for table in sorted(migrated_tables)
        }

        second_upgrade = _run_alembic(database_url, "upgrade", "head")
        _assert_success(second_upgrade)

        inspector = sa.inspect(engine)
        schema_after = {
            table: tuple(column["name"] for column in inspector.get_columns(table))
            for table in sorted(inspector.get_table_names())
        }
        assert schema_after == schema_before

        # Si la migración base se aleja de los modelos, autogenerate lo detecta.
        consistency_check = _run_alembic(database_url, "check")
        _assert_success(consistency_check)
        assert "No new upgrade operations detected" in consistency_check.stdout

        # Simula una instalación histórica creada con create_all: solo se
        # adopta si el esquema completo equivale al modelo actual.
        downgrade = _run_alembic(database_url, "downgrade", "base")
        _assert_success(downgrade)
        with engine.begin() as connection:
            connection.execute(sa.text("DROP TABLE IF EXISTS alembic_version"))
        Base.metadata.create_all(engine)

        adoption = _run_migration_entrypoint(database_url)
        _assert_success(adoption)
        with engine.connect() as connection:
            adopted_revision = connection.scalar(sa.text("SELECT version_num FROM alembic_version"))
        assert adopted_revision == expected_head
    finally:
        engine.dispose()
