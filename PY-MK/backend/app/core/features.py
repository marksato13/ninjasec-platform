"""Cápsulas de funcionalidad: módulos que existen pero pueden estar apagados.

El problema que resuelve está en
`DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md`. En corto: hay módulos
terminados a medias, y uno de ellos devuelve datos que parecen reales y no
lo son. Exponerlos en la web pública es un riesgo comercial.

Ni se borran ni se exponen: se apagan. El código se queda íntegro y un
interruptor decide si se registra.

Una cápsula es una entrada en este registro, no un `if` repartido por el
código. Para cambiar qué entra en ella se edita una tupla, no se persigue
código por veinte archivos.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Capsula:
    """Un conjunto de módulos que se enciende o se apaga junto."""

    nombre: str
    descripcion: str
    motivo: str
    """Por qué está apagada. Si no hay un motivo escrito, no debería estarlo."""

    modulos: tuple[str, ...] = field(default_factory=tuple)
    """Módulos de `app/modules/` que la componen. Documental, para auditar."""

    rutas_api: tuple[str, ...] = field(default_factory=tuple)
    """Prefijos de ruta que NO se registran cuando está apagada."""

    rutas_ui: tuple[str, ...] = field(default_factory=tuple)
    """Rutas del panel que el frontend esconde. Aquí solo se declaran."""

    activa_por_defecto: bool = False


CAPSULAS: dict[str, Capsula] = {
    "telemetria": Capsula(
        nombre="telemetria",
        descripcion=(
            "Conectores a equipos, recolección de configuración y todo lo que "
            "se calcula sobre ella: hardening, puntuación de riesgo, índice de "
            "salud e informe SOC."
        ),
        motivo=(
            "Los conectores son simulados: simulate_connector_test() devuelve "
            "reachable=True sin contactar ningún equipo. El informe SOC, el "
            "hardening y el índice de salud corren sobre ese dato inventado."
        ),
        modulos=(
            "integrations",
            "collection",
            "hardening",
            "risk_scoring",
            "health_score",
        ),
        rutas_api=(
            "/integrations",
            "/collection",
            "/hardening",
            "/risk-scoring",
            "/health-score",
        ),
        rutas_ui=(
            "/dashboard/integrations",
            "/dashboard/hardening",
            "/dashboard/soc-report",
        ),
        activa_por_defecto=False,
    ),
}


class CapsulaDesconocida(ValueError):
    """Se pidió activar una cápsula que no está en el registro.

    Falla al arrancar, a propósito: un nombre mal escrito en la variable de
    entorno es silencioso de la peor manera -- crees que encendiste algo y no.
    """


def _nombres_pedidos(valor: str | None) -> set[str]:
    """Parte `CAPSULAS_ACTIVAS` en nombres, tolerando espacios y vacíos."""
    if not valor:
        return set()
    return {parte.strip() for parte in valor.split(",") if parte.strip()}


def capsulas_activas(valor_entorno: str | None) -> set[str]:
    """Nombres de las cápsulas encendidas.

    Parte de las que están activas por defecto y añade las que pida
    `CAPSULAS_ACTIVAS`. Un nombre que no exista en el registro **rompe el
    arranque**, en lugar de ignorarse.
    """
    pedidas = _nombres_pedidos(valor_entorno)
    desconocidas = pedidas - set(CAPSULAS)
    if desconocidas:
        raise CapsulaDesconocida(
            "CAPSULAS_ACTIVAS nombra cápsulas que no existen: "
            f"{', '.join(sorted(desconocidas))}. "
            f"Las que hay son: {', '.join(sorted(CAPSULAS))}."
        )
    por_defecto = {c.nombre for c in CAPSULAS.values() if c.activa_por_defecto}
    return por_defecto | pedidas


def rutas_apagadas(valor_entorno: str | None) -> tuple[str, ...]:
    """Prefijos de API que no deben registrarse."""
    activas = capsulas_activas(valor_entorno)
    apagadas: list[str] = []
    for capsula in CAPSULAS.values():
        if capsula.nombre not in activas:
            apagadas.extend(capsula.rutas_api)
    return tuple(apagadas)


def esta_activa(nombre: str, valor_entorno: str | None) -> bool:
    """Si una cápsula concreta está encendida.

    Pensado para el código que necesita preguntarlo, no para repartir `if`:
    la vía normal es que la ruta no se registre.
    """
    if nombre not in CAPSULAS:
        raise CapsulaDesconocida(
            f"No existe la cápsula '{nombre}'. "
            f"Las que hay son: {', '.join(sorted(CAPSULAS))}."
        )
    return nombre in capsulas_activas(valor_entorno)


def inventario(valor_entorno: str | None) -> list[dict[str, object]]:
    """El estado de todas las cápsulas, para exponerlo y para auditarlo.

    El frontend lo consume para saber qué pantallas pintar. No lleva nada
    sensible: son nombres de módulo y de ruta, que además están en el
    repositorio público.
    """
    activas = capsulas_activas(valor_entorno)
    return [
        {
            "nombre": capsula.nombre,
            "descripcion": capsula.descripcion,
            "activa": capsula.nombre in activas,
            "motivo": None if capsula.nombre in activas else capsula.motivo,
            "rutas_ui": list(capsula.rutas_ui),
        }
        for capsula in sorted(CAPSULAS.values(), key=lambda c: c.nombre)
    ]
