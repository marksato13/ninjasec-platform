# Implementación — Módulo Tickets de Soporte

> Basado en: `DOCUMENTOS/PLATAFORMA/07-MODULO-TICKETS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Bandeja admin `/dashboard/support-tickets`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Tabs por estado (open / in_progress / pending / resolved / closed) | ✅ | `support-tickets/page.tsx` |
| 2 | Badge con conteo por estado | ✅ | `support-tickets/page.tsx` → `tickets.filter(status).length` |
| 3 | Indicador ⚠ con tickets vencidos por estado | ✅ | `support-tickets/page.tsx` → `isOverdue()` |
| 4 | Filtro por cliente | ✅ | `support-tickets/page.tsx` |
| 5 | Filtro por prioridad | ✅ | `support-tickets/page.tsx` |
| 6 | Filtro por rango de fechas | ✅ | `support-tickets/page.tsx` |
| 7 | SLA vencido — badge rojo "Vencido Nh" | ✅ | `support-tickets/page.tsx` → `hoursOpen()` |
| 8 | Crear ticket (admin, collaborator, super_admin) | ✅ | `support-tickets/page.tsx` → botón siempre visible para staff |
| 9 | Asignar técnico al crear: solo admin/super_admin | ✅ | `support-tickets/page.tsx` → `{isAdmin && <select assigned_to>}` |
| 10 | Exportar XLSX: solo admin/super_admin | ✅ | `support-tickets/page.tsx` → `{isAdmin && <button Exportar>}` |
| 11 | Importar XLSX: solo admin/super_admin | ✅ | `support-tickets/page.tsx` → `{isAdmin && <label Importar>}` |

### Detalle del ticket (modal)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 12 | Historial de eventos (tipo, detalle, fecha) | ✅ | `support-tickets/page.tsx` → tabla de eventos |
| 13 | Cambiar estado: staff (admin, collaborator, super_admin) | ✅ | `support-tickets/page.tsx` → select status sin guard |
| 14 | Asignar técnico en detalle: solo admin/super_admin | ✅ | `support-tickets/page.tsx` → `{isAdmin && <select assigned_to>}` |
| 15 | Campo resolución: staff | ✅ | `support-tickets/page.tsx` → textarea siempre visible |
| 16 | Agregar evento manual: staff | ✅ | `support-tickets/page.tsx` → botón siempre visible |
| 17 | Eliminar ticket: solo super_admin | ✅ | `support-tickets/page.tsx` + backend `DELETE /support-tickets/{id}` |

### Backend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 18 | `GET /support-tickets` — client role ve solo sus tickets | ✅ | `ticket_service.py` → filtro por `client_id` del perfil |
| 19 | `POST /support-tickets` — requiere resolución antes de cerrar | ✅ | `ticket_service.py` → validación en `update()` |
| 20 | Auto-evento al cambiar estado | ✅ | `ticket_service.py` → `SupportTicketEvent` status_change |
| 21 | `DELETE /support-tickets/{id}` — solo super_admin | ✅ | `support_tickets/routers/router.py` + `ticket_service.py` |
| 22 | Exportar XLSX: `GET /support-tickets/export-xlsx` | ✅ | Backend + `exportSupportTicketsXlsx()` |
| 23 | Importar XLSX: `POST /support-tickets/import` | ✅ | Backend + `importSupportTickets()` |

### SLA definidos

| # | Prioridad | SLA | Implementado |
|---|-----------|-----|-------------|
| 24 | critical | 4 horas | ✅ `SLA_HOURS.critical = 4` |
| 25 | high | 8 horas | ✅ `SLA_HOURS.high = 8` |
| 26 | medium | 24 horas | ✅ `SLA_HOURS.medium = 24` |
| 27 | low | 72 horas | ✅ `SLA_HOURS.low = 72` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/support_tickets/services/ticket_service.py` | Método `delete()` nuevo con audit log |
| `backend/app/modules/support_tickets/routers/router.py` | Endpoint `DELETE /support-tickets/{id}` — solo super_admin |
| `frontend/src/lib/api/tickets.ts` | Agregado `deleteSupportTicket()` → `DELETE /support-tickets/{id}`. Nuevo tipo `SupportTicketStats` + función `getSupportTicketStats(filters?)` → `GET /support-tickets/stats` |
| `frontend/src/app/(admin)/dashboard/support-tickets/page.tsx` | `isSuperAdmin` nuevo; Export/Import XLSX guardados con `{isAdmin &&}`; `assigned_to` en detalle guardado con `{isAdmin &&}`; botón Eliminar con `{isSuperAdmin &&}`. **Nuevo:** KPI strip arriba del filtros panel con 4 cards (Total, Abiertos, Cerrados, Tiempo medio) consumiendo `getSupportTicketStats`. **Nuevo:** botón "Desde hallazgo" + modal que permite seleccionar revisión → hallazgo → prioridad → `createTicketFromFinding` |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/tickets.ts` | `createSupportTicket`, `updateSupportTicket`, `createSupportTicketEvent`, `exportSupportTicketsXlsx`, `importSupportTickets` |
| `backend/app/modules/support_tickets/services/ticket_service.py` | Lógica completa: close validation, auto-evento, from-finding, stats |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~07-P-01~~ | ~~Portal cliente no podía crear tickets~~ | ✅ **Implementado** en sesión anterior |
| ~~07-P-02~~ | ~~Estadísticas de tickets (`GET /support-tickets/stats`)~~ | ✅ **Implementado**: nueva API `getSupportTicketStats` + 4 KPI cards arriba del listado (Total / Abiertos / Cerrados / Tiempo medio). Reactivo a los filtros `client_id` y `date_from`. Datos del backend `TicketStats` (total, by_status, by_priority, open/closed counts, avg_resolution_hours) |
| ~~07-P-03~~ | ~~Crear ticket `from-finding` desde el listado~~ | ✅ **Implementado**: botón "Desde hallazgo" en el panel-actions abre modal que carga `getSecurityReviews({})` (solo reviews con `findings_count > 0`); al elegir revisión carga `getSecurityReview(id)` para listar sus findings; al elegir finding + prioridad, hace `createTicketFromFinding`. Invalida `QK.tickets` y `["ticket-stats"]` después |
| ~~07-P-04~~ | ~~`category` sin select fijo~~ | ✅ **Implementado** en sesión anterior |
