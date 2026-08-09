"""25-P1: contrato de persistencia de la migración de riesgos.

Estas comprobaciones son independientes del CRUD: protegen las invariantes
que deben existir también para escrituras que no pasen por la API.
"""

from importlib import import_module
from pathlib import Path


def test_migracion_riesgos_define_scores_derivados_y_residual_acotado():
    migration = import_module("app.db.migrations.versions.20260809_05_risks")
    source = migration.__file__
    assert source is not None
    content = Path(source).read_text(encoding="utf-8")

    assert 'sa.Column("device_id", sa.Integer(), nullable=True)' in content
    assert 'sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL")' in content
    assert 'sa.CheckConstraint("inherent_score = likelihood * impact", name="ck_risks_inherent_score")' in content
    assert 'sa.CheckConstraint("residual_score IS NULL OR residual_score <= inherent_score", name="ck_risks_residual_score")' in content
