from pydantic import ValidationError

from app.modules.services.schemas.service import ServiceRequestConvert, ServiceRequestCreate


def test_service_request_create_valid():
    """ServiceRequestCreate con datos mínimos es válido."""
    request = ServiceRequestCreate(
        service_id=1,
        requester_name="Ana",
        requester_email="ana@empresa.pe"
    )
    assert request.service_id == 1
    assert request.requester_name == "Ana"
    assert request.requester_email == "ana@empresa.pe"
    assert request.message is None
    assert request.client_id is None


def test_service_request_create_message_min_length():
    """Message con menos de 5 caracteres lanza ValidationError."""
    try:
        ServiceRequestCreate(
            service_id=1,
            requester_name="Ana",
            requester_email="ana@empresa.pe",
            message="Hola"  # 4 caracteres
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass

    # 5 caracteres debe ser válido
    request = ServiceRequestCreate(
        service_id=1,
        requester_name="Ana",
        requester_email="ana@empresa.pe",
        message="Hola!"  # 5 caracteres
    )
    assert request.message == "Hola!"


def test_service_request_create_validation_errors():
    """Varios casos que deben lanzar ValidationError."""
    # requester_name con menos de 2 caracteres
    try:
        ServiceRequestCreate(
            service_id=1,
            requester_name="A",
            requester_email="ana@empresa.pe"
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass

    # requester_email inválido
    try:
        ServiceRequestCreate(
            service_id=1,
            requester_name="Ana",
            requester_email="ana"
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass

    # request_type con más de 80 caracteres
    try:
        ServiceRequestCreate(
            service_id=1,
            requester_name="Ana",
            requester_email="ana@empresa.pe",
            request_type="x" * 81
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass

    # message con más de 1000 caracteres
    try:
        ServiceRequestCreate(
            service_id=1,
            requester_name="Ana",
            requester_email="ana@empresa.pe",
            message="x" * 1001
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass


def test_service_request_convert_valid():
    """ServiceRequestConvert con datos mínimos es válido."""
    convert = ServiceRequestConvert(project_type_id=1)
    assert convert.project_type_id == 1
    assert convert.name is None
    assert convert.client_id is None


def test_service_request_convert_name_min_length():
    """Name con menos de 3 caracteres lanza ValidationError."""
    try:
        ServiceRequestConvert(
            project_type_id=1,
            name="ab"  # 2 caracteres
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass

    # 3 caracteres debe ser válido
    convert = ServiceRequestConvert(
        project_type_id=1,
        name="Red nueva"
    )
    assert convert.name == "Red nueva"


def test_service_request_convert_description_max_length():
    """Description con más de 255 caracteres lanza ValidationError."""
    try:
        ServiceRequestConvert(
            project_type_id=1,
            description="x" * 256
        )
        assert False, "Debería haber lanzado ValidationError"
    except ValidationError:
        pass
