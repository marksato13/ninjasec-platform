# Requerimientos adaptados a NinjaSec

## Objetivo

Traducir los requerimientos funcionales y no funcionales al sistema NinjaSec actual, indicando modulos existentes y extensiones necesarias.

## Requerimientos funcionales (RF)

### RF-01 Gestion de clientes

- Necesidad: registrar, editar, consultar y desactivar clientes.
- NinjaSec: `Client` existe con `commercial_status`.
- Ajuste sugerido: usar `commercial_status = paused` o agregar `is_active` si se requiere corte total.

### RF-02 Gestion de sedes

- Necesidad: sedes asociadas a cada cliente.
- NinjaSec: no existe modulo de sedes.
- Extension: crear `client_sites` (client_id, name, address, city, status).

### RF-03 Gestion de contactos

- Necesidad: responsables internos y contactos del cliente.
- NinjaSec: `ClientProfile` cubre usuarios cliente internos.
- Extension: crear `client_contacts` para contactos externos (nombre, email, telefono, rol).

### RF-04 Gestion de inventario

- Necesidad: activos por cliente, sede, tipo y estado.
- NinjaSec: `Device` existe y se asocia a `Integration`.
- Extension: agregar `site_id` (sede) y campos tecnicos (asset_tag, serial, owner).

### RF-05 Gestion de consolas

- Necesidad: registrar consolas por cliente.
- NinjaSec: `Integration` ya es la consola.
- Extension: agregar `environment`, `license_type`, `license_expires_at`, `responsible_user_id`.

### RF-06 Asociacion inventario-consola

- Necesidad: asociar activos a una o varias consolas.
- NinjaSec: `Device.integration_id` es 1..1.
- Extension opcional: `device_integrations` si se requiere N..N.

### RF-07 Registro de revisiones

- Necesidad: crear revisiones manuales o programadas sobre consola.
- NinjaSec: modulo nuevo `security_reviews`.

### RF-08 Checklist de revision

- Necesidad: registrar criterios de revision y resultado.
- NinjaSec: requiere `review_checklist_items`.

### RF-09 Registro de hallazgos

- Necesidad: documentar hallazgos, observaciones y evidencias.
- NinjaSec: requiere `review_findings` + `review_attachments`.

### RF-10 Gestion de severidad

- Necesidad: clasificar hallazgos por severidad.
- NinjaSec: enum `severity` en `review_findings`.

### RF-11 Generacion de tickets

- Necesidad: tickets manuales o desde hallazgos.
- NinjaSec: `ServiceRequest` no cubre ciclo completo.
- Extension: crear `support_tickets` y relacionarlo con `review_findings`.

### RF-12 Importacion de tickets

- Necesidad: importar tickets desde Excel.
- NinjaSec: endpoint nuevo `POST /support-tickets/import` + parser XLSX.

### RF-13 Seguimiento de tickets

- Necesidad: ciclo de vida completo.
- NinjaSec: crear `support_ticket_events` o usar `audit_logs` con detalle.

### RF-14 Consolidacion desde 2026

- Necesidad: consultar tickets y reportes desde 01/01/2026.
- NinjaSec: filtros por fecha en tickets y reportes.

### RF-15 Exportacion de tickets

- Necesidad: export por cliente, estado, fecha, tipo y prioridad.
- NinjaSec: endpoint `export-xlsx` en tickets con plantilla corporativa.

### RF-16 Exportacion de inventario

- Necesidad: export inventario por cliente y sede.
- NinjaSec: endpoint `devices/export-xlsx` con filtros.

### RF-17 Exportacion de revisiones

- Necesidad: export revisiones y hallazgos.
- NinjaSec: export desde `security_reviews` + `review_findings`.

### RF-18 Dashboard

- Necesidad: indicadores clave de gestion.
- NinjaSec: agregar metricas en admin (tickets, revisiones, hallazgos, inventario).

### RF-19 Alertas internas

- Necesidad: notificar tickets vencidos, licencias vencidas, hallazgos criticos.
- NinjaSec: job periodico + notificaciones internas.

### RF-20 Control de acceso

- Necesidad: funcionalidades por rol.
- NinjaSec: RBAC existente, reforzar filtros por `client_id` en portal.

## Requerimientos no funcionales (RNF)

### RNF-01 Seguridad

- NinjaSec: JWT + auth. Reforzar expiracion y bloqueo por intentos.

### RNF-02 Disponibilidad

- NinjaSec: healthchecks en backend y docker compose.

### RNF-03 Trazabilidad

- NinjaSec: `AuditLog` obligatorio en acciones criticas.

### RNF-04 Usabilidad

- NinjaSec: admin y portal con cards, filtros y tabs.

### RNF-05 Escalabilidad

- NinjaSec: indices por `client_id`, `status`, `created_at` en tickets/revisiones.

### RNF-06 Rendimiento

- NinjaSec: paginacion en listados + filtros por fecha.

### RNF-07 Integridad

- NinjaSec: validar FK y reglas de negocio al crear/actualizar.

### RNF-08 Exportacion

- NinjaSec: plantilla corporativa para XLSX.

### RNF-09 Respaldo

- NinjaSec: backups de Postgres programados.

### RNF-10 Auditoria

- NinjaSec: bitacora en cambios de estado y exportaciones.

## Integracion resumida

- Clientes: `Client`
- Consolas: `Integration`
- Inventario: `Device`
- Revisiones: `security_reviews` (nuevo)
- Hallazgos: `review_findings` (nuevo)
- Tickets: `support_tickets` (nuevo) o `ServiceRequest` extendido
- Reportes: `Report` + `ReportRun`
- Auditoria: `AuditLog`
