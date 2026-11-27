import pytest
from pydantic import ValidationError

from app.modules.audits.schemas.audit import AuditCreate, AuditUpdate

def test_acepta_los_cuatro_marcos():
    """Test that the audit schema accepts the four valid frameworks"""
    frameworks = ["cobit_2019", "iso_27001", "iso_19011", "custom"]
    
    for framework in frameworks:
        audit = AuditCreate(
            client_id=1,
            title="Auditoria anual",
            lead_auditor_id=1,
            framework=framework,
            audit_type="internal"
        )
        assert audit.framework == framework

def test_rechaza_un_marco_desconocido():
    """Test that the audit schema rejects unknown frameworks"""
    with pytest.raises(ValidationError):
        AuditCreate(
            client_id=1,
            title="Auditoria anual",
            lead_auditor_id=1,
            framework="nist",
            audit_type="internal"
        )

def test_acepta_los_cuatro_tipos():
    """Test that the audit schema accepts the four valid audit types"""
    audit_types = ["internal", "external", "certification", "follow_up"]
    
    for audit_type in audit_types:
        audit = AuditCreate(
            client_id=1,
            title="Auditoria anual",
            lead_auditor_id=1,
            framework="cobit_2019",
            audit_type=audit_type
        )
        assert audit.audit_type == audit_type

def test_rechaza_un_tipo_desconocido():
    """Test that the audit schema rejects unknown audit types"""
    with pytest.raises(ValidationError):
        AuditCreate(
            client_id=1,
            title="Auditoria anual",
            lead_auditor_id=1,
            framework="cobit_2019",
            audit_type="otro"
        )

def test_update_vacio_es_valido():
    """Test that empty AuditUpdate is valid"""
    update = AuditUpdate()
    assert update.status is None
    assert update.opinion is None

def test_update_acepta_estados_y_opiniones():
    """Test that AuditUpdate accepts valid statuses and opinions"""
    valid_statuses = ["planned", "in_progress", "reporting", "closed"]
    valid_opinions = ["satisfactory", "with_observations", "unsatisfactory"]
    
    for status in valid_statuses:
        update = AuditUpdate(status=status)
        assert update.status == status
    
    for opinion in valid_opinions:
        update = AuditUpdate(opinion=opinion)
        assert update.opinion == opinion

def test_update_rechaza_estado_y_opinion_desconocidos():
    """Test that AuditUpdate rejects invalid statuses and opinions"""
    with pytest.raises(ValidationError):
        AuditUpdate(status="abierto")
    
    with pytest.raises(ValidationError):
        AuditUpdate(opinion="buena")
