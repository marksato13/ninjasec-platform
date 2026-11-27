import pytest
from pydantic import ValidationError

from app.modules.compliance.schemas.soa import ControlStatusUpdate


def test_madurez_acepta_los_extremos():
    """maturity_level=0 y maturity_level=5 se aceptan y conservan el valor"""
    # Test maturity_level = 0
    obj = ControlStatusUpdate(maturity_level=0)
    assert obj.maturity_level == 0
    
    # Test maturity_level = 5
    obj = ControlStatusUpdate(maturity_level=5)
    assert obj.maturity_level == 5


def test_madurez_rechaza_seis():
    """maturity_level=6 lanza ValidationError"""
    with pytest.raises(ValidationError):
        ControlStatusUpdate(maturity_level=6)


def test_madurez_rechaza_negativos():
    """maturity_level=-1 lanza ValidationError"""
    with pytest.raises(ValidationError):
        ControlStatusUpdate(maturity_level=-1)


def test_aplicabilidad_valida():
    """applicability igual a 'applicable' y 'not_applicable' se aceptan"""
    # Test applicability = "applicable"
    obj = ControlStatusUpdate(applicability="applicable")
    assert obj.applicability == "applicable"
    
    # Test applicability = "not_applicable"
    obj = ControlStatusUpdate(applicability="not_applicable")
    assert obj.applicability == "not_applicable"


def test_aplicabilidad_desconocida():
    """applicability='tal_vez' lanza ValidationError"""
    with pytest.raises(ValidationError):
        ControlStatusUpdate(applicability="tal_vez")


def test_estado_de_implementacion_valido():
    """implementation_status igual a 'not_implemented', 'planned', 'partial' y 'implemented' se aceptan"""
    # Test implementation_status = "not_implemented"
    obj = ControlStatusUpdate(implementation_status="not_implemented")
    assert obj.implementation_status == "not_implemented"
    
    # Test implementation_status = "planned"
    obj = ControlStatusUpdate(implementation_status="planned")
    assert obj.implementation_status == "planned"
    
    # Test implementation_status = "partial"
    obj = ControlStatusUpdate(implementation_status="partial")
    assert obj.implementation_status == "partial"
    
    # Test implementation_status = "implemented"
    obj = ControlStatusUpdate(implementation_status="implemented")
    assert obj.implementation_status == "implemented"


def test_estado_de_implementacion_desconocido():
    """implementation_status='done' lanza ValidationError"""
    with pytest.raises(ValidationError):
        ControlStatusUpdate(implementation_status="done")
