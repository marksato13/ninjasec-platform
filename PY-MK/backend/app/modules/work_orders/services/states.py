"""Tabla de transiciones del módulo de órdenes de trabajo (planificación 36).

Puro a propósito: sin base de datos ni FastAPI, para que las reglas de quién
puede mover qué se prueben solas. Los servicios llaman a ``can_transition``
antes de cambiar un estado y a ``requires_note`` para exigir la nota.

Actores: ``admin`` (gerencia o coordinación de la organización), ``client``
(usuario del cliente dueño), ``assignee`` (el técnico asignado a esa orden) y
``system`` (lo que ocurre solo, como crear la orden al aprobar la cotización).
"""

from __future__ import annotations

ADMIN = "admin"
CLIENT = "client"
ASSIGNEE = "assignee"
SYSTEM = "system"

REQUEST_STATUSES = ("new", "reviewing", "quoted", "converted", "discarded")
QUOTE_STATUSES = ("draft", "sent", "approved", "rejected", "expired", "superseded")
WORK_ORDER_STATUSES = (
    "pending_assignment",
    "assigned",
    "in_progress",
    "on_hold",
    "completed",
    "accepted",
    "closed",
    "cancelled",
)

TRANSITIONS: dict[str, dict[tuple[str | None, str], frozenset[str]]] = {
    "work_request": {
        (None, "new"): frozenset({ADMIN, CLIENT}),
        ("new", "reviewing"): frozenset({ADMIN}),
        ("reviewing", "quoted"): frozenset({SYSTEM}),
        ("reviewing", "discarded"): frozenset({ADMIN}),
        ("quoted", "converted"): frozenset({SYSTEM}),
        ("quoted", "reviewing"): frozenset({SYSTEM}),
    },
    "quote": {
        (None, "draft"): frozenset({ADMIN}),
        ("draft", "sent"): frozenset({ADMIN}),
        ("sent", "approved"): frozenset({CLIENT, ADMIN}),
        ("sent", "rejected"): frozenset({CLIENT, ADMIN}),
        ("sent", "expired"): frozenset({SYSTEM}),
        ("sent", "superseded"): frozenset({SYSTEM}),
        ("expired", "superseded"): frozenset({SYSTEM}),
    },
    "work_order": {
        (None, "pending_assignment"): frozenset({SYSTEM}),
        ("pending_assignment", "assigned"): frozenset({ADMIN}),
        ("assigned", "assigned"): frozenset({ADMIN}),
        ("assigned", "in_progress"): frozenset({ASSIGNEE}),
        ("in_progress", "on_hold"): frozenset({ASSIGNEE}),
        ("on_hold", "in_progress"): frozenset({ASSIGNEE}),
        ("in_progress", "completed"): frozenset({ASSIGNEE}),
        ("completed", "accepted"): frozenset({CLIENT, ADMIN}),
        ("completed", "in_progress"): frozenset({CLIENT}),
        ("accepted", "closed"): frozenset({ADMIN}),
        ("pending_assignment", "cancelled"): frozenset({ADMIN}),
        ("assigned", "cancelled"): frozenset({ADMIN}),
    },
}

# (entidad, desde, hasta, actor) que exigen nota: R-05, R-11, R-12 y las
# pausas y cierres del técnico.
NOTE_REQUIRED: frozenset[tuple[str, str | None, str, str]] = frozenset(
    {
        ("work_request", "reviewing", "discarded", ADMIN),
        ("quote", "sent", "approved", ADMIN),
        ("quote", "sent", "rejected", ADMIN),
        ("work_order", "in_progress", "on_hold", ASSIGNEE),
        ("work_order", "in_progress", "completed", ASSIGNEE),
        ("work_order", "completed", "accepted", ADMIN),
        ("work_order", "completed", "in_progress", CLIENT),
        ("work_order", "pending_assignment", "cancelled", ADMIN),
        ("work_order", "assigned", "cancelled", ADMIN),
    }
)


def can_transition(entity: str, from_status: str | None, to_status: str, actor: str) -> bool:
    """¿Puede ``actor`` llevar ``entity`` de ``from_status`` a ``to_status``?

    Una transición que no está en la tabla devuelve ``False``, nunca lanza.
    """
    allowed = TRANSITIONS.get(entity, {}).get((from_status, to_status))
    if allowed is None:
        return False
    return actor in allowed


def requires_note(entity: str, from_status: str | None, to_status: str, actor: str) -> bool:
    """¿Esa transición, hecha por ese actor, exige una nota escrita?"""
    return (entity, from_status, to_status, actor) in NOTE_REQUIRED
