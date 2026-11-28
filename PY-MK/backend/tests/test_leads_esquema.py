from pydantic import ValidationError

from app.modules.leads.schemas.lead import LeadCreate, LeadInfoUpdate


def test_lead_create_valid():
    """Prueba que LeadCreate sea válido con datos mínimos."""
    lead = LeadCreate(contact_name="Ana", email="ana@empresa.pe")
    assert lead.contact_name == "Ana"
    assert lead.email == "ana@empresa.pe"
    assert lead.company_name is None
    assert lead.phone is None
    assert lead.interest_area is None
    assert lead.message is None
    assert lead.source is None


def test_lead_create_source_validation():
    """Prueba que el campo source se valide correctamente."""
    # source de 80 caracteres se acepta
    lead = LeadCreate(contact_name="Ana", email="ana@empresa.pe", source="website:tiktok-03")
    assert lead.source == "website:tiktok-03"
    
    # source de 80 caracteres se acepta
    source_80 = "x" * 80
    lead = LeadCreate(contact_name="Ana", email="ana@empresa.pe", source=source_80)
    assert lead.source == source_80
    
    # source de 81 caracteres lanza ValidationError
    source_81 = "x" * 81
    try:
        LeadCreate(contact_name="Ana", email="ana@empresa.pe", source=source_81)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_lead_create_invalid_fields():
    """Prueba que LeadCreate lance ValidationError con campos inválidos."""
    # contact_name menor a 2 caracteres
    try:
        LeadCreate(contact_name="A", email="ana@empresa.pe")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # email inválido
    try:
        LeadCreate(contact_name="Ana", email="no-es-correo")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # phone de 51 caracteres
    try:
        LeadCreate(contact_name="Ana", email="ana@empresa.pe", phone="9" * 51)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # message de 1001 caracteres
    try:
        LeadCreate(contact_name="Ana", email="ana@empresa.pe", message="x" * 1001)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # company_name de 151 caracteres
    try:
        LeadCreate(contact_name="Ana", email="ana@empresa.pe", company_name="x" * 151)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_lead_info_update_valid_empty():
    """Prueba que LeadInfoUpdate() vacío sea válido."""
    update = LeadInfoUpdate()
    assert update.contact_name is None
    assert update.email is None
    assert update.company_name is None
    assert update.phone is None
    assert update.interest_area is None
    assert update.message is None
    assert update.source is None


def test_lead_info_update_invalid_fields():
    """Prueba que LeadInfoUpdate lance ValidationError con campos inválidos."""
    # contact_name menor a 2 caracteres
    try:
        LeadInfoUpdate(contact_name="A")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # email inválido
    try:
        LeadInfoUpdate(email="mal")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_lead_info_update_source_validation():
    """Prueba que el campo source de LeadInfoUpdate se valide correctamente."""
    # source de 81 caracteres lanza ValidationError
    try:
        LeadInfoUpdate(source="x" * 81)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
