# Flujos operativos integrados - Iteracion (con NinjaSec actual)

## Objetivo

Documentar el flujo general del sistema solicitado y como se integra con los modulos ya existentes en NinjaSec, indicando extensiones o nuevos modulos cuando haga falta.

## Mapeo con modulos existentes

- Clientes -> `Client` + `ClientProfile` (contactos base).
- Consolas de seguridad -> `Integration` (una consola por cliente).
- Inventario -> `Device` (activo asociado a una consola por `integration_id`).
- Reportes -> `Report` + `ReportRun` (soporta salida de archivos).
- Auditoria -> `AuditLog` (trazabilidad de acciones).
- Soporte -> `ServiceRequest` existe, pero no cubre ciclo completo de ticket.

## Modulos a extender o crear

- ClientSites (sedes): nueva tabla `client_sites` para multiples sedes por cliente.
- ClientContacts (contactos): nueva tabla `client_contacts` para contactos operativos/ejecutivos.
- ClientServices (servicios contratados): tabla puente `client_services` (client_id + service_id + fechas).
- Integrations: extender `Integration` con campos de licencia, entorno y responsables.
- SecurityReview: nuevas tablas `security_reviews`, `review_findings`, `review_recommendations`.
- SupportTicket: nueva tabla `support_tickets` (o extender `ServiceRequest`).
- TicketLink: tabla de asociaciones (ticket con cliente/consola/activo/revision).
- ReportExport (opcional): si se requiere plantilla corporativa externa a `ReportRun`.

## Flujo 1. Registro de cliente

### Descripcion

El administrador registra la empresa cliente, sus sedes, contactos y servicios contratados. Luego habilita el acceso del cliente.

### Integracion con NinjaSec

- Reutilizar `Client` para datos base.
- Reutilizar `ClientProfile` para usuarios cliente (acceso al portal).
- Crear `client_sites` y `client_contacts` para sedes/contacts multiples.
- Crear `client_services` para vincular servicios (`Service`) contratados.

### Entidades y endpoints sugeridos

- `POST /clients` (existente)
- `POST /client-sites`
- `POST /client-contacts`
- `POST /client-services`
- `POST /users` + `POST /client-profiles` (acceso portal)

### UI

- Admin: cards de clientes con tabs (Info, Sedes, Contactos, Servicios, Acceso).
- Portal cliente: perfil de empresa y contactos autorizados.

### Auditoria

- Log en `audit_logs`: alta/edicion de cliente, sede, contacto y servicio.

## Flujo 2. Registro de inventario

### Descripcion

Se registran activos del cliente, se clasifican por tipo, se asocian a consola o servicio y se guarda estado operativo y datos tecnicos.

### Integracion con NinjaSec

- Usar `Device` como activo.
- La asociacion al cliente se resuelve via `Device.integration_id -> Integration.client_id`.
- Para clasificacion, usar `device_type` y `status` ya existentes.

### Entidades y endpoints sugeridos

- `GET/POST /devices` (existente)
- `PATCH /devices/{id}` para estado operativo y datos tecnicos.
- Filtro por cliente via integracion (`?client_id=`) en backend.

### UI

- Admin: inventario por cliente y consola con cards por tipo.
- Portal cliente: inventario con filtros por tipo/estado.

### Auditoria

- Log en `audit_logs`: alta/actualizacion de activos.

## Flujo 3. Registro de consolas

### Descripcion

Se registra la consola de seguridad del cliente, se indica tipo, entorno, licencia, responsables y se asocia a activos o grupos monitoreados.

### Integracion con NinjaSec

- Usar `Integration` como consola.
- Extender `Integration` con:
  - `environment` (prod/dev/lab)
  - `license_type`, `license_expires_at`
  - `owner_user_id` o `responsible_contact_id`
  - `monitored_groups_json` (opcional)

### Entidades y endpoints sugeridos

- `GET/POST /integrations` (existente)
- `PATCH /integrations/{id}` para licencia/entorno/responsables
- `GET /devices?integration_id=` para activos asociados

### UI

- Admin: detalle de consola con estado de salud, licencia y activos asociados.
- Portal cliente: vista de consolas autorizadas.

### Auditoria

- Log en `audit_logs`: alta/edicion de consola y cambios de licencia.

## Flujo 4. Revision de consola

### Descripcion

El analista programa o crea una revision, selecciona cliente y consola, registra hallazgos/alertas/incidentes, adjunta evidencias, emite recomendaciones y cierra la revision o genera tickets derivados.

### Integracion con NinjaSec

- Nuevo modulo `security_reviews`.
- Hallazgos: `review_findings` con severidad y estado.
- Recomendaciones: `review_recommendations` con responsable y fecha.
- Evidencias: se pueden reutilizar `ProjectDoc` o crear `review_attachments`.

### Entidades y endpoints sugeridos

- `POST /security-reviews`
- `POST /review-findings`
- `POST /review-recommendations`
- `POST /review-attachments`
- `PATCH /security-reviews/{id}` para cierre.

### UI

- Admin: agenda de revisiones + detalle con tabs (Hallazgos, Evidencias, Recomendaciones, Tickets).
- Portal cliente: lectura de revisiones autorizadas.

### Auditoria

- Log en `audit_logs`: creacion/cierre de revision, alta de hallazgo, recomendacion y evidencia.

## Flujo 5. Gestion de ticket

### Descripcion

Se crea o importa un ticket, se asigna a cliente/consola/activo, se define prioridad y responsable, se atiende, se documenta solucion y se cierra.

### Integracion con NinjaSec

- `ServiceRequest` existe pero no cubre ciclo completo.
- Recomendacion: crear `support_tickets` con estados, prioridad, responsable y timestamps.
- Asociacion flexible mediante `ticket_links` (cliente/consola/activo/revision).

### Entidades y endpoints sugeridos

- `POST /support-tickets`
- `PATCH /support-tickets/{id}` (status, responsable, solucion)
- `POST /ticket-links` (link a cliente/consola/activo/revision)
- `GET /support-tickets?client_id=`

### UI

- Admin: bandeja de tickets con filtros por prioridad/estado/cliente.
- Portal cliente: tickets abiertos/cerrados.

### Auditoria

- Log en `audit_logs`: cambios de estado, reasignaciones, cierre.

## Flujo 6. Reporte y exportacion

### Descripcion

El supervisor filtra por cliente o periodo, el sistema consolida revisiones, hallazgos y tickets, genera informe y exporta Excel con formato corporativo.

### Integracion con NinjaSec

- Usar `Report` + `ReportRun` para ejecuciones.
- Export Excel como `ReportRun.output_file` o `ReportExport` adicional.
- Consolidacion via consultas de `security_reviews`, `review_findings`, `support_tickets`.

### Entidades y endpoints sugeridos

- `POST /reports` (definicion)
- `POST /reports/{id}/run` (existente)
- `GET /reports/runs` (existente)
- `POST /reports/{id}/export-xlsx` (nuevo)

### UI

- Admin: vista de reportes con filtros por cliente/periodo y boton Export XLSX.
- Portal cliente: acceso a reportes autorizados.

### Auditoria

- Log en `audit_logs`: generacion de reporte y exportacion.

## Notas de integracion tecnica

- Todas las nuevas entidades deben incluir `organization_id` cuando aplique.
- Filtros por fecha deben soportar anios >= 2026.
- Cualquier accion critica debe registrar `audit_logs`.
