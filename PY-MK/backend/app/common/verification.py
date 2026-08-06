"""Re-verificacion al editar un registro ya aprobado (21-P-01 / 17-P-04).

El flujo `declarar -> aprobar -> editar` permitia elevar una capacidad ya
verificada sin pasar de nuevo por revision: se aprobaba "Cisco basico" y
despues se editaba a "CCIE", conservando el sello de verificado.

Como el directorio de colaboradores es material de cara al cliente, la
aprobacion tiene que referirse a lo que un revisor vio realmente. Si el
contenido cambia, la aprobacion deja de aplicar.

La regla vive aqui y no en cada router para que skills y certificaciones
no puedan divergir.
"""

from __future__ import annotations

from typing import Any


def revoke_verification_if_changed(
    entity: Any,
    payload: dict[str, Any],
    *,
    material_fields: tuple[str, ...],
    pending_value: Any,
) -> list[str]:
    """Devuelve la aprobacion a `pending` si cambio algun campo material.

    Compara valor a valor: reenviar el mismo dato no revoca nada, de modo
    que guardar un formulario sin tocarlo no penaliza al colaborador.

    Devuelve la lista de campos que cambiaron y motivaron la revocacion;
    vacia si no hubo que revocar. El llamador la usa para el audit log.

    No hace commit: el router decide cuando persistir.
    """
    changed = [
        field
        for field in material_fields
        if field in payload and payload[field] != getattr(entity, field)
    ]
    if not changed:
        return []

    # Solo tiene sentido revocar lo que estaba aprobado. Un registro en
    # `pending` ya esta donde debe, y uno rechazado no debe "ascender" a
    # pendiente por una edicion.
    if getattr(entity, "status", None) != _approved_of(entity):
        return []

    entity.status = pending_value
    entity.verified_by = None
    entity.verified_at = None
    return changed


def _approved_of(entity: Any) -> Any:
    """El valor `APPROVED` del enum que use esta entidad."""
    return type(entity.status).APPROVED
