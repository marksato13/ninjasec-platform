from __future__ import annotations

import pytest

from app.modules.client_systems.router import _texto, _url_limpia


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_url_limpia_vacia_da_none(valor):
    """Una URL ausente o en blanco no es un dato: se guarda como None."""
    assert _url_limpia(valor) is None


def test_url_limpia_quita_espacios():
    """Los espacios de los extremos no llegan a la base de datos."""
    assert _url_limpia("  https://github.com/empresa/repo  ") == "https://github.com/empresa/repo"


def test_url_limpia_acepta_puerto_y_ruta():
    """Una URL interna con puerto y ruta es vÃ¡lida."""
    assert _url_limpia("http://intranet.local:8080/app") == "http://intranet.local:8080/app"


@pytest.mark.parametrize(
    "valor",
    [
        "github.com/empresa/repo",
        "ftp://servidor/x",
        "https://",
        "javascript:alert(1)",
    ],
)
def test_url_limpia_rechaza_lo_que_no_es_web(valor):
    """Sin esquema http(s) o sin dominio no es una URL aceptable."""
    with pytest.raises(ValueError):
        _url_limpia(valor)


@pytest.mark.parametrize(
    "valor",
    [
        "https://ana:x@github.com/repo",
        "https://ana@github.com/repo",
    ],
)
def test_url_limpia_rechaza_credenciales(valor):
    """Usuario o contraseÃ±a incrustados en la URL no se aceptan."""
    with pytest.raises(ValueError):
        _url_limpia(valor)


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_texto_vacio_da_none(valor):
    """Un texto ausente o en blanco se guarda como None."""
    assert _texto(valor) is None


def test_texto_quita_espacios():
    """Los espacios de los extremos se recortan y el resto se conserva."""
    assert _texto("  Django 5  ") == "Django 5"
