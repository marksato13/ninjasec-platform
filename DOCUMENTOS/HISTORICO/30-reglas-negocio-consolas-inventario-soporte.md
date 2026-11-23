# Reglas de negocio - Consolas, inventario y soporte

## Objetivo

Definir las reglas de negocio obligatorias para el sistema de gestion de clientes, consolas, inventario, revisiones, hallazgos, tickets y reportes, integradas al entorno NinjaSec.

## Reglas generales (operacion)

1) **Cliente previo**
   - Todo cliente debe estar registrado antes de registrar inventario, consolas o tickets.
   - Impacto: `Client` es requisito para `Integration`, `Device`, `SupportTicket`.

2) **Consola obligatoria por cliente**
   - Toda consola debe pertenecer obligatoriamente a un cliente.
   - Impacto: `Integration.client_id` obligatorio al crear consola.

3) **Activo asociado a cliente**
   - Todo activo debe estar asociado a una empresa cliente.
   - Impacto: `Device.integration_id -> Integration.client_id` no puede ser null.

4) **Revision con responsable**
   - Una revision no puede cerrarse sin responsable asignado.
   - Impacto: `security_reviews.reviewer_user_id` obligatorio al cerrar.

5) **Hallazgo con severidad**
   - Todo hallazgo debe tener severidad definida.
   - Impacto: `review_findings.severity` no puede ser null.

6) **Hallazgo critico/alto genera accion**
   - Un hallazgo critico o alto debe generar accion correctiva o ticket obligatorio.
   - Impacto: validar `review_findings.severity in (critical, high)` => `support_ticket` o `recommendation`.

7) **Ticket con estado/prioridad/fecha**
   - Todo ticket debe tener estado, prioridad y fecha de creacion.
   - Impacto: `support_tickets.status`, `priority`, `created_at` obligatorios.

8) **Cierre de ticket con solucion**
   - No se puede cerrar un ticket sin registrar solucion o comentario final.
   - Impacto: `support_tickets.resolution` obligatorio cuando status = closed.

9) **Export tickets desde 2026**
   - Las exportaciones deben permitir filtrar desde 2026 en adelante.
   - Impacto: endpoints de export deben aceptar `date_from >= 2026-01-01`.

10) **Inventario historico**
    - El inventario historico no debe eliminarse fisicamente; solo cambiar de estado.
    - Impacto: soft delete en `Device` con `status = retired` o `inactive`.

11) **Revision con historial y evidencias**
    - Las revisiones deben conservar historial y evidencias.
    - Impacto: `review_attachments` o `ProjectDoc` vinculados a `security_reviews`.

12) **Scope de cliente**
    - Usuarios cliente solo pueden ver informacion de su propia empresa.
    - Impacto: filtros por `client_id` en portal y validacion RBAC.

13) **Ticket refleja servicio/consola**
    - Tickets asociados a cliente deben reflejar servicio o consola relacionada.
    - Impacto: `support_tickets` requiere `integration_id` o `service_id`.

14) **Auditoria obligatoria**
    - Toda modificacion critica debe quedar registrada en bitacora.
    - Impacto: `audit_logs` en cambios de estado, cierre, asignacion y export.

15) **Relacion ticket-revision**
    - Un ticket puede estar asociado a una revision, pero una revision puede originar varios tickets.
    - Impacto: relacion 1..N `security_reviews` -> `support_tickets`.

16) **Reportes por cliente/fecha/consola/estado**
    - Los reportes deben emitirse por cliente, por fecha, por consola y por estado.
    - Impacto: filtros en `Report` y `ReportRun`.

17) **Formato estandar en exportaciones**
    - Todo registro exportado debe respetar formato estandar de la organizacion.
    - Impacto: plantilla corporativa para XLSX/PDF.

18) **Licencia vencida = riesgo**
    - Si una licencia esta vencida, la consola debe mostrar estado de riesgo.
    - Impacto: `Integration.license_expires_at < today` => `status = risk`.

19) **Activo sin revision**
    - Si un activo no ha sido revisado en un periodo definido, debe aparecer como pendiente.
    - Impacto: job que marca `Device.status = pending_review`.

20) **Indicadores con data validada**
    - Los indicadores del dashboard deben actualizarse con informacion validada.
    - Impacto: consolidacion solo con revisiones cerradas y tickets con estado final.

## Integracion con NinjaSec (modulos)

- Clientes -> `Client`
- Consolas -> `Integration`
- Inventario -> `Device`
- Revisiones -> `security_reviews` (nuevo)
- Hallazgos -> `review_findings` (nuevo)
- Tickets -> `support_tickets` (nuevo) o `ServiceRequest` extendido
- Reportes -> `Report` + `ReportRun`
- Auditoria -> `AuditLog`

## Validaciones recomendadas (backend)

- Validar relaciones obligatorias en create/update.
- Reglas de cierre en endpoints `PATCH`.
- Control de acceso por rol y `client_id`.
- Registro en `audit_logs` en acciones criticas.
