import pytest
from pydantic import ValidationError

from app.modules.certifications.schemas.certification import (
    _url_publica,
    UserCertificationCreate,
    UserCertificationUpdate,
)


def test_url_publica_none():
    """_url_publica(None) es None"""
    assert _url_publica(None) is None


def test_url_publica_empty_strings():
    """_url_publica("") y _url_publica("   ") son None"""
    assert _url_publica("") is None
    assert _url_publica("   ") is None


def test_url_publica_trimmed():
    """_url_publica("  https://www.credly.com/badges/abc  ") devuelve el texto sin espacios"""
    result = _url_publica("  https://www.credly.com/badges/abc  ")
    assert result == "https://www.credly.com/badges/abc"


def test_url_publica_case_insensitive():
    """"HTTPS://EJEMPLO.COM" y "http://ejemplo.com" se aceptan sin cambios"""
    assert _url_publica("HTTPS://EJEMPLO.COM") == "HTTPS://EJEMPLO.COM"
    assert _url_publica("http://ejemplo.com") == "http://ejemplo.com"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "javascript:alert(1)",
        "ftp://ejemplo.com",
        "www.ejemplo.com",
        "data:text/html,hola",
    ],
)
def test_url_publica_invalid_urls(invalid_url):
    """Con pytest.mark.parametrize, lanzan ValueError"""
    with pytest.raises(ValueError, match="El enlace de verificación debe empezar por https://"):
        _url_publica(invalid_url)


def test_user_certification_create_validation():
    """UserCertificationCreate(name="CCNA", url="javascript:alert(1)") lanza pydantic.ValidationError"""
    with pytest.raises(ValidationError):
        UserCertificationCreate(name="CCNA", url="javascript:alert(1)")


def test_user_certification_update_valid_url():
    """UserCertificationUpdate(url="https://ok.com").url == "https://ok.com" """
    update = UserCertificationUpdate(url="https://ok.com")
    assert update.url == "https://ok.com"
