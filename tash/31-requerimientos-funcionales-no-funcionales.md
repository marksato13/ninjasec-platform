# Requerimientos funcionales y no funcionales

## Objetivo

Consolidar los requerimientos funcionales (RF) y no funcionales (RNF) para la iteracion de gestion de clientes, consolas, inventario, revisiones y tickets, alineados a NinjaSec.

## Requerimientos funcionales

### RF-01 Gestion de clientes

- Registrar, editar, consultar y desactivar empresas cliente.
- Modulo actual: `Client`.

### RF-02 Gestion de sedes

- Registrar sedes asociadas a cada cliente.
- Requiere modulo nuevo: `client_sites`.

### RF-03 Gestion de contactos

- Registrar responsables internos y contactos del cliente.
- Requiere modulo nuevo: `client_contacts`.

### RF-04 Gestion de inventario

- Registrar activos tecnologicos por cliente, sede, tipo y estado.
- Modulo actual: `Device` (extender con `site_id`).

### RF-05 Gestion de consolas

- Registrar y administrar consolas de seguridad por cliente.
- Modulo actual: `Integration`.

### RF-06 Asociacion inventario-consola

- Asociar activos a una o varias consolas.
- Estado actual: 1 consola por activo (`Device.integration_id`).
- Requiere extension: tabla puente `device_integrations` si se necesita N..N.

### RF-07 Registro de revisiones

- Crear revisiones manuales o programadas sobre una consola.
- Requiere modulo nuevo: `security_reviews`.

### RF-08 Checklist de revision

- Registrar criterios de revision y su resultado.
- Requiere modulo nuevo: `review_checklist_items`.

### RF-09 Registro de hallazgos

- Documentar hallazgos, observaciones y evidencias.
- Requiere modulo nuevo: `review_findings` + `review_attachments`.

### RF-10 Gestion de severidad

- Clasificar hallazgos por severidad.
- Campo requerido en `review_findings.severity`.

### RF-11 Generacion de tickets

- Crear tickets manualmente o desde un hallazgo.
- Requiere modulo nuevo: `support_tickets` (o extender `ServiceRequest`).

### RF-12 Importacion de tickets

- Importar tickets desde archivo Excel.
- Requiere endpoint de import y parser XLSX.

### RF-13 Seguimiento de tickets

- Visualizar ciclo de vida del ticket.
- Requiere `ticket_events` o `support_ticket_history`.

### RF-14 Consolidacion desde 2026

- Consultar tickets y reportes desde 01/01/2026 en adelante.
- Filtros por fecha obligatorios en reportes y export.

### RF-15 Exportacion de tickets

- Exportar tickets por cliente, estado, fecha, tipo y prioridad.
- Requiere endpoint `export-xlsx` con plantilla corporativa.

### RF-16 Exportacion de inventario

- Exportar inventario por cliente y sede.
- Requiere export XLSX con filtros.

### RF-17 Exportacion de revisiones

- Exportar revisiones y hallazgos en Excel.
- Requiere export XLSX desde `security_reviews`.

### RF-18 Dashboard

- Mostrar indicadores clave de gestion.
- Requiere agregaciones con datos validados.

### RF-19 Alertas internas

- Notificar tickets vencidos, licencias vencidas y hallazgos criticos abiertos.
- Requiere scheduler o job periodico + notificaciones.

### RF-20 Control de acceso

- Restringir funcionalidades segun rol.
- Modulo actual: RBAC en auth + portal/admin.

## Requerimientos no funcionales

### RNF-01 Seguridad

- Autenticacion segura y control de sesiones.
- Modulo actual: auth + JWT.

### RNF-02 Disponibilidad

- Disponibilidad operativa en horario laboral y ventanas definidas.
- Requiere monitoreo y health checks.

### RNF-03 Trazabilidad

- Todo cambio relevante debe quedar registrado con usuario, fecha y accion.
- Modulo actual: `AuditLog`.

### RNF-04 Usabilidad

- Interfaz clara con filtros, buscadores y navegacion sencilla.
- UI admin/portal debe mantener cards + tabs.

### RNF-05 Escalabilidad

- Soportar crecimiento en clientes, tickets y revisiones.
- DB indexes por cliente/fecha/estado.

### RNF-06 Rendimiento

- Consultas comunes deben responder en tiempos aceptables con historicos.
- Usar paginacion y filtros por fecha.

### RNF-07 Integridad

- No permitir inconsistencias entre clientes, consolas, activos y tickets.
- Validaciones de FK y reglas de negocio.

### RNF-08 Exportacion

- Archivos Excel deben descargarse correctamente y respetar diseno corporativo.
- Plantilla estandar en backend.

### RNF-09 Respaldo

- Informacion respaldable periodicamente.
- Procedimiento con snapshots o backups automatizados.

### RNF-10 Auditoria

- Bitacora para acciones criticas.
- `audit_logs` obligatorio en cambios de estado y export.

## Integracion con NinjaSec (resumen)

- Clientes: `Client`
- Consolas: `Integration`
- Inventario: `Device`
- Revisiones: `security_reviews` (nuevo)
- Hallazgos: `review_findings` (nuevo)
- Tickets: `support_tickets` (nuevo) o `ServiceRequest` extendido
- Reportes: `Report` + `ReportRun`
- Auditoria: `AuditLog`
