# Planeamiento iteracion - Gestion de consolas, inventario y soporte

## Objetivo

Disenar la iteracion para un sistema que centraliza clientes, consolas de seguridad, inventario, revisiones periodicas, hallazgos, tickets de soporte y reportes con exportacion a Excel, manteniendo trazabilidad desde 2026.

## Problema que resuelve

Actualmente la gestion se reparte en correos, hojas separadas y tickets sin consolidacion, lo que genera perdida de trazabilidad, baja visibilidad de hallazgos y reportes no estandarizados. Esta iteracion organiza la operacion en un unico flujo.

## Alcance de la iteracion (solo lo solicitado)

- Registro de empresas clientes.
- Administracion de inventario de activos y consolas por cliente.
- Programacion y registro de revisiones de seguridad.
- Documentacion de hallazgos y recomendaciones.
- Administracion de tickets de soporte tecnico.
- Asociacion de tickets a cliente, consola, activo o revision.
- Reportes con exportacion Excel en formato corporativo.
- Trazabilidad historica desde 2026 en adelante.
- Indicadores operativos y de seguridad.

## Adaptacion al sistema actual (NinjaSec)

- Clientes: reutilizar `Client` y `ClientProfile` como entidad base de empresa.
- Consolas de seguridad: mapear a `Integration` como consola (conector, base_url, estado).
- Inventario: reutilizar `Device` como activo por cliente e integracion.
- Reportes: extender modulo `Reports` para export Excel corporativo.
- Auditoria: usar `AuditLog` para trazabilidad de acciones criticas.

## Modelo de datos (alto nivel)

- SecurityReview (nuevo)
  - client_id, console_id (integration_id), scheduled_at, executed_at, status, reviewer_user_id.
- ReviewFinding (nuevo)
  - review_id, severity, title, description, status, evidence_url.
- ReviewRecommendation (nuevo)
  - review_id, finding_id, recommendation, owner_user_id, due_date, status.
- SupportTicket (nuevo o extension de ServiceRequest)
  - client_id, console_id, device_id, review_id, category, priority, status, assigned_to, opened_at, closed_at.
- TicketLink (nuevo)
  - ticket_id, entity_type, entity_id (cliente, consola, activo, revision).
- ReportExport (nuevo)
  - report_id, format (xlsx), template_name, generated_by, generated_at, file_url.

## Flujos principales

1) Cliente y consola
   - Admin registra cliente.
   - Admin registra consolas (integraciones) y vincula al cliente.

2) Inventario
   - Admin/analista agrega activos asociados a cliente y consola.

3) Revision de seguridad
   - Analista agenda revision y la ejecuta.
   - Se registran hallazgos y recomendaciones.

4) Tickets de soporte
   - Analista soporte registra ticket y lo vincula a cliente/consola/activo/revision.
   - Seguimiento hasta cierre con trazabilidad.

5) Reportes y exportacion
   - Supervisor genera reporte consolidado y exporta Excel con formato corporativo.

## Roles y permisos (mapeo a roles actuales)

- Administrador del sistema -> super_admin / admin
  - configura catalogos, usuarios, consolas, inventario, permisos y reportes.
- Analista de seguridad -> collaborator
  - crea revisiones, hallazgos y recomendaciones.
- Analista de soporte tecnico -> collaborator
  - crea y actualiza tickets.
- Supervisor / coordinador -> admin
  - valida revisiones, aprueba informes, ve indicadores.
- Cliente -> client
  - lectura de inventario, tickets, revisiones e informes autorizados.

## UI/UX (admin y portal)

### Admin

- Clientes: cards + detalle.
- Consolas: listado por cliente con estado y salud.
- Inventario: activos por cliente y consola.
- Revisiones: agenda, detalle con hallazgos y recomendaciones.
- Tickets: bandeja por prioridad, estado y cliente.
- Reportes: generacion y export Excel.

### Portal cliente

- Inventario visible por cliente.
- Tickets abiertos/cerrados.
- Revisiones e informes autorizados.

## Reportes y exportacion Excel

- Endpoint de exportacion por cliente y rango de fechas.
- Plantilla corporativa (logo, colores, encabezado, pie, resumen ejecutivo).
- Export de:
  - revisiones y hallazgos
  - tickets por estado y SLA
  - inventario por cliente/consola

## Indicadores operativos y de seguridad

- % revisiones ejecutadas vs programadas.
- Hallazgos por severidad y estado.
- Tickets abiertos, resueltos y SLA promedio.
- Activos por cliente y cobertura de consola.

## Trazabilidad y auditoria

- Registrar en `audit_logs` acciones: alta/edicion de consola, revision, hallazgo, ticket y reporte.
- Mantener fechas de creacion/actualizacion y filtros por anio >= 2026.

## Validacion (criterios de salida)

- Cliente puede ver su inventario, tickets y revisiones autorizadas.
- Analista de seguridad puede registrar revision y hallazgos.
- Analista de soporte puede registrar y cerrar tickets.
- Supervisor puede aprobar reportes y ver indicadores.
- Export Excel genera archivo con formato corporativo y datos consistentes.
