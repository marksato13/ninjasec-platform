# 36 - Módulo de órdenes de trabajo

> Estado: planificado el 2026-11-26. Diseño validado en #119.
> Primer caso del método de entrega de NinjaSec: un portal para empresas de
> servicios técnicos (aire acondicionado, cámaras, redes, ascensores…).
> Checklist: [`IMPLEMENTACION/36`](../IMPLEMENTACION/36-MODULO-ORDENES-DE-TRABAJO.md).

## Objetivo

Que una empresa que manda técnicos a atender clientes lleve en la plataforma
lo que hoy lleva en un Excel y en WhatsApp:

```
solicitud → cotización → aprobación del cliente → orden de trabajo
         → asignación de técnico → ejecución → conformidad → cierre
```

Cada empresa es una **organización** (tenant). Sus clientes ya existen en
`clients` y `client_sites`; sus técnicos son usuarios `collaborator`.

## Fuera de alcance

Facturación electrónica (se deja la lista «para facturar»), app móvil nativa,
almacén y repuestos, rutas y geolocalización, RUC del cliente y migración del
Excel (rebanada 2), tope de monto con revisión de gerencia y avisos
(rebanada 3).

## Roles

No se crea ningún rol (#119).

| Rol | Quién es | Ve |
| --- | --- | --- |
| `super_admin` | NinjaSec | Todo |
| `admin` | Gerencia y coordinación | Todo lo de su organización |
| `collaborator` | Técnico | **Solo las órdenes que le asignaron** |
| `client` | Usuario del cliente | Solo lo de su `client_id`, y de las cotizaciones solo las enviadas |

## Reglas

| Regla | Enunciado |
| --- | --- |
| R-01 | Un técnico solo puede ver las órdenes que le asignaron. Cualquier otra → **404**, no 403 |
| R-02 | Todo dato lleva `organization_id`; otra organización → 404 |
| R-03 | El cliente solo ve lo de su `client_id`; de una cotización, nunca un borrador |
| R-04 | Una cotización aprobada no se edita: se crea una versión nueva |
| R-05 | Aprueba o rechaza el cliente desde el portal; si lo registra un `admin`, con nota obligatoria |
| R-06 | Al aprobarse una cotización se crea una orden, una sola (`UNIQUE (quote_id)`) |
| R-07 | Solo se asigna a un `collaborator` activo de la misma organización |
| R-08 | *(rebanada 3)* Tope de monto con revisión de gerencia |
| R-09 | Una cotización vencida no se aprueba |
| R-10 | Todo cambio de estado deja un `work_events` y un `AuditService.record`, en la misma transacción |
| R-11 | Cancelar una orden exige nota y solo antes de empezar |
| R-12 | Si el cliente observa la entrega, la orden vuelve a `in_progress` con la observación |
| R-13 | Solo el técnico asignado inicia, pausa y termina |
| R-14 | El técnico no ve montos |

## Estados y transiciones

La tabla es código: `app/modules/work_orders/services/states.py`
(`TRANSITIONS`, `can_transition`, `requires_note`). Actores: `admin`,
`client`, `assignee` (el técnico asignado), `system`.

| Entidad | Desde → hasta | Actor | Nota |
| --- | --- | --- | --- |
| `work_request` | — → `new` | admin, client | |
| | `new` → `reviewing` | admin | |
| | `reviewing` → `quoted` | system | |
| | `reviewing` → `discarded` | admin | obligatoria |
| | `quoted` → `converted` | system | |
| | `quoted` → `reviewing` | system | |
| `quote` | — → `draft` | admin | |
| | `draft` → `sent` | admin | |
| | `sent` → `approved` | client, admin | obligatoria si admin |
| | `sent` → `rejected` | client, admin | obligatoria si admin |
| | `sent` → `expired` | system | |
| | `sent`, `expired` → `superseded` | system | |
| `work_order` | — → `pending_assignment` | system | |
| | `pending_assignment`, `assigned` → `assigned` | admin | |
| | `assigned` → `in_progress` | assignee | |
| | `in_progress` → `on_hold` | assignee | obligatoria |
| | `on_hold` → `in_progress` | assignee | |
| | `in_progress` → `completed` | assignee | obligatoria |
| | `completed` → `accepted` | client, admin | obligatoria si admin |
| | `completed` → `in_progress` | client | obligatoria (R-12) |
| | `accepted` → `closed` | admin | |
| | `pending_assignment`, `assigned` → `cancelled` | admin | obligatoria |

## Datos

Migración `20261203_01`. Cinco tablas nuevas, todas con
`organization_id NOT NULL`; el aislamiento lo hace el servicio y lo prueban
las pruebas de acceso (sin FK compuestas, #119).

| Tabla | Claves y restricciones |
| --- | --- |
| `work_requests` | `client_id`, `site_id`; `CHECK` de estado y prioridad |
| `quotes` | `request_id`; `UNIQUE (request_id, version)`; índice único parcial: una sola en `draft` o `sent` por solicitud; `total = subtotal + tax` |
| `quote_items` | `quote_id`; `quantity > 0`, `unit_price >= 0`; tipo `labor`, `material`, `travel` |
| `work_orders` | `quote_id` **único**; `UNIQUE (organization_id, number)`; técnico obligatorio salvo en `pending_assignment` y `cancelled`; índice `(organization_id, assigned_to, status)` para R-01 |
| `work_events` | Historial de las tres entidades: exactamente uno de `request_id`, `quote_id`, `work_order_id`; `internal` oculta la nota al cliente |

Por qué no reutilizar `service_requests` (formulario público, sin
`organization_id`) ni `support_tickets` (soporte posventa con su propio
ciclo): mezclarlos rompe dos flujos que funcionan.

## Trazabilidad

| Regla | Prueba |
| --- | --- |
| R-01, R-02, R-03, R-07, R-14 | `tests/test_work_orders_access.py` (#121) |
| R-04, R-05, R-09, R-11, R-12, R-13 | `tests/test_work_order_states.py` (#122) y `tests/test_work_orders_flow.py` (#121) |
| R-06, R-10 | `tests/test_work_orders_flow.py` (#121) |
