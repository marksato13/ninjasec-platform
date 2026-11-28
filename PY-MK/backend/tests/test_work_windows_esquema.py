from datetime import datetime

import pytest
from pydantic import ValidationError

from app.modules.work_windows.schemas import (
    WorkWindowCreate,
    WorkWindowDecision,
    WorkWindowStatusChange,
)


def datos(**cambios):
    """Función auxiliar para crear datos válidos."""
    base = {
        "project_id": 1,
        "title": "Cambio de firewall",
        "change_description": "Actualizar reglas del perímetro",
        "rollback_plan": "Restaurar la copia de configuración",
        "starts_at": "2026-12-01T10:00:00",
        "ends_at": "2026-12-01T12:00:00",
    }
    base.update(cambios)
    return base


def test_work_window_create_defaults():
    """Prueba que se creen con valores por defecto."""
    data = datos()
    schema = WorkWindowCreate(**data)
    assert schema.impact == "medium"
    assert schema.is_emergency is False


def test_work_window_create_utc_conversion():
    """Prueba la conversión de horas a UTC sin zona."""
    data = datos(
        starts_at="2026-12-01T10:00:00-05:00",
        ends_at="2026-12-01T12:00:00-05:00"
    )
    schema = WorkWindowCreate(**data)
    expected_start = datetime(2026, 12, 1, 15, 0)
    expected_end = datetime(2026, 12, 1, 17, 0)
    assert schema.starts_at == expected_start
    assert schema.ends_at == expected_end
    assert schema.starts_at.tzinfo is None
    assert schema.ends_at.tzinfo is None


def test_work_window_create_utc_conversion_sin_zona():
    """Prueba que una hora ya sin zona se conserve tal cual."""
    data = datos(
        starts_at="2026-12-01T10:00:00",
        ends_at="2026-12-01T12:00:00"
    )
    schema = WorkWindowCreate(**data)
    expected_start = datetime(2026, 12, 1, 10, 0)
    expected_end = datetime(2026, 12, 1, 12, 0)
    assert schema.starts_at == expected_start
    assert schema.ends_at == expected_end
    assert schema.starts_at.tzinfo is None
    assert schema.ends_at.tzinfo is None


@pytest.mark.parametrize(
    "field,value,error_msg",
    [
        ("title", "ab", "title"),
        ("title", "x" * 161, "title"),
        ("change_description", "corto", "change_description"),
        ("rollback_plan", "corto", "rollback_plan"),
        ("impact", "critical", "impact"),
    ]
)
def test_work_window_create_validation_errors(field, value, error_msg):
    """Prueba que se lancen ValidationError para campos inválidos."""
    data = datos(**{field: value})
    with pytest.raises(ValidationError) as exc_info:
        WorkWindowCreate(**data)
    
    # Verificar que el error sea para el campo correcto
    assert error_msg in str(exc_info.value)


def test_work_window_decision_valid():
    """Prueba que WorkWindowDecision sea válido."""
    decision = WorkWindowDecision(approve=True)
    assert decision.approve is True
    assert decision.comment is None
    
    decision_with_comment = WorkWindowDecision(approve=True, comment="Comentario de prueba")
    assert decision_with_comment.comment == "Comentario de prueba"


def test_work_window_decision_validation_error():
    """Prueba que se lance ValidationError con comentario muy largo."""
    with pytest.raises(ValidationError) as exc_info:
        WorkWindowDecision(approve=True, comment="x" * 1001)
    
    assert "comment" in str(exc_info.value)


def test_work_window_status_change_valid():
    """Prueba que WorkWindowStatusChange sea válido."""
    status_change = WorkWindowStatusChange(status="completed")
    assert status_change.status == "completed"
    assert status_change.note is None


def test_work_window_status_change_validation_error():
    """Prueba que se lance ValidationError con estado inválido."""
    with pytest.raises(ValidationError) as exc_info:
        WorkWindowStatusChange(status="terminado")
    
    assert "status" in str(exc_info.value)
