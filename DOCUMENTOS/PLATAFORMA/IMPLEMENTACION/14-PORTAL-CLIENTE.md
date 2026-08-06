# Implementación — Portal Cliente

> Basado en: `DOCUMENTOS/PLATAFORMA/14-PORTAL-CLIENTE.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Sidebar de navegación

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Inicio (`/portal`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` |
| 2 | Inventario (`/portal/inventory`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` |
| 3 | Documentos (`/portal/documents`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` |
| 4 | Tickets (`/portal/tickets`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` |
| 5 | Servicios (`/portal/services`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` (nuevo) |
| 6 | Perfil (`/portal/profile`) | ✅ | `portal-sidebar.tsx` → `clientNavItems` |

### Dashboard del portal (`/portal`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 7 | Saludo personalizado con nombre y cargo | ✅ | `portal-shell.tsx` |
| 8 | KPI: Tickets abiertos | ✅ | `portal-shell.tsx` → `getSupportTickets({ ticket_status: "open" })` |
| 9 | KPI: Dispositivos activos | ✅ | `portal-shell.tsx` → `getDevices({})` + filtro `status === "active"` |
| 10 | KPI: Documentos disponibles | ✅ | `portal-shell.tsx` → `getProjectDocs()` |
| 11 | KPI: Estado seguridad | ✅ | `portal-shell.tsx` → derivado de tickets abiertos |
| 12 | Accesos rápidos a secciones del portal | ✅ | `portal-shell.tsx` → links a inventory, documents, tickets, services |

### Inventario (`/portal/inventory`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 13 | Lista de dispositivos del cliente | ✅ | `portal/inventory/page.tsx` → `getDevices({})` |
| 14 | Filtro por tipo de dispositivo | ✅ | `portal/inventory/page.tsx` → pills clickables + select |
| 15 | Semáforo de estado (activo/pendiente/retirado) | ✅ | `portal/inventory/page.tsx` → `STATUS_COLOR` map |
| 16 | Banner de alerta si hay dispositivos `pending_review` | ✅ | `portal/inventory/page.tsx` → banner naranja con conteo |
| 17 | KPIs: total, activos, pendientes, retirados | ✅ | `portal/inventory/page.tsx` → `kpis` + metric cards |

### Documentos (`/portal/documents`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 18 | Biblioteca de documentos compartidos | ✅ | `portal/documents/page.tsx` |
| 19 | Filtro por proyecto y tipo de documento | ✅ | `portal/documents/page.tsx` → selects |
| 20 | Badge de estado (Activo / Borrador / Archivado) | ✅ | `portal/documents/page.tsx` → `STATUS_BADGE` map |
| 21 | Preview de PDF dentro del portal | ✅ | `portal/documents/page.tsx` → iframe en modal |
| 22 | Abrir/descargar documento | ✅ | `portal/documents/page.tsx` → link externo + iframe |

### Tickets (`/portal/tickets`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 23 | Ver tickets abiertos y cerrados | ✅ | `portal/tickets/page.tsx` → tabs open/closed |
| 24 | Crear nuevo ticket (título, descripción, prioridad) | ✅ | `portal/tickets/page.tsx` → modal + `createSupportTicket()` |
| 25 | Ver historial de eventos de cada ticket | ✅ | `portal/tickets/page.tsx` → modal detalle con eventos |
| 26 | NO puede cambiar estado ni reasignar | ✅ | `portal/tickets/page.tsx` → sin botones de cambio de estado |
| 27 | Backend: CLIENT puede crear tickets | ✅ | `support_tickets/routers/router.py` → `RoleCode.CLIENT` + auto-resolve `client_id` |

### Servicios (`/portal/services`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 28 | Ver catálogo de servicios disponibles | ✅ | `portal/services/page.tsx` → `getServices()` |
| 29 | Solicitar un servicio con mensaje | ✅ | `portal/services/page.tsx` → modal + `createServiceRequest()` |
| 30 | Ver solicitudes propias | ⚠️ | Pendiente: `GET /services/requests` solo permite admin — ver `14-P-01` |

### Perfil (`/portal/profile`)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 31 | Ver datos personales | ✅ | `portal/profile/page.tsx` |
| 32 | Barra de progreso de completitud del perfil | ✅ | `portal/profile/page.tsx` → `ProfileCompleteness` componente |
| 33 | Editar nombre y cargo | ✅ | `portal/profile/page.tsx` → modal editar + `updateMyProfile()` |
| 34 | Cambiar contraseña | ✅ | `POST /auth/change-password` (verifica `current_password` con `verify_password`, hashea nueva con `hash_password`, audita `user.password_changed`) + modal en `portal/profile/page.tsx` con 3 inputs (actual, nueva ≥8, confirmar) |
| 35 | Registrar skills y certificaciones | ✅ | `portal/profile/page.tsx` → modales de skill y certificación |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/dashboard/portal-sidebar.tsx` | Reemplazado nav de cliente con `clientNavItems` (6 items exactos del spec) + icono `Package` para Servicios |
| `frontend/src/components/dashboard/portal-shell.tsx` | KPIs actualizados a: Tickets abiertos, Dispositivos activos, Documentos disponibles, Estado seguridad; quick access → inventory/documents/tickets/services. **Nuevo:** KPI "Servicios contratados" usa `getClientServices(myClientId)` (real, no catalog count); filtra por `ends_at` futuro |
| `frontend/src/app/(portal)/portal/tickets/page.tsx` | Agregado botón "Nuevo ticket" + modal con form (título, descripción, prioridad) + `createSupportTicket()` |
| `frontend/src/app/(portal)/portal/services/page.tsx` | Creado (nuevo) — catálogo de servicios + modal solicitar servicio |
| `frontend/src/app/(portal)/portal/profile/page.tsx` | Agregado modal editar datos personales + `updateMyProfile()`. **Nuevo:** botón "Cambiar contraseña" + modal con 3 inputs y validación de longitud + match |
| `frontend/src/lib/api/auth-api.ts` | Agregado `updateMyProfile()` → `PATCH /auth/profile`. **Nuevo:** `changeMyPassword({current_password, new_password})` → `POST /auth/change-password` |
| `backend/app/modules/auth/routers/router.py` | Agregado `PATCH /auth/profile`. **Nuevo:** `POST /auth/change-password` con verificación de contraseña actual via `verify_password`, hashea nueva con `hash_password`, audita `user.password_changed`. Schema `PasswordChange` con `min_length=8` en new_password |
| `backend/app/modules/support_tickets/schemas/support_ticket.py` | `client_id: int \| None = None` en `SupportTicketCreate` (permite omitir para clientes) |
| `backend/app/modules/support_tickets/routers/router.py` | `POST /` ahora incluye `RoleCode.CLIENT`; auto-resolve `client_id` desde `ClientProfile` cuando es cliente |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/app/(portal)/portal/inventory/page.tsx` | Inventario ya completo — filtros, KPIs, banner pending_review |
| `frontend/src/app/(portal)/portal/documents/page.tsx` | Documentos ya completo — filtros, preview PDF, badge estado |
| `backend/app/modules/services/routers/router.py` | `GET /services/` (público), `POST /services/requests` (público) |
| `backend/app/modules/support_tickets/services/ticket_service.py` | `list()` ya filtra por `client_id` del perfil cuando rol = CLIENT |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~14-P-01~~ | ~~Ver solicitudes propias de servicios~~ | ✅ **Implementado** en sesión anterior |
| ~~14-P-02~~ | ~~Cambiar contraseña desde el portal~~ | ✅ **Implementado**: nuevo endpoint `POST /auth/change-password` con verificación + audit. UI con modal de 3 inputs y validación. Verificado vía API: con contraseña incorrecta devuelve 400 "Contraseña actual incorrecta"; con la correcta devuelve 200 y permite login con la nueva |
| ~~14-P-03~~ | ~~"Servicios contratados" como KPI real~~ | ✅ **Implementado**: `portal-shell.tsx` ahora hace `getClients()` (que para CLIENT devuelve sólo su empresa) + `getClientServices(id)`, y cuenta los que tienen `ends_at` futuro o `null`. El label del quick link también pasó de "Catálogo de servicios" a "Servicios contratados" |
| ~~14-P-04~~ | ~~Restricción de documentos por cliente~~ | ✅ **Implementado** (auditado): el endpoint `GET /project-docs` ya filtra por `Project.client_id == profile.client_id` cuando `current_user.role == CLIENT`, además exige `Project enabled` y `visibility=CLIENT` |
