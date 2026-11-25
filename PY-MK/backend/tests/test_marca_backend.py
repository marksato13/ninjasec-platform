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


# --- El nombre NO puede quedar fijado en otro sitio -------------------------------------------------------------
# `app_name` se lee del entorno (APP_NAME). Si el compose, el .env.example o el instalador siguen diciendo
# «NinjaSec», ese valor PISA el que se cambia en config.py y en produccion el backend sigue presentandose con el
# nombre viejo. Las pruebas de arriba no lo ven porque el entorno de pruebas no define APP_NAME: paso en el PR #12.

import re  # noqa: E402
from pathlib import Path  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def _lineas_con_app_name():
    archivos = [
        RAIZ / "infra" / "docker-compose.yml",
        RAIZ / "infra" / "docker-compose.prod.yml",
        RAIZ / ".env.example",
        RAIZ / "infra" / "instalar-en-vm.sh",
    ]
    for a in archivos:
        assert a.exists(), f"falta {a}"
        for n, linea in enumerate(a.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?<![A-Z_])APP_NAME\b", linea) and not linea.lstrip().startswith("#"):
                yield a.name, n, linea.strip()


def test_hay_donde_fijar_el_nombre():
    """Si esto devuelve vacio, la prueba de abajo no estaria comprobando nada."""
    assert len(list(_lineas_con_app_name())) >= 4


def test_ningun_archivo_de_configuracion_fija_el_nombre_viejo():
    malas = [f"{a}:{n} {t}" for a, n, t in _lineas_con_app_name() if "NinjaSec" in t]
    assert not malas, "estas lineas pisan el nombre nuevo en produccion:\n" + "\n".join(malas)
