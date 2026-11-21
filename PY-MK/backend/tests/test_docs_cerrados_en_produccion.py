"""Swagger no se publica en produccion.

`/docs`, `/redoc` y `/openapi.json` no son codigo fuente, pero exponen el
plano completo de la API: cada endpoint, cada esquema, cada campo y cada
validacion. En una plataforma publica eso es reconocimiento gratis.

El `.env.example` prometia "Modo produccion (deshabilita /docs...)" desde
hace tiempo, pero `app/main.py` nunca pasaba `docs_url=None` -- la intencion
estaba documentada y sin implementar. Y aunque lo hubiera estado, tampoco
habria funcionado: `settings.is_production` devolvia False en produccion
(ver tests/test_config_modo_produccion.py).

Estos tests **recargan `app.main` de verdad** con la configuracion alterada,
en vez de construir una FastAPI equivalente a mano. Una version anterior de
este archivo hacia lo segundo y pasaba igual con y sin el arreglo: no
probaba nada. Replicar la logica que quieres verificar solo prueba que
sabes escribirla dos veces.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

RUTAS = ("/docs", "/redoc", "/openapi.json")


def _recargar_main(monkeypatch, *, es_produccion: bool):
    """Reimporta app.main con settings alterado y devuelve la app nueva."""
    from app.core import config

    monkeypatch.setattr(config.settings, "is_production", es_produccion)
    # Las guardas de produccion de main.py abortan el arranque si falta
    # cualquiera de estas dos. Aqui se rellenan para poder llegar a la
    # construccion de FastAPI, que es lo que este archivo verifica.
    monkeypatch.setattr(config.settings, "jwt_secret_key", "secreto-de-test")
    monkeypatch.setattr(
        config.settings, "cors_origins", "https://ejemplo.test"
    )

    import app.main

    return importlib.reload(app.main).app


@pytest.fixture(autouse=True)
def _restaurar_main():
    """Deja app.main como estaba para no contaminar al resto de la suite."""
    yield
    import app.main

    importlib.reload(app.main)


def test_en_produccion_las_tres_rutas_responden_404(monkeypatch):
    app = _recargar_main(monkeypatch, es_produccion=True)
    client = TestClient(app)
    for ruta in RUTAS:
        assert client.get(ruta).status_code == 404, ruta


def test_en_produccion_no_se_filtra_el_esquema_por_openapi_json(monkeypatch):
    """La mas importante de las tres.

    /docs y /redoc son solo visores: quien sirve el contenido es
    /openapi.json. Cerrar los visores y dejar el JSON abierto no protegeria
    nada, porque cualquiera puede apuntar su propio visor a esa URL.
    """
    app = _recargar_main(monkeypatch, es_produccion=True)
    respuesta = TestClient(app).get("/openapi.json")

    assert respuesta.status_code == 404
    assert "paths" not in respuesta.text


def test_en_produccion_los_atributos_quedan_en_none(monkeypatch):
    app = _recargar_main(monkeypatch, es_produccion=True)

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


def test_en_desarrollo_la_documentacion_sigue_disponible(monkeypatch):
    """El arreglo no puede romper el flujo de trabajo diario."""
    app = _recargar_main(monkeypatch, es_produccion=False)
    client = TestClient(app)

    for ruta in RUTAS:
        assert client.get(ruta).status_code == 200, ruta


def test_en_produccion_la_api_sigue_funcionando(monkeypatch):
    """Cerrar la documentacion no puede tumbar los endpoints reales."""
    app = _recargar_main(monkeypatch, es_produccion=True)

    assert TestClient(app).get("/health").status_code == 200
