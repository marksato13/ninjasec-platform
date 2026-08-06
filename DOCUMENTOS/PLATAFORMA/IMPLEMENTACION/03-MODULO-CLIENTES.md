# Implementación — Módulo Clientes

> Basado en: `DOCUMENTOS/PLATAFORMA/03-MODULO-CLIENTES.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Listado `/dashboard/clients`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Mostrar nombre de empresa | ✅ | `clients/page.tsx` |
| 2 | Mostrar sector | ✅ | `clients/page.tsx` |
| 3 | Mostrar estado de relación (badge) | ✅ | `clients/page.tsx` |
| 4 | Botón para ir al perfil detallado | ✅ | `clients/page.tsx` → Link `/dashboard/clients/[id]` |
| 5 | Crear nuevo cliente (admin) | ✅ | `clients/page.tsx` → `ClientForm` + `createClient()` |
| 6 | Editar datos del cliente | ✅ | `clients/page.tsx` → modal edit + `updateClient()` |
| 7 | País y ciudad en listado | ✅ | Columnas `city`/`country` agregadas al modelo + UI muestra con icono MapPin |
| 8 | Número de dispositivos activos en listado | ✅ | Badge con icono `Server` — viene de subquery `devices_count` |
| 9 | Badge de tickets abiertos en listado | ✅ | Badge con icono `Ticket` — viene de subquery `open_tickets_count` |
| 10 | Exportar listado XLSX | ✅ | `GET /clients/export-xlsx` con openpyxl + frontend `exportClientsXlsx()` + botón |

### Perfil `/dashboard/clients/[id]`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 11 | Tab Resumen — KPIs (tickets, devices, services, consoles) | ✅ | `clients/[id]/page.tsx` |
| 12 | Tab Resumen — banner de alertas del cliente | ✅ | `clients/[id]/page.tsx` |
| 13 | Tab Resumen — botón exportar PDF | ✅ | `clients/[id]/page.tsx` → `exportConsolidatedReportPdf()` |
| 14 | Tab Consolas — lista de integraciones pfSense/FortiGate | ✅ | `clients/[id]/page.tsx` |
| 15 | Tab Consolas — estado de salud de cada consola | ✅ | `clients/[id]/page.tsx` → badge `effective_status` |
| 16 | Tab Consolas — próxima expiración de licencia | ✅ | `clients/[id]/page.tsx` → `license_expires_at` + badge vencida |
| 17 | Tab Inventario — activos del cliente | ✅ | `clients/[id]/page.tsx` |
| 18 | Tab Inventario — filtro por tipo de dispositivo | ✅ | `clients/[id]/page.tsx` → `deviceTypeFilter` local |
| 19 | Tab Inventario — estado de cada dispositivo | ✅ | `clients/[id]/page.tsx` → badge `device.status` |
| 20 | Tab Tickets — historial completo (todos los estados) | ✅ | `clients/[id]/page.tsx` → fetch sin filtro de status |
| 21 | Tab Tickets — filtro por estado | ✅ | `clients/[id]/page.tsx` → `ticketStatusFilter` local |
| 22 | Tab Tickets — filtro por prioridad | ✅ | `clients/[id]/page.tsx` → `ticketPriorityFilter` local |
| 23 | Tab Revisiones — lista de auditorías del cliente | ✅ | `clients/[id]/page.tsx` → tab + `getSecurityReviews()` |
| 24 | Tab Revisiones — estado y fechas | ✅ | `clients/[id]/page.tsx` → scheduled_at, executed_at, badge status |
| 25 | Tab Revisiones — link al detalle de la revisión | ✅ | `clients/[id]/page.tsx` → Link `/dashboard/security-reviews/[id]` |
| 26 | Tab Servicios — servicios contratados | ✅ | `clients/[id]/page.tsx` |
| 27 | Tab Revisiones — hallazgos por revisión (counts) | ✅ | Columna "Hallazgos" muestra total + badge crítico cuando aplica |

---

## Archivos modificados en esta sesión

### Backend

| Archivo | Cambio |
|---------|--------|
| `backend/app/db/models/client.py` | Columnas nuevas `city: str(120) \| None`, `country: str(80) \| None` |
| `backend/app/modules/clients/schemas/client.py` | `ClientRead/Create/Update` con `city`, `country`. `ClientRead` con `devices_count`, `open_tickets_count` (default 0) |
| `backend/app/modules/clients/services/client_service.py` | `list()` ahora llama `_enrich_counts()` — dos subqueries con `func.count` para devices vía Integration y tickets con status OPEN. `create()` persiste city/country |
| `backend/app/modules/clients/routers/router.py` | Nuevo endpoint `GET /clients/export-xlsx` — openpyxl con estilo y columnas: ID, Empresa, Sector, Tamaño, Ciudad, País, Estado, Dispositivos, Tickets abiertos, Notas. Solo super_admin/admin |
| `backend/app/modules/security_reviews/schemas/security_review.py` | `SecurityReviewRead` con `findings_count`, `critical_findings_count` (default 0) |
| `backend/app/modules/security_reviews/routers/router.py` | `list_reviews()` enriquece cada review con counts via subquery agrupando por `review_id` (total y filtrado por `severity=CRITICAL`) |

### Frontend

| Archivo | Cambio |
|---------|--------|
| `frontend/src/lib/api/clients.ts` | `DashboardClient` con `city`, `country`, `devices_count`, `open_tickets_count`. `createClient` payload acepta city/country. Nueva función `exportClientsXlsx()` |
| `frontend/src/lib/api/reviews.ts` | `SecurityReviewItem` con `findings_count`, `critical_findings_count` opcionales |
| `frontend/src/lib/validation.ts` | `clientFormSchema` con `city`, `country` opcionales |
| `frontend/src/components/forms/client-form.tsx` | Inputs nuevos en grid 2-col para ciudad y país; se pasan al `createClient` |
| `frontend/src/app/(admin)/dashboard/clients/page.tsx` | Botón "Exportar XLSX" en header; badges con icono `Server` (devices) e icono `Ticket` (tickets abiertos) en `card-badges`; nueva celda "Ubicación" con icono `MapPin` en card-meta; inputs ciudad/país en modal edit |
| `frontend/src/app/(admin)/dashboard/clients/[id]/page.tsx` | Nueva columna "Hallazgos" en tab Revisiones — muestra `✓ Sin hallazgos` cuando 0 o un par de badges (total + críticos) cuando hay |

### Base de datos / seed

- `ALTER TABLE clients ADD COLUMN city VARCHAR(120)` y `country VARCHAR(80)` aplicado vía SQL directo (no Alembic) — `Base.metadata.create_all` no añade columnas a tablas existentes
- Datos de ejemplo cargados para los 9 clientes (Lima/Arequipa/Trujillo/Cusco/Piura — Perú; Bogotá — Colombia)
- 8 findings de ejemplo insertados en 4 revisiones (review 1: 1 crit + 1 high + 1 med, etc.) para que el badge de hallazgos se vea en el demo

---

## Archivos de referencia (sin cambios en esta sesión)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/reviews.ts` | `getSecurityReviews({ client_id })` consume el nuevo `findings_count` |
| `frontend/src/lib/api/integrations.ts` | `IntegrationItem.license_expires_at` + `is_license_expired` ya existían |
| `backend/app/modules/clients/routers/router.py` | `PUT /clients/{id}` y `DELETE /clients/{id}` ya existían con `ClientService` |

---

## Notas de implementación

| # | Nota |
|---|------|
| N-01 | Para `devices_count` se hace JOIN `Integration → Device` y se cuenta agrupando por `Integration.client_id`. Para `open_tickets_count` se filtra `SupportTicket.client_id` con `status == OPEN` |
| N-02 | `_enrich_counts` corre dos subqueries por petición (O(2) calls, no N+1). Se ejecutan solo si la lista de clientes no está vacía |
| N-03 | El endpoint `GET /clients/export-xlsx` usa el mismo helper `downloadFile()` del frontend que se usa para devices/leads/tickets/reviews. Se ubica antes de `/{client_id}` en el router pero al estar el path-segment estático `/export-xlsx` con prefijo distinto, FastAPI lo resuelve correctamente |
| N-04 | `findings_count` y `critical_findings_count` se computan con 2 subqueries agrupadas. La vista detalle (`SecurityReviewDetail`) trae findings inline, por lo que ahí no se duplica el trabajo |
| N-05 | No se creó migración Alembic en esta sesión — los campos `city`/`country` se agregaron con `ALTER TABLE`. Para producción se debe generar una migración `alembic revision --autogenerate -m "add city country to clients"` |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~03-P-01~~ | ~~País y ciudad en el listado de clientes~~ | ✅ **Implementado**: columnas DB + schemas + UI con icono MapPin |
| ~~03-P-02~~ | ~~Dispositivos activos + tickets abiertos como badges en listado~~ | ✅ **Implementado**: `_enrich_counts()` con 2 subqueries, badges visibles en cards |
| ~~03-P-03~~ | ~~Exportar listado XLSX~~ | ✅ **Implementado**: endpoint backend con openpyxl + botón en header |
| ~~03-P-04~~ | ~~Tab Revisiones — hallazgos por revisión~~ | ✅ **Implementado**: `findings_count` y `critical_findings_count` en `SecurityReviewRead`, columna en UI |
| ~~03-P-05~~ | ~~`deleteClient()` sin botón en UI~~ | ✅ **Implementado** en sesión anterior |
| ~~03-P-06~~ | ~~Crear migración Alembic para los campos city/country~~ | ✅ **Resuelto** (verificado 2026-08-06): `app/db/migrations/versions/20260522_01_pending_schema_updates.py:27-30` agrega `clients.city` y `clients.country` con guarda `_has_column()` idempotente |
