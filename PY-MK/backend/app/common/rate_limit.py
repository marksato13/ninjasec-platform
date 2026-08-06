"""Limitador de peticiones en memoria (15-P-05).

`POST /job-applications/` es el unico endpoint de la API sin autenticacion.
Sin freno, cualquiera puede inundar la tabla de postulaciones antes de que
el sitio este siquiera publicado.

ALCANCE — leelo antes de confiar en esto
=========================================
Es un limitador **por proceso y en memoria**. Cubre el caso real de hoy
(un contenedor, un worker) y nada mas:

- Se reinicia con el proceso: un redespliegue vacia los contadores.
- No se comparte entre workers: con N workers uvicorn el limite efectivo
  es N veces el configurado.
- No frena un ataque distribuido: limita por IP, y muchas IPs pasan.

Es una barrera contra abuso accidental y flooding trivial, no una defensa
anti-DDoS. Cuando el despliegue crezca a varios workers o replicas, esto
debe migrar a Redis (o ponerse en Caddy, que ya esta delante). Mientras
tanto, es mucho mejor que no tener nada.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    """Ventana deslizante por clave. Seguro entre hilos."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """(permitido, segundos_para_reintentar).

        `segundos_para_reintentar` es 0 cuando se permite.
        """
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
        """Solo para tests."""
        with self._lock:
            self._hits.clear()


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


def rate_limit(max_requests: int, window_seconds: int, *, name: str):
    """Construye una dependencia FastAPI que aplica el limite."""
    limiter = SlidingWindowLimiter(max_requests, window_seconds)

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
