"""La cabecera Location nunca sale con el host interno de Docker.

Hallazgo real del primer CI de las pruebas E2E (PR #128): pedir una
colección sin barra final hacía que FastAPI respondiera

    Location: http://backend:8024/api/v1/clients/

con `backend:8024`, el nombre del servicio dentro de la red de Docker. Dos
problemas en uno: filtra la topología interna y el redirect no funciona
desde fuera, porque ese nombre no resuelve.

Estas pruebas simulan la situación exacta: una petición cuya cabecera
`Host` es la interna, que es lo que ve el backend detrás del proxy de Next.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


HOST_INTERNO = "backend:8024"


def _pedir_sin_barra(ruta: str):
    """Pide una ruta sin barra final, haciéndose pasar por el proxy."""
    with TestClient(app, follow_redirects=False) as cliente:
        return cliente.get(ruta, headers={"Host": HOST_INTERNO})


def test_el_redirect_de_barra_final_no_filtra_el_host_interno():
    respuesta = _pedir_sin_barra("/api/v1/clients")

    assert 300 <= respuesta.status_code < 400, (
        "Se esperaba una redirección por la barra final; si FastAPI deja de "
        f"redirigir, esta prueba sobra. Llegó {respuesta.status_code}."
    )
    destino = respuesta.headers["location"]
    assert HOST_INTERNO not in destino, (
        f"La cabecera Location expone el host interno: {destino}"
    )


def test_el_location_es_relativo():
    respuesta = _pedir_sin_barra("/api/v1/clients")
    destino = respuesta.headers["location"]

    assert destino.startswith("/"), (
        "El Location debe ser relativo para que lo resuelva el cliente contra "
        f"el host por el que entró. Llegó: {destino}"
    )
    assert "://" not in destino, f"El Location sigue siendo absoluto: {destino}"


def test_se_conserva_la_ruta_de_destino():
    """Hacerlo relativo no debe cambiar a dónde apunta."""
    respuesta = _pedir_sin_barra("/api/v1/clients")

    assert respuesta.headers["location"] == "/api/v1/clients/"


def test_se_conserva_la_cadena_de_consulta():
    """Un redirect que pierde los parámetros rompe la paginación."""
    respuesta = _pedir_sin_barra("/api/v1/clients?skip=20&limit=10")
    destino = respuesta.headers["location"]

    assert "skip=20" in destino and "limit=10" in destino, (
        f"El redirect perdió la cadena de consulta: {destino}"
    )
    assert "://" not in destino


def test_una_respuesta_normal_no_se_toca():
    """El middleware solo actúa sobre redirecciones."""
    with TestClient(app) as cliente:
        respuesta = cliente.get("/health", headers={"Host": HOST_INTERNO})

    assert respuesta.status_code == 200
    assert "location" not in respuesta.headers
