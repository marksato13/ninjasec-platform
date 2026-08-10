"""Backend Redis del rate limiter (G-06).

Usa fakeredis en vez de un servidor real -- CI no levanta Redis, y el
comportamiento (ventana deslizante, atomicidad via el script Lua, fallo
abierto si Redis se cae) debe verificarse igual sin depender de red.
"""

import fakeredis
import pytest

from app.common import rate_limit as rate_limit_module
from app.common.rate_limit import (
    InMemorySlidingWindowLimiter,
    RedisSlidingWindowLimiter,
    _build_limiter,
)


def _fake_client():
    return fakeredis.FakeStrictRedis()


def test_redis_limiter_bloquea_tras_superar_el_limite():
    limiter = RedisSlidingWindowLimiter(_fake_client(), max_requests=5, window_seconds=3600, prefix="test")

    permitidos = sum(1 for _ in range(6) if limiter.check("203.0.113.10")[0])

    assert permitidos == 5


def test_redis_limiter_es_por_clave():
    limiter = RedisSlidingWindowLimiter(_fake_client(), max_requests=1, window_seconds=3600, prefix="test")

    assert limiter.check("ip-a")[0] is True
    assert limiter.check("ip-a")[0] is False
    assert limiter.check("ip-b")[0] is True, "una clave saturada no debe bloquear a otra"


def test_redis_limiter_reset_limpia_los_contadores():
    limiter = RedisSlidingWindowLimiter(_fake_client(), max_requests=1, window_seconds=3600, prefix="test")

    assert limiter.check("ip-a")[0] is True
    assert limiter.check("ip-a")[0] is False

    limiter.reset()

    assert limiter.check("ip-a")[0] is True


def test_redis_limiter_falla_abierto_si_redis_se_cae_en_pleno_vuelo():
    """Si Redis responde al arrancar pero se cae despues, el limitador
    debe dejar pasar la peticion -- nunca tumbar el endpoint que protege."""

    class _RedisRoto:
        def register_script(self, _script):
            def _explota(**_kwargs):
                raise ConnectionError("Redis no disponible")
            return _explota

    limiter = RedisSlidingWindowLimiter(_RedisRoto(), max_requests=1, window_seconds=60, prefix="test")

    allowed, retry_after = limiter.check("ip-a")

    assert allowed is True
    assert retry_after == 0


def test_build_limiter_usa_memoria_si_redis_url_esta_vacio(monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "redis_url", "")

    limiter = _build_limiter(5, 60, "test-vacio")

    assert isinstance(limiter, InMemorySlidingWindowLimiter)


def test_build_limiter_cae_a_memoria_si_redis_no_responde(monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "redis_url", "redis://localhost:1")

    limiter = _build_limiter(5, 60, "test-inalcanzable")

    assert isinstance(limiter, InMemorySlidingWindowLimiter), (
        "si Redis no responde al arrancar, debe degradar a un limitador que SI funciona"
    )
    # y el fallback debe funcionar de verdad, no ser un cascaron vacio
    assert limiter.check("ip-a")[0] is True


def test_build_limiter_usa_redis_si_esta_configurado_y_responde(monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "redis_url", "redis://fake:6379/0")

    import redis as redis_module
    monkeypatch.setattr(redis_module, "from_url", lambda *_args, **_kwargs: fakeredis.FakeStrictRedis())

    limiter = _build_limiter(5, 60, "test-redis-ok")

    assert isinstance(limiter, RedisSlidingWindowLimiter)
