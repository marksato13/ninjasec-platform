# Flujo entre clientes, consolas, inventario y tickets

## Objetivo

Definir el flujo relacional entre clientes, consolas, inventario, revisiones, hallazgos y tickets, mapeado a los modulos ya existentes en NinjaSec.

## Entidad principal

**Cliente** (`Client`) es la entidad base de toda la operacion.

Cada cliente puede tener:

- varias sedes (nuevo `client_sites`)
- varios activos (inventario via `Device`)
- varias consolas (via `Integration`)
- varias revisiones (nuevo `security_reviews`)
- multiples hallazgos (nuevo `review_findings`)
- multiples tickets (nuevo `support_tickets` o extension de `ServiceRequest`)

## Mapeo a NinjaSec (actual)

- Cliente -> `Client`
- Consola -> `Integration` (tipo de conector, base_url, estado)
- Inventario -> `Device` (asociado a consola por `integration_id`)
- Revision -> `security_reviews` (nuevo)
- Hallazgo -> `review_findings` (nuevo)
- Ticket -> `support_tickets` (nuevo) o `ServiceRequest` extendido
- Informe final -> `Report` + `ReportRun`

## Flujo logico (alto nivel)

Cliente -> Consolas -> Activos monitoreados -> Revisiones -> Hallazgos -> Tickets -> Informe final

## Explicacion operativa

1) Un cliente registra sus consolas de seguridad (integraciones).
2) Cada consola monitorea activos (`Device`) asociados a esa integracion.
3) El analista programa y ejecuta revisiones sobre esas consolas.
4) La revision genera hallazgos (incidentes, alertas, brechas).
5) Algunos hallazgos se convierten en tickets de soporte.
6) Todo se consolida en un informe por cliente y periodo.

## Relaciones clave

- `Client` 1..* `Integration`
- `Integration` 1..* `Device`
- `Client` 1..* `SecurityReview`
- `SecurityReview` 1..* `ReviewFinding`
- `ReviewFinding` 0..* `SupportTicket`
- `Client` 1..* `Report`

## Reglas de integracion

- Todo registro debe estar vinculado a un `client_id` de forma directa o indirecta.
- El inventario se vincula al cliente por su consola (`Device.integration_id -> Integration.client_id`).
- Los tickets deben poder asociarse a:
  - cliente
  - consola
  - activo
  - revision
- La auditoria registra cambios de estado en revisiones, hallazgos y tickets.

## Ejemplo de trazabilidad

- Cliente: Empresa X
- Consola: FortiGate (Integration)
- Activo: FW-FG-01 (Device)
- Revision: R-2026-04
- Hallazgo: FW reglas expuestas
- Ticket: T-2026-0412
- Reporte: Informe Ejecutivo Abril 2026

## Salida esperada

El supervisor puede filtrar por cliente y periodo y obtener un informe consolidado con:

- estado del inventario
- resumen de revisiones
- hallazgos por severidad
- tickets abiertos/cerrados
