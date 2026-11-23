# Postulaciones (Talento) - Plan por fases e instrucciones

## Objetivo

Gestionar postulaciones provenientes de `/colabora` con un flujo claro de revision, asignacion a revisores, comentarios internos, validacion de CV/links y aprobacion final por admin.

## Roles y acceso

### Roles involucrados

- super_admin: control total del flujo, estados, asignaciones y cierre.
- admin: gestiona postulaciones, asigna revisores y decide final.
- collaborator_admin (opcional): puede revisar y recomendar, no decide final.
- collaborator: revisa y comenta postulaciones asignadas.
- visitor: crea postulacion desde publico.

### Permisos

- admin/super_admin: CRUD total, cambio de estado, asignar revisores, aprobar/rechazar.
- collaborator_admin: ver postulaciones asignadas, comentar, calificar, recomendar.
- collaborator: solo ver asignadas, comentar y calificar.

## Estados y flujo

### Estados sugeridos

- new -> screening -> interview -> offer -> hired
- rejected, withdrawn, on_hold

### Reglas

- Solo admin/super_admin puede mover a offer o hired.
- rejected/withdrawn son estados finales.
- Cambios de estado generan auditoria.

## Entidades y campos (Backend)

### job_applications (base existente)

- id
- full_name
- email
- phone
- desired_role
- skills_summary
- cv_url
- portfolio_url
- status (enum)
- source (ej: web, referral)
- created_at

### application_assignments (nuevo)

- id
- application_id
- reviewer_user_id
- assigned_by_user_id
- assigned_at
- role (reviewer / interviewer)

### application_reviews (nuevo)

- id
- application_id
- reviewer_user_id
- score (1-5)
- recommendation (approve / reject / hold)
- notes
- created_at

### application_notes (nuevo)

- id
- application_id
- author_user_id
- note
- visibility (internal)
- created_at

### application_attachments (nuevo)

- id
- application_id
- file_url
- file_type
- uploaded_by
- created_at

### application_events (nuevo)

- id
- application_id
- type (status_change / interview / note / review)
- payload_json
- created_at

## Endpoints (API)

### Publico

- POST /job-applications  (crea postulacion desde /colabora)

### Admin / Collaborator

- GET /job-applications (filtros: status, role, date, reviewer)
- GET /job-applications/{id}
- PATCH /job-applications/{id} (status update)
- POST /job-applications/{id}/assign
- POST /job-applications/{id}/reviews
- POST /job-applications/{id}/notes
- POST /job-applications/{id}/attachments
- GET /job-applications/{id}/timeline

## UI / UX

### Vista lista (admin)

- Cards con: nombre, rol deseado, estado, fecha, badge de prioridad.
- Filtros: status, rol deseado, reviewer, fechas.
- Botones: Ver detalle, Asignar revisor, Cambiar estado.

### Vista detalle (admin)

Tabs:
- Resumen: datos del postulante, links, CV, estado actual.
- Revisiones: reviews internas y score promedio.
- Notas: comentarios internos.
- Entrevistas: calendario o registros.
- Historial: timeline de eventos.

### Vista lista (colaborador)

- "Mis revisiones" con cards.
- Ver postulaciones asignadas.

### Vista detalle (colaborador)

- Resumen del postulante.
- Formulario de review + recomendacion.
- Notas internas visibles para admin.

## Interaccion Admin <-> Colaborador

- Admin asigna revisores a postulaciones.
- Colaborador agrega review y recomendacion.
- Admin ve recomendaciones agregadas y decide estado final.

## Auditoria y seguridad

- Todo cambio de estado y asignacion genera evento en audit_logs.
- Acceso a CV/adjuntos restringido por rol.
- Logs de lectura del CV opcional.

## Criterios de aceptacion

- Admin puede crear, asignar, revisar y cerrar postulaciones.
- Colaborador solo ve lo asignado.
- Historial completo visible en detalle.
- Estados finales bloquean nuevas acciones (excepto notas internas).

---

# Plan por fases con instrucciones

## Fase 1 - Backend base y auditoria

### Objetivo

Crear entidades, reglas y endpoints del flujo.

### Instrucciones

- Crear modelos: application_assignments, application_reviews, application_notes, application_attachments, application_events.
- Enums para status y recommendation.
- Endpoints base segun listado (GET/POST/PATCH).
- Validar reglas de estado (offer/hired solo admin).
- Registrar eventos en audit_logs y application_events.

### Validacion

- Tests o requests manuales con datos seed.
- Confirmar que audit_logs recibe eventos.

## Fase 2 - Admin UI

### Objetivo

Vista lista + detalle con tabs y acciones.

### Instrucciones

- Listado en cards con filtros y badges de estado.
- Vista detalle con tabs y formularios internos.
- Accion "Asignar revisor" con modal.
- Accion "Cambiar estado" con confirmacion.

### Validacion

- Navegacion completa: lista -> detalle -> updates.
- Cambios de estado se reflejan en timeline.

## Fase 3 - Portal colaborador

### Objetivo

Acceso a postulaciones asignadas y reviews.

### Instrucciones

- Listado "Mis revisiones" en cards.
- Vista detalle con review + recomendacion.
- Notas internas visibles para admin.

### Validacion

- Colaborador no ve postulaciones no asignadas.
- Admin ve recomendaciones en detalle.

## Fase 4 - Notificaciones y analitica

### Objetivo

Alertas de asignacion y metricas.

### Instrucciones

- Notificaciones (email o in-app) al asignar.
- Analitica basica: tiempo promedio por estado.

### Validacion

- Notificacion al asignar/rechazar.
- Reporte con tiempos por estado.

---

# Uso de Context7 (obligatorio)

## FastAPI

- Validar RBAC y dependencias con Context7 (FastAPI Security / Depends).
- Documentar patrones usados en endpoints.

## Next.js App Router

- Validar layouts y route groups para admin/portal.
- Uso de modales y rutas anidadas.

## Resultado esperado

- Flujo completo desde /colabora hasta decision final.
- Roles y permisos aplicados en backend y frontend.
- Auditoria y timeline habilitados.
