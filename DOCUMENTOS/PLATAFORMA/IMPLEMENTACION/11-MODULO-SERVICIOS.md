# Implementación — Módulo Servicios

> Basado en: `DOCUMENTOS/PLATAFORMA/11-MODULO-SERVICIOS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Catálogo de servicios

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Cards con borde izquierdo verde seguridad | ✅ | `services/page.tsx` → `borderLeft: "3px solid var(--security)"` |
| 2 | Icono de escudo/categoría por servicio | ✅ | `services/page.tsx` → `serviceIcon()` |
| 3 | Nombre y descripción del servicio | ✅ | `services/page.tsx` |
| 4 | Precio referencial | ✅ | Columna `price_label VARCHAR(80)` en `Service` + chip azul en cada card de servicio ("💰 Desde S/ 800/mes") |
| 5 | Botón "Solicitar servicio" | ✅ | `services/page.tsx` |
| 6 | Crear servicio en catálogo (admin/super_admin) | ✅ | `services/page.tsx` → modal + `createService()` |
| 7 | Eliminar del catálogo (solo super_admin) | ✅ | `services/page.tsx` → `isSuperAdmin` + `deleteService()` |

### Gestión de solicitudes (admin)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 8 | Tabla de solicitudes: Solicitante, Servicio, Mensaje, Estado, Fecha | ✅ | `services/page.tsx` |
| 9 | KPIs: nuevas, en revisión | ✅ | `services/page.tsx` → badges en panel head |
| 10 | Filtro por estado | ✅ | `services/page.tsx` → select `filterStatus` |
| 11 | Transicionar estado inline (NEW→REVIEW→CLOSED) | ✅ | `services/page.tsx` → `STATUS_CFG.next` + `handleStatusChange()` |

### Acciones por rol

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 12 | Ver catálogo: todos (admin, super_admin) | ✅ | `services/page.tsx` |
| 13 | Crear servicio: admin / super_admin | ✅ | `services/page.tsx` + backend `POST /services/` |
| 14 | Solicitar servicio: admin / super_admin / cliente | ✅ | Modal de solicitud visible para todos |
| 15 | Ver solicitudes (todas): admin / super_admin | ✅ | `services/page.tsx` → `enabled: isAdmin` |
| 16 | Cambiar estado de solicitud: admin / super_admin | ✅ | `services/page.tsx` → botones dentro del panel de gestión |
| 17 | Eliminar del catálogo: solo super_admin | ✅ | `services/page.tsx` → `isSuperAdmin` + backend corregido |

### Estados de solicitud

| # | Estado | Color | Implementado |
|---|--------|-------|-------------|
| 18 | `NEW` → Nuevo | 🔵 badge-pending | ✅ |
| 19 | `REVIEW` → En revisión | 🟡 badge-draft | ✅ |
| 20 | `CLOSED` → Cerrado | ⚫ badge-archived | ✅ |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/db/models/service.py` | Nueva columna `price_label: String(80) \| None` |
| `backend/app/modules/services/schemas/service.py` | `ServiceRead/Create` con `price_label`, `is_public`, `active` (Create acepta los flags con defaults `True`) |
| `backend/app/modules/services/routers/router.py` | `DELETE /services/{id}` ahora requiere solo `SUPER_ADMIN` (antes permitía `ADMIN`) |
| `frontend/src/lib/api/services.ts` | `ServiceItem` con `price_label`; `createService` payload acepta `price_label`, `is_public`, `active` |
| `frontend/src/app/(admin)/dashboard/services/page.tsx` | `isSuperAdmin`; `QK.services()` y `QK.serviceRequests()` en queryKeys; modal crear servicio; botón eliminar (super_admin); funciones `handleCreateService()` y `handleDeleteService()`. **Nuevo:** input `price_label` + 2 toggles (`active`, `is_public`) en el form de creación. **Nuevo:** chip azul con icono 💰 en cada card de servicio mostrando `price_label` |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/services.ts` | `getServices()`, `getServiceRequests()`, `createServiceRequest()`, `updateServiceRequestStatus()` |
| `backend/app/modules/services/routers/router.py` | `GET /services`, `POST /services`, `DELETE /services/{id}`, `GET /services/requests`, `POST /services/requests`, `PATCH /services/requests/{id}` |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~11-P-01~~ | ~~Precio referencial en las cards~~ | ✅ **Implementado**: columna DB `price_label`, schema, input en form, chip azul en cards. 4 servicios seedeados con precios demo |
| ~~11-P-02~~ | ~~Portal cliente `/portal/services`~~ | ✅ **Implementado** en módulo 14 |
| ~~11-P-03~~ | ~~`is_public` y `active` en el form de creación~~ | ✅ **Implementado**: 2 toggles en el modal de creación con etiquetas dinámicas (`Activo`/`Inactivo`, `Público en /servicios`/`Solo interno`). Defaults a `true/true`. El schema `ServiceCreate` acepta los flags |
| ~~11-P-04~~ | ~~Ver solicitudes propias (cliente)~~ | ✅ **Implementado** en sesión anterior |
| ~~11-P-05~~ | ~~Migración Alembic para `price_label`~~ | ✅ **Resuelto** (verificado 2026-08-06): `20260522_01_pending_schema_updates.py:39-40` |
