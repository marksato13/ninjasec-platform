"""25-P2: contrato de persistencia de la migración de catálogos de riesgo."""

from importlib import import_module
from pathlib import Path


def test_migracion_catalogos_encadena_tras_risks_y_define_join_tables():
    migration = import_module("app.db.migrations.versions.20260809_08_risk_catalogs")
    assert migration.revision == "20260809_08"
    assert migration.down_revision == "20260809_07"

    source = Path(migration.__file__).read_text(encoding="utf-8")
    assert '"uq_threat_org_code"' in source
    assert '"uq_vulnerability_org_code"' in source
    assert 'sa.UniqueConstraint("organization_id", "code", name=constraint_name)' in source
    assert 'sa.ForeignKeyConstraint(["risk_id"], ["risks.id"], ondelete="CASCADE")' in source
    assert 'sa.ForeignKeyConstraint(["threat_id"], ["threats.id"], ondelete="RESTRICT")' in source
    assert 'sa.ForeignKeyConstraint(["vulnerability_id"], ["vulnerabilities.id"], ondelete="RESTRICT")' in source
