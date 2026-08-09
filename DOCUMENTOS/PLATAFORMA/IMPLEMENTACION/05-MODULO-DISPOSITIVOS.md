# Implementación — Módulo Dispositivos

> Basado en: `DOCUMENTOS/PLATAFORMA/05-MODULO-DISPOSITIVOS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Filtros y vista

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Filtro por tipo de dispositivo como **pills clickables** | ✅ | `devices/page.tsx` → pills con conteo por tipo |
| 2 | Filtro por cliente | ✅ | `devices/page.tsx` → dropdown |
| 3 | Filtro por integración / consola | ✅ | `devices/page.tsx` → dropdown filtrado por cliente |
| 4 | **Vista de cards agrupadas por tipo** | ✅ | `devices/page.tsx` → `grouped` por `DEVICE_TYPES` |
| 5 | Cards: nombre + IP | ✅ | `devices/page.tsx` |
| 6 | Cards: estado con badge y color semáforo | ✅ | `devices/page.tsx` → `borderLeft` + badge |
| 7 | Cards: cliente e integración | ✅ | `devices/page.tsx` → lookup por `integration_id` |
| 8 | Cards: modelo / fabricante | ✅ | `devices/page.tsx` → `vendor · model` |
| 9 | Cards: última actualización (`last_seen_at`) | ✅ | `devices/page.tsx` → `formatLastSeen()` |
| 10 | **Banner de alerta** si hay `pending_review` | ✅ | `devices/page.tsx` → banner naranja con conteo |
| 11 | Exportar XLSX | ✅ | `devices/page.tsx` → `exportDevicesXlsx()` |

### Acciones por rol

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 12 | Ver inventario: todos los roles (incluye collaborator) | ✅ | `sidebar.tsx` + `dashboard-guard.tsx` |
| 13 | Agregar dispositivo: solo admin / super_admin | ✅ | `devices/page.tsx` → `isAdmin` |
| 14 | Editar dispositivo: admin, super_admin **y collaborator** | ✅ | `devices/page.tsx` → `isStaff` |
| 15 | Cambiar estado: incluido en el modal de edición | ✅ | `devices/page.tsx` → select `STATUS_OPTIONS` |
| 16 | Retirar dispositivo (soft-delete): **solo super_admin** | ✅ | `devices/page.tsx` → `isSuperAdmin` |

### Tipos de dispositivo

| # | Tipo | Reconocido |
|---|------|-----------|
| 17 | firewall, switch, server, endpoint, router, ap, camera, other | ✅ | `DEVICE_TYPES` constant |

### Estados de dispositivo

| # | Estado | Color en UI |
|---|--------|------------|
| 18 | active → verde | ✅ |
| 19 | maintenance → amarillo | ✅ |
| 20 | pending_review → naranja | ✅ |
| 21 | offline → rojo | ✅ |
| 22 | decommissioned → gris | ✅ |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/lib/api/devices.ts` | Agregado `last_seen_at?: string \| null` a `DeviceItem` |
| `frontend/src/lib/api/clients.ts` | Nueva función `getAllClientSites()` → `GET /client-sites` (sin filtro), usada para lookup de nombres de sede en la página de devices |
| `frontend/src/app/(admin)/dashboard/devices/page.tsx` | Reescrito: cards agrupadas por tipo, pills de filtro, banner pending_review, `isStaff` para edit, `isSuperAdmin` para retire, `last_seen_at` en cards, cliente por nombre. Carga sites con `useQuery(["client-sites","all"])` y muestra "Sede" en card-meta cuando `device.site_id` está set |
| `frontend/src/app/(portal)/portal/inventory/page.tsx` | Removida columna IP y `asset_tag` del listado — vista cliente ahora no expone información sensible (IP, etiqueta de activo). Conserva hostname/tipo/vendor/modelo/estado |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/devices.ts` | `getDevices()`, `createDevice()`, `updateDevice()`, `retireDevice()`, `exportDevicesXlsx()` |
| `backend/app/modules/devices/services/device_service.py` | Lógica de negocio: org boundary, CLIENT role filter, audit |
| `backend/app/modules/devices/routers/router.py` | `PATCH /devices/{id}` (staff), `DELETE /devices/{id}` → retire (solo super_admin en backend) |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~05-P-01~~ | ~~Portal cliente — vista simplificada sin IPs~~ | ✅ **Implementado**: `/portal/inventory` ya no muestra columna IP ni `asset_tag` — vista cliente solo expone hostname / tipo / vendor / modelo / estado. La grilla pasó de 6 columnas a 5 |
| ~~05-P-02~~ | ~~Filtro por estado en el listado~~ | ✅ **Implementado**: `devices/page.tsx` → `statusFilter` state + `<select>` con `STATUS_OPTIONS`; filtra `devices` combinado con `typeFilter`. |
| ~~05-P-03~~ | ~~Sede (`site_id`) en las cards~~ | ✅ **Implementado**: nueva API `getAllClientSites()` que llama `GET /client-sites` sin filtro. La página de devices hace un `useQuery(["client-sites","all"])` y resuelve `site_id → name` con un map. La fila "Sede" en `card-meta` aparece solo si `device.site_id` está set |
| ~~05-P-04~~ | ~~`last_seen_at` no en `DeviceRead` schema~~ | ✅ **Corregido**: `backend/.../devices/schemas/device.py` → `last_seen_at: datetime \| None = None` añadido a `DeviceRead`. |
| ~~05-P-05~~ | ~~Filtro real backend por `site_id` en portal cliente~~ | ✅ **Resuelto 2026-08-09**: selector de sede en `/portal/inventory` (oculto si el cliente tiene ≤1 sede), pasa `site_id` a `getDevices()`. `GET /client-sites` ahora acepta rol `client` y se auto-limita a las sedes de su propia empresa vía `ClientProfile` (antes ese endpoint no admitía el rol client en absoluto). Verificado en `tests/test_portal_site_filter.py`: un cliente no ve sedes ni dispositivos de otro cliente al filtrar. |
