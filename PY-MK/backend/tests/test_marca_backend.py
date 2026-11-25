"""La API se presenta como Ninja Tech.

Es lo que ve quien abre /docs, /health o la raiz del backend, y el titulo del esquema OpenAPI.

Lo que NO se prueba aqui, a proposito: los asuntos de correo siguen siendo «[NinjaSec] …» hasta que Mark confirme
que no tiene un filtro de correo que dependa del nombre viejo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

MARCA = "Ninja Tech"


def test_health_dice_ninja_tech():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "app": MARCA}


def test_el_esquema_openapi_se_llama_ninja_tech():
    info = app.openapi()["info"]
    assert info["title"] == MARCA
    assert MARCA in info["description"]


def test_la_raiz_da_la_bienvenida_con_la_marca():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert MARCA in r.json()["message"]


def test_ningun_texto_de_la_api_conserva_el_nombre_viejo():
    """Recorre lo que la API devuelve en su raiz y en /health: ninguna cadena visible lleva «NinjaSec»."""
    cliente = TestClient(app)
    for ruta in ("/", "/health"):
        assert "NinjaSec" not in cliente.get(ruta).text, ruta
