"""Las fases del recorrido de un proyecto.

Salen de `COMERCIAL/01-COMO-TRABAJAMOS.md`: los cuatro momentos de un proyecto no son
servicios sueltos sino fases de un mismo recorrido, y el acompanamiento es opcional.

Las CLAVES son iguales para todos los proyectos (es lo que se guarda en la base); lo que
cambia es el ROTULO, segun la linea:

    infra   Diagnostico, Planificacion, Implementacion, Transferencia, Acompanamiento
    dev     Descubrimiento, Diseno, Desarrollo, Entrega, Soporte

Asi un cliente de desarrollo lee su recorrido con las palabras de su mundo, y el sistema
sigue teniendo un solo conjunto de fases que contar y comparar.
"""

from __future__ import annotations

from typing import Literal

Linea = Literal["dev", "infra"]

CLAVES: tuple[str, ...] = (
    "diagnostico", "planificacion", "implementacion", "transferencia", "acompanamiento",
)

ROTULOS: dict[str, dict[str, tuple[str, str]]] = {
    "infra": {
        "diagnostico": ("Diagnóstico", "Miramos qué tienes y qué falla. No tocamos nada."),
        "planificacion": ("Planificación", "Definimos qué se hace, cómo y en qué orden."),
        "implementacion": ("Implementación", "Lo construimos y lo probamos."),
        "transferencia": ("Transferencia", "Tu equipo queda con el manual y la autonomía."),
        "acompanamiento": ("Acompañamiento", "Seguimos a tu lado, mes a mes."),
    },
    "dev": {
        "diagnostico": ("Descubrimiento", "Entendemos qué necesitas y para quién."),
        "planificacion": ("Diseño", "Prototipo, arquitectura y alcance de la primera entrega."),
        "implementacion": ("Desarrollo", "Construimos por entregas que puedes probar."),
        "transferencia": ("Entrega", "Puesta en línea, documentación y capacitación."),
        "acompanamiento": ("Soporte", "Correcciones y mejoras después de salir."),
    },
}


def es_valida(clave: str) -> bool:
    return clave in CLAVES


def indice(clave: str) -> int:
    return CLAVES.index(clave) if clave in CLAVES else 0


def linea_de(categoria_servicio: str | None) -> Linea:
    """'desarrollo' es dev; todo lo demas (infraestructura, nube, seguridad) es infra."""
    return "dev" if (categoria_servicio or "").lower() == "desarrollo" else "infra"
