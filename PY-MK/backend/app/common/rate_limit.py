"""Limitador de peticiones — en memoria o distribuido con Redis (15-P-05 / G-06).

Protege las rutas que no piden sesion y el login:

- `POST /auth/login`: 10 intentos cada 5 minutos por IP (adivinar claves;
  `LOGIN_RATE_LIMIT_MAX` lo cambia, solo el e2e del CI lo sube).
- `POST /leads/`: 5 por hora por IP (cada envio manda un correo).
- `POST /services/requests`: 5 por hora por IP.
- `POST /job-applications/`: 5 por hora por IP.

El limite es por IP y no por correo a proposito: uno por correo dejaria a
cualquiera bloquear la cuenta de otro a base de fallar su clave.

ALCANCE — leelo antes de confiar en esto
=========================================
Hay dos backends con la misma semantica de ventana deslizante (evaluados
en `check`, con `reset()` para tests):

- **En memoria** (`InMemorySlidingWindowLimiter`): por proceso. Se usa
  siempre que `settings.redis_url` esta vacio (default en dev y en CI, que
  no levanta Redis) o si Redis no responde al arrancar. Se reinicia con el
  proceso; con N workers uvicorn el limite efectivo es N veces el
  configurado.
- **Redis** (`RedisSlidingWindowLimiter`): compartido entre workers y
  replicas. Se activa solo con `settings.redis_url` configurado y Redis
  alcanzable en el arranque. Si Redis se cae *despues* de arrancar, el
  limitador **falla abierto** (deja pasar la peticion) — un rate limiter
  caido nunca debe tumbar el endpoint que protege, la barrera aca es
  contra abuso trivial, no una defensa anti-DDoS.

En ambos casos limita por IP; muchas IPs distintas igual pasan. Es una
barrera contra abuso accidental y flooding trivial, no una defensa
anti-DDoS real.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Protocol

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiterBackend(Protocol):
    """Interfaz comun entre el backend en memoria y el de Redis."""

    max_requests: int
    window_seconds: int

    def check(self, key: str) -> tuple[bool, int]:
        """(permitido, segundos_para_reintentar). 0 cuando se permite."""
        ...

    def reset(self) -> None:
        """Solo para tests."""
        ...


class InMemorySlidingWindowLimiter:
    """Ventana deslizante por clave, en memoria. Seguro entre hilos."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = int(hits[0] + self.window_seconds - now) + 1
                return False, max(retry_after, 1)

            hits.append(now)

            # Poda: sin esto el dict crece sin techo con cada IP nueva,
            # que es en si mismo un vector de agotamiento de memoria.
            if len(self._hits) > 10_000:
                self._prune(cutoff)

            return True, 0

    def _prune(self, cutoff: float) -> None:
        """Elimina claves sin actividad reciente. Se llama con el lock puesto."""
        vacias = [k for k, v in self._hits.items() if not v or v[-1] < cutoff]
        for k in vacias:
            del self._hits[k]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Ventana deslizante atomica sobre un sorted set: ZREMRANGEBYSCORE saca lo
# vencido, ZCARD cuenta lo que queda, y solo si hay hueco se agrega el
# nuevo hit. Todo en un solo EVAL -- sin esto, dos peticiones concurrentes
# podrian leer el mismo conteo antes de que ninguna escriba (TOCTOU).
_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local member = ARGV[4]
local cutoff = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)
if count >= max_requests then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry_after = 1
  if oldest[2] then
    retry_after = math.floor(tonumber(oldest[2]) + window - now) + 1
    if retry_after < 1 then retry_after = 1 end
  end
  return {0, retry_after}
end

redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window)
return {1, 0}
"""


class RedisSlidingWindowLimiter:
    """Misma ventana deslizante que la version en memoria, compartida via Redis."""

    def __init__(self, redis_client, max_requests: int, window_seconds: int, *, prefix: str) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis = redis_client
        self._prefix = prefix
        self._script = redis_client.register_script(_SLIDING_WINDOW_LUA)

    def check(self, key: str) -> tuple[bool, int]:
        now = time.time()
        member = uuid.uuid4().hex
        try:
            allowed, retry_after = self._script(
                keys=[f"{self._prefix}:{key}"],
                args=[now, self.window_seconds, self.max_requests, member],
            )
        except Exception:
            # Redis se cayo despues de arrancar: mejor dejar pasar que
            # tumbar el endpoint que este limitador deberia proteger.
            logger.warning("Redis no disponible para rate limit '%s'; dejando pasar la peticion", self._prefix)
            return True, 0
        return bool(allowed), int(retry_after)

    def reset(self) -> None:
        """Solo para tests."""
        try:
            for redis_key in self._redis.scan_iter(f"{self._prefix}:*"):
                self._redis.delete(redis_key)
        except Exception:
            pass


def client_key(request: Request) -> str:
    """Identifica al peticionario.

    Detras de Caddy la IP real viaja en X-Forwarded-For. La cabecera es
    falsificable si la app queda expuesta directamente, pero en este
    despliegue solo el reverse proxy le habla al backend.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _build_limiter(max_requests: int, window_seconds: int, name: str) -> RateLimiterBackend:
    if settings.redis_url:
        try:
            import redis as redis_module

            client = redis_module.from_url(settings.redis_url)
            client.ping()
            return RedisSlidingWindowLimiter(
                client, max_requests, window_seconds, prefix=f"ratelimit:{name}"
            )
        except Exception:
            logger.warning(
                "No se pudo conectar a Redis para el rate limit '%s'; usando el limitador en memoria",
                name,
            )
    return InMemorySlidingWindowLimiter(max_requests, window_seconds)


_REGISTRADOS: list[RateLimiterBackend] = []


def reset_all() -> None:
    """Solo para tests: vacia todos los limitadores creados."""
    for limiter in _REGISTRADOS:
        limiter.reset()


def rate_limit(max_requests: int, window_seconds: int, *, name: str):
    """Construye una dependencia FastAPI que aplica el limite."""
    limiter = _build_limiter(max_requests, window_seconds, name)
    _REGISTRADOS.append(limiter)

    def dependency(request: Request) -> None:
        allowed, retry_after = limiter.check(f"{name}:{client_key(request)}")
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Demasiadas solicitudes. Espera unos minutos antes de "
                    "volver a intentarlo."
                ),
                headers={"Retry-After": str(retry_after)},
            )

    dependency.limiter = limiter  # type: ignore[attr-defined]  # los tests lo resetean
    return dependency
