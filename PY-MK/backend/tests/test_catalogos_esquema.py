from app.modules.catalogs.schemas.area import AreaCreate, AreaUpdate
from app.modules.catalogs.schemas.project_type import ProjectTypeCreate, ProjectTypeUpdate
from pydantic import ValidationError


def test_area_create_valid():
    """AreaCreate con name válido es válido, con slug y business_line en None."""
    area = AreaCreate(name="Redes")
    assert area.name == "Redes"
    assert area.slug is None
    assert area.business_line is None


def test_area_create_business_line_valid():
    """AreaCreate con business_line 'sec' o 'dev' es válido; 'ops' lanza ValidationError."""
    area_sec = AreaCreate(name="Redes", business_line="sec")
    assert area_sec.business_line == "sec"
    
    area_dev = AreaCreate(name="Redes", business_line="dev")
    assert area_dev.business_line == "dev"


def test_area_create_business_line_invalid():
    """AreaCreate con business_line 'ops' lanza ValidationError."""
    try:
        AreaCreate(name="Redes", business_line="ops")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_area_create_name_validation():
    """AreaCreate lanza ValidationError con name de longitud inválida."""
    # Nombre muy corto
    try:
        AreaCreate(name="R")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
    
    # Nombre muy largo
    try:
        AreaCreate(name="x" * 121)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_area_update_valid():
    """AreaUpdate() es válido y confirm_deactivation vale False; AreaUpdate(business_line='ops') lanza ValidationError."""
    area_update = AreaUpdate()
    assert area_update.confirm_deactivation is False
    
    # Test que business_line inválido lanza ValidationError
    try:
        AreaUpdate(business_line="ops")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_project_type_create_valid():
    """ProjectTypeCreate con name válido es válido."""
    project_type = ProjectTypeCreate(name="Auditoría")
    assert project_type.name == "Auditoría"


def test_project_type_create_name_validation():
    """ProjectTypeCreate lanza ValidationError con name de longitud inválida."""
    try:
        ProjectTypeCreate(name="A")
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass


def test_project_type_update_valid():
    """ProjectTypeUpdate con is_active=False es válido; name muy largo lanza ValidationError."""
    project_type_update = ProjectTypeUpdate(is_active=False)
    assert project_type_update.is_active is False
    
    # Test que nombre muy largo lanza ValidationError
    try:
        ProjectTypeUpdate(name="x" * 121)
        assert False, "Debería lanzar ValidationError"
    except ValidationError:
        pass
