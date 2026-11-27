from pydantic import ValidationError
from app.modules.docs.schemas.project_doc import ProjectDocClientDecision


def test_aprobar_sin_nota():
    """Un cliente que aprueba no necesita nota."""
    decision = ProjectDocClientDecision(decision="approved")
    assert decision.decision == "approved"
    assert decision.note is None


def test_nota_en_blanco_queda_vacia():
    """Una nota en blanco se convierte en None."""
    decision = ProjectDocClientDecision(decision="approved", note="   ")
    assert decision.note is None


def test_la_nota_se_recorta():
    """Las notas se recortan de espacios."""
    decision = ProjectDocClientDecision(decision="changes_requested", note="  cambia el logo  ")
    assert decision.note == "cambia el logo"


def test_pedir_cambios_sin_nota_falla():
    """Pedir cambios sin nota lanza ValidationError."""
    with pytest.raises(ValidationError):
        ProjectDocClientDecision(decision="changes_requested")


def test_pedir_cambios_con_nota_corta_falla():
    """Pedir cambios con nota corta lanza ValidationError."""
    with pytest.raises(ValidationError):
        ProjectDocClientDecision(decision="changes_requested", note="abc")


def test_pedir_cambios_con_cinco_caracteres():
    """Pedir cambios con 5 caracteres se acepta."""
    decision = ProjectDocClientDecision(decision="changes_requested", note="falta")
    assert decision.decision == "changes_requested"
    assert decision.note == "falta"
from pydantic import ValidationError
import pytest
from app.modules.docs.schemas.project_doc import ProjectDocClientDecision


def test_aprobar_sin_nota():
    """Un cliente que aprueba no necesita nota."""
    decision = ProjectDocClientDecision(decision="approved")
    assert decision.decision == "approved"
    assert decision.note is None


def test_nota_en_blanco_queda_vacia():
    """Una nota en blanco se convierte en None."""
    decision = ProjectDocClientDecision(decision="approved", note="   ")
    assert decision.note is None


def test_la_nota_se_recorta():
    """Las notas se recortan de espacios."""
    decision = ProjectDocClientDecision(decision="changes_requested", note="  cambia el logo  ")
    assert decision.note == "cambia el logo"


def test_pedir_cambios_sin_nota_falla():
    """Pedir cambios sin nota lanza ValidationError."""
    with pytest.raises(ValidationError):
        ProjectDocClientDecision(decision="changes_requested")


def test_pedir_cambios_con_nota_corta_falla():
    """Pedir cambios con nota corta lanza ValidationError."""
    with pytest.raises(ValidationError):
        ProjectDocClientDecision(decision="changes_requested", note="abc")


def test_pedir_cambios_con_cinco_caracteres():
    """Pedir cambios con 5 caracteres se acepta."""
    decision = ProjectDocClientDecision(decision="changes_requested", note="falta")
    assert decision.decision == "changes_requested"
    assert decision.note == "falta"
