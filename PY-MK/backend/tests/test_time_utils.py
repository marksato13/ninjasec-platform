"""Contrato de app/core/time_utils.utcnow().

Los modelos usan TIMESTAMP WITHOUT TIME ZONE y psycopg3 rechaza fechas con
zona horaria: utcnow() debe devolver la hora UTC *sin* tzinfo.
"""

from datetime import UTC, datetime

from app.core.time_utils import utcnow


def test_utcnow_devuelve_datetime_sin_zona_horaria():
    resultado = utcnow()
    assert isinstance(resultado, datetime)
    assert resultado.tzinfo is None


def test_utcnow_es_la_hora_utc_y_no_la_local():
    # Sin mocks: se compara con el reloj real en UTC. Si utcnow() devolviera la
    # hora local (Lima va 5 h por detras), la diferencia seria de horas.
    referencia = datetime.now(UTC).replace(tzinfo=None)
    assert abs((utcnow() - referencia).total_seconds()) < 5


def test_dos_llamadas_seguidas_no_retroceden():
    a = utcnow()
    b = utcnow()
    assert b >= a
