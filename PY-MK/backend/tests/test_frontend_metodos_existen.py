"""Cada llamada PATCH/PUT/DELETE del frontend existe en el backend con ese metodo.

Auditoria funcional del 2026-11-25: editar un proyecto, un usuario, una sede o un
contacto respondia 405 en produccion, porque el frontend enviaba PATCH y el backend
solo tenia PUT. Ninguna prueba lo vio: el backend probaba PUT y el frontend no se
probaba contra el backend. Esta prueba lee `frontend/src/lib/api/*.ts` y compara cada
(metodo, ruta) con el contrato OpenAPI real.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.main import app

API_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "api"
PREFIJO = "/api/v1"

# request<T>(`/ruta/${x}`, { method: "PATCH" ...  — tambien con la ruta en "..."
LLAMADA = re.compile(
    r"""request<[^>]*>\(\s*[`"](?P<ruta>/[^`"]*)[`"]\s*,\s*\{[^}]*?method:\s*"(?P<metodo>PATCH|PUT|DELETE)\"""",
    re.S,
)


def _normalizar(ruta: str) -> str:
    """`/projects/${id}` y `/projects/{project_id}` se comparan como `/projects/{}`."""
    ruta = ruta.split("?")[0]
    ruta = re.sub(r"\$\{[^}]+\}", "{}", ruta)
    ruta = re.sub(r"\{[^}]+\}", "{}", ruta)
    return ruta.rstrip("/") or "/"


def _llamadas_del_frontend() -> list[tuple[str, str, str]]:
    llamadas = []
    for archivo in sorted(API_DIR.glob("*.ts")):
        for m in LLAMADA.finditer(archivo.read_text(encoding="utf-8")):
            llamadas.append((archivo.name, m["metodo"].lower(), _normalizar(m["ruta"])))
    return llamadas


def _rutas_del_backend() -> dict[str, set[str]]:
    rutas: dict[str, set[str]] = {}
    for ruta, operaciones in app.openapi()["paths"].items():
        if ruta.startswith(PREFIJO):
            rutas.setdefault(_normalizar(ruta[len(PREFIJO):]), set()).update(operaciones)
    return rutas


@pytest.mark.skipif(not API_DIR.exists(), reason="sin el frontend junto al backend")
def test_el_frontend_no_llama_a_metodos_que_el_backend_no_tiene():
    llamadas = _llamadas_del_frontend()
    assert len(llamadas) > 20, f"El patron no encontro llamadas en {API_DIR}; revisar LLAMADA"
    rutas = _rutas_del_backend()
    rotas = [
        f"{archivo}: {metodo.upper()} {ruta} (el backend tiene {sorted(rutas.get(ruta, set())) or 'nada'})"
        for archivo, metodo, ruta in llamadas
        if metodo not in rutas.get(ruta, set())
    ]
    assert not rotas, "Llamadas del frontend que darian 405 o 404:\n" + "\n".join(rotas)
