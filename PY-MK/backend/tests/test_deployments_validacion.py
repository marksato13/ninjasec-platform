from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from app.modules.deployments.router import _version, _fecha
from app.core.time_utils import utcnow


def test_version_vacia_es_none():
    assert _version(None) is None


def test_version_se_recorta():
    assert _version("  v1.2.3  ") == "v1.2.3"


def test_versiones_validas():
    assert _version("a1b2c3d") == "a1b2c3d"
    assert _version("release/2026-11") == "release/2026-11"


def test_version_de_sesenta_caracteres():
    assert _version("a" * 60) == "a" * 60
    with pytest.raises(ValueError):
        _version("a" * 61)


def test_versiones_invalidas():
    invalid_versions = ["-v1", "v 1", ""]
    for version in invalid_versions:
        with pytest.raises(ValueError):
            _version(version)


def test_fecha_vacia_es_none():
    assert _fecha(None) is None


def test_fecha_con_zona_pasa_a_utc():
    dt = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5)))
    result = _fecha(dt)
    expected = datetime(2026, 1, 1, 17, 0)
    assert result == expected


def test_fecha_futura_falla():
    with pytest.raises(ValueError):
        _fecha(utcnow() + timedelta(hours=1))


def test_fecha_casi_actual_se_acepta():
    result = _fecha(utcnow() + timedelta(minutes=1))
    assert result is not None
