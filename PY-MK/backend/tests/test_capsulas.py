"""Una cápsula apagada no deja rutas accesibles, y encendida las devuelve todas.

El criterio está en `DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md`.

Lo que estas pruebas vigilan es la diferencia entre **apagar** y **esconder**:
si el router no se registra, la ruta no existe y el 404 es el natural de
FastAPI. Esconder solo el menú deja la ruta en pie y cualquiera que teclee la
URL entra.
"""

from __future__ import annotations

import importlib
import os

import pytest

from app.core import features
from app.core.features import (
    CAPSULAS,
    CapsulaDesconocida,
    capsulas_activas,
    esta_activa,
    inventario,
    rutas_apagadas,
)


PREFIJOS_TELEMETRIA = (
    "/integrations",
    "/collection",
    "/hardening",
    "/risk-scoring",
    "/health-score",
)


def _rutas_registradas(valor_capsulas: str | None) -> set[str]:
    """Recarga el router con un valor concreto de CAPSULAS_ACTIVAS.

    Hay que recargar de verdad: el registro de rutas ocurre al importar, así
    que una prueba que solo monkeypatchee los settings no prueba nada. Es el
    mismo error que ya se cometió una vez con las pruebas de Swagger, que
    construían una aplicación réplica y pasaban con y sin el arreglo.
    """
    import app.api.router
    import app.core.config

    original = app.core.config.settings.capsulas_activas
    try:
        app.core.config.settings.capsulas_activas = valor_capsulas
        importlib.reload(app.api.router)
        return {ruta.path for ruta in app.api.router.api_router.routes}
    finally:
        app.core.config.settings.capsulas_activas = original
        importlib.reload(app.api.router)


def _rutas_de_la_capsula(rutas: set[str]) -> set[str]:
    return {r for r in rutas if any(r.startswith(p) for p in PREFIJOS_TELEMETRIA)}


# --------------------------------------------------------------------------
# Apagada: la ruta no existe
# --------------------------------------------------------------------------


def test_apagada_no_registra_ninguna_ruta_de_la_capsula():
    presentes = _rutas_de_la_capsula(_rutas_registradas(None))

    assert presentes == set(), (
        "Con telemetria apagada no debe quedar ninguna ruta accesible. "
        f"Quedaron: {sorted(presentes)}"
    )


def test_apagada_no_rompe_los_modulos_que_solo_hacen_join():
    """dashboard, reports y vulnerability_inventory usan Integration como join.

    Esto es lo que hubo que medir antes de decidir el límite: esos módulos
    importan Integration para filtrar por organización, no para hablar con
    un equipo. Apagar la cápsula les quita filas, no los rompe.
    """
    rutas = _rutas_registradas(None)

    for prefijo in (
        "/dashboard",
        "/reports",
        "/vulnerability-inventory",
        "/alerts",
        "/security-reviews",
    ):
        assert any(r.startswith(prefijo) for r in rutas), (
            f"Apagar telemetria se llevó por delante {prefijo}, que no depende "
            "de los conectores."
        )


# --------------------------------------------------------------------------
# Encendida: vuelve todo
# --------------------------------------------------------------------------


def test_encendida_devuelve_las_rutas():
    presentes = _rutas_de_la_capsula(_rutas_registradas("telemetria"))

    assert presentes, "Encender telemetria debe devolver sus rutas"


def test_encender_solo_anade_no_quita():
    apagada = _rutas_registradas(None)
    encendida = _rutas_registradas("telemetria")

    assert apagada < encendida, (
        "Encender una cápsula solo puede añadir rutas. Desaparecieron: "
        f"{sorted(apagada - encendida)}"
    )


def test_los_cinco_modulos_vuelven():
    rutas = _rutas_registradas("telemetria")

    for prefijo in PREFIJOS_TELEMETRIA:
        assert any(r.startswith(prefijo) for r in rutas), (
            f"{prefijo} no volvió al encender telemetria"
        )


# --------------------------------------------------------------------------
# El parseo de la variable de entorno
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valor",
    [None, "", "   ", ",", " , ,"],
)
def test_valores_vacios_no_encienden_nada(valor):
    assert capsulas_activas(valor) == set()


@pytest.mark.parametrize(
    "valor",
    ["telemetria", " telemetria ", "telemetria,", ",telemetria"],
)
def test_tolera_espacios_y_comas_sueltas(valor):
    assert capsulas_activas(valor) == {"telemetria"}


def test_un_nombre_desconocido_rompe_el_arranque():
    """Una errata no se ignora: se grita.

    Ignorarla es el peor fallo posible aquí, porque crees que encendiste algo
    y la pantalla simplemente no está.
    """
    with pytest.raises(CapsulaDesconocida) as capturado:
        capsulas_activas("telemetria,telemetria-con-errata")

    mensaje = str(capturado.value)
    assert "telemetria-con-errata" in mensaje
    assert "telemetria" in mensaje, "El error debe decir qué nombres sí existen"


def test_preguntar_por_una_capsula_que_no_existe_tambien_rompe():
    with pytest.raises(CapsulaDesconocida):
        esta_activa("no-existe", None)


# --------------------------------------------------------------------------
# El inventario que consume el frontend
# --------------------------------------------------------------------------


def test_el_inventario_dice_el_motivo_cuando_esta_apagada():
    entradas = {e["nombre"]: e for e in inventario(None)}
    telemetria = entradas["telemetria"]

    assert telemetria["activa"] is False
    assert telemetria["motivo"], (
        "Una cápsula apagada sin motivo escrito no debería estar apagada"
    )
    assert "simulate_connector_test" in telemetria["motivo"]


def test_el_inventario_no_da_motivo_cuando_esta_encendida():
    entradas = {e["nombre"]: e for e in inventario("telemetria")}

    assert entradas["telemetria"]["activa"] is True
    assert entradas["telemetria"]["motivo"] is None


def test_el_inventario_lista_las_rutas_de_interfaz():
    """El frontend necesita saber qué pantallas no pintar."""
    entradas = {e["nombre"]: e for e in inventario(None)}

    assert entradas["telemetria"]["rutas_ui"], (
        "Sin rutas_ui el frontend no sabe qué esconder"
    )


# --------------------------------------------------------------------------
# Coherencia del registro
# --------------------------------------------------------------------------


def test_toda_capsula_apagada_por_defecto_tiene_motivo():
    for capsula in CAPSULAS.values():
        if not capsula.activa_por_defecto:
            assert capsula.motivo.strip(), (
                f"La cápsula '{capsula.nombre}' está apagada sin explicar por qué"
            )


def test_rutas_apagadas_coincide_con_el_registro():
    apagadas = set(rutas_apagadas(None))

    assert apagadas == set(CAPSULAS["telemetria"].rutas_api)


def test_ninguna_ruta_declarada_se_queda_sin_apagar():
    """Si alguien añade un prefijo al registro y no existe, se nota aquí.

    Protege el caso contrario al habitual: no que sobre una ruta, sino que el
    registro declare apagar algo que ya no se llama así. Entonces la cápsula
    cree estar apagada y la ruta sigue viva.
    """
    rutas_vivas = _rutas_registradas("telemetria")

    for prefijo in CAPSULAS["telemetria"].rutas_api:
        assert any(r.startswith(prefijo) for r in rutas_vivas), (
            f"El registro declara el prefijo '{prefijo}', pero ninguna ruta "
            "empieza así. Si el router se renombró, apagar la cápsula ya no "
            "apaga esa ruta."
        )


# --------------------------------------------------------------------------
# El frontend: que ninguna pantalla de la capsula se quede sin guarda
# --------------------------------------------------------------------------


def test_toda_pagina_de_una_capsula_llama_a_rutaDisponible():
    """Ninguna página bajo una ruta de cápsula puede quedarse sin guarda.

    Esta prueba existe porque el descuido ya se cometió: en la primera pasada
    se guardaron las tres páginas principales y se olvidó
    `integrations/[id]/page.tsx`, que era alcanzable con la cápsula apagada.

    `rutaDisponible` compara por prefijo, pero eso solo sirve si la página la
    llama. Una ruta nueva bajo `/dashboard/integrations/` vuelve a abrir el
    agujero, y esto lo caza.
    """
    import re
    from pathlib import Path

    # tests/ -> backend/ -> PY-MK/ ; el frontend es hermano del backend.
    raiz = Path(__file__).resolve().parents[2] / "frontend" / "src" / "app"
    if not raiz.exists():  # pragma: no cover - el backend se puede probar solo
        pytest.skip("No hay frontend en este checkout")

    sin_guarda: list[str] = []
    for capsula in CAPSULAS.values():
        for ruta_ui in capsula.rutas_ui:
            # /dashboard/integrations -> (admin)/dashboard/integrations
            relativa = ruta_ui.lstrip("/")
            carpeta = raiz / "(admin)" / relativa
            if not carpeta.exists():
                sin_guarda.append(f"{ruta_ui} (la carpeta no existe: {carpeta})")
                continue
            for pagina in carpeta.rglob("page.tsx"):
                # La LLAMADA, no la mencion. Buscar la cadena a secas hacia
                # esta prueba de carton: la encontraba en un comentario que
                # hablaba de ella y daba verde con la guarda quitada.
                # Comprobado: sin esto, la prueba pasa igual.
                if not re.search(
                    r"if\s*\(\s*!\s*rutaDisponible\s*\(",
                    pagina.read_text(encoding="utf-8"),
                ):
                    sin_guarda.append(str(pagina.relative_to(raiz)))

    assert not sin_guarda, (
        "Hay páginas de una cápsula sin llamar a rutaDisponible(), así que son "
        "alcanzables con la cápsula apagada:\n  " + "\n  ".join(sin_guarda)
    )


# --------------------------------------------------------------------------
# El contrato OpenAPI
# --------------------------------------------------------------------------


def test_el_contrato_exportado_incluye_las_rutas_de_la_capsula():
    """El contrato describe lo que ofrece el codigo, no lo que sirve un deploy.

    Si el esquema siguiera al interruptor, apagar una capsula se leeria como
    la desaparicion de 13 rutas -- un cambio rompedor -- y el check de
    contrato empezaria a gritar cada vez que se toca una variable de entorno.
    Un check que grita por todo deja de cazar las roturas de verdad.

    Esto paso de hecho: el job `Contrato OpenAPI` se puso rojo en el PR que
    introdujo las capsulas. La prueba fija la decision para que nadie
    "arregle" el exportador en la direccion contraria.
    """
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    guion = Path(__file__).resolve().parents[1] / "scripts" / "exportar_openapi.py"
    if not guion.exists():  # pragma: no cover
        pytest.skip("No hay script de exportacion en este checkout")

    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "openapi.json"
        completado = subprocess.run(
            [sys.executable, str(guion), str(destino)],
            cwd=str(guion.parents[1]),
            env={**os.environ, "PYTHONPATH": "."},
            capture_output=True,
            text=True,
            # Sin esto, bajo la captura de salida de pytest en Windows el
            # lanzamiento falla con "WinError 6: controlador no valido":
            # pytest sustituye stdin por un objeto sin descriptor real.
            # Solo se ve en la suite completa, no al correr este archivo solo.
            stdin=subprocess.DEVNULL,
        )
        assert completado.returncode == 0, completado.stderr
        esquema = json.loads(destino.read_text(encoding="utf-8"))

    rutas = set(esquema["paths"])
    for prefijo in CAPSULAS["telemetria"].rutas_api:
        completo = f"/api/v1{prefijo}"
        assert any(r.startswith(completo) for r in rutas), (
            f"El contrato exportado no incluye {completo}. Si el exportador "
            "dejo de encender todas las capsulas, apagar una se leera como un "
            "cambio rompedor en cada PR."
        )
