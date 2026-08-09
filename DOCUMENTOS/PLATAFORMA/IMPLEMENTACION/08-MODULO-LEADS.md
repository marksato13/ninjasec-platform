# Implementación — Módulo Leads / CRM Pipeline

> Basado en: `DOCUMENTOS/PLATAFORMA/08-MODULO-LEADS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Vista Kanban

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | 6 columnas por etapa (NEW → CLOSED_LOST) | ✅ | `leads/page.tsx` → `COLUMNS` array |
| 2 | Conteo de leads por columna | ✅ | `leads/page.tsx` → badge con `colLeads.length` |
| 3 | Fondo de color suave por etapa | ✅ | `leads/page.tsx` → `col.bg` en cada columna |
| 4 | Cards con nombre, email, teléfono, área de interés | ✅ | `leads/page.tsx` |
| 5 | Badge de antigüedad del lead (días en verde/amarillo/rojo) | ✅ | `leads/page.tsx` → `ageBadge()` |
| 6 | Botones de transición entre etapas | ✅ | `leads/page.tsx` → `TRANSITIONS` map |
| 7 | CLOSED_WON y CLOSED_LOST son estados terminales (sin transiciones) | ✅ | `leads/page.tsx` → `TRANSITIONS.CLOSED_WON = []` (corregido) |
| 8 | KPI strip (Total, Conversión %, En propuesta, Calificados) | ✅ | `leads/page.tsx` |

### Acciones

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 9 | Ver pipeline (admin/super_admin) | ✅ | `sidebar.tsx` → grupo commercial, adminOnly |
| 10 | Crear lead: solo admin/super_admin | ✅ | `leads/page.tsx` → `{isAdmin && <button Nuevo lead>}` |
| 11 | Mover entre etapas (admin/super_admin) | ✅ | `leads/page.tsx` → `handleMove()` |
| 12 | Modal de detalle al hacer clic en card | ✅ | `leads/page.tsx` → `openDetail()` + modal |
| 13 | Editar lead (nombre, email, teléfono, mensaje): admin/super_admin | ✅ | `leads/page.tsx` + backend `PUT /leads/{id}` |
| 14 | Eliminar lead: solo super_admin | ✅ | `leads/page.tsx` + backend `DELETE /leads/{id}` |

### Backend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 15 | `GET /leads` — listar todos | ✅ | `leads/routers/router.py` |
| 16 | `POST /leads` — crear (público, desde formulario web) | ✅ | `leads/routers/router.py` |
| 17 | `PATCH /leads/{id}` — cambiar estado | ✅ | `leads/routers/router.py` + `lead_service.py` con audit |
| 18 | `PUT /leads/{id}` — editar datos del lead (admin) | ✅ | `leads/routers/router.py` + `lead_service.py` (nuevo) |
| 19 | `DELETE /leads/{id}` — eliminar (super_admin) | ✅ | `leads/routers/router.py` + `lead_service.py` (nuevo) |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/leads/schemas/lead.py` | Agregado `LeadInfoUpdate` con campos editables (sin status) |
| `backend/app/modules/leads/services/lead_service.py` | Métodos `update_info()` y `delete()` nuevos con audit log |
| `backend/app/modules/leads/routers/router.py` | Endpoints `PUT /leads/{id}` (admin) y `DELETE /leads/{id}` (super_admin) |
| `frontend/src/lib/api/leads.ts` | Agregados `updateLead()` → `PUT` y `deleteLead()` → `DELETE` |
| `frontend/src/app/(admin)/dashboard/leads/page.tsx` | `isAdmin`/`isSuperAdmin`; `QK.leads()` en queryKey; `TRANSITIONS` terminales fijos; `openDetail()` en clic de card; modal de edición/detalle; `handleSaveEdit()` y `handleDelete()`; guard "Nuevo lead". **Nuevo:** select `source` editable en el modal (linkedin/referral/website/event/google_ads/cold_outreach/other). **Nuevo:** botón "Convertir a cliente" cuando lead.status=CLOSED_WON — llama `createClient` con la data del lead + audit. Invalida `QK.clients()` después |
| `frontend/src/components/public/lead-form.tsx` | Refactor: usa `requestPublic` (proxy de Next.js) en vez de URL hardcoded con puerto incorrecto. Agregados inputs `phone` y `interest_area` (antes hardcoded). Mensaje de éxito/error con clases `form-success`/`form-error` |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/leads.ts` | `createLead`, `updateLeadStatus` ya existían |
| `backend/app/modules/leads/schemas/lead.py` | `LeadCreate`, `LeadRead`, `LeadUpdate` sin cambios |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~08-P-01~~ | ~~Conversión lead → cliente~~ | ✅ **Implementado** (manual): botón "Convertir a cliente" en el modal de lead cuando `status === CLOSED_WON`. Crea Cliente con `company_name = lead.company_name \|\| lead.contact_name`, `commercial_status = "active"`, y un `notes` armado con interest_area + contacto + teléfono + source + mensaje original. Invalida `QK.clients()` |
| ~~08-P-02~~ | ~~Drag & drop real en el Kanban~~ | ✅ **Implementado** (verificado 2026-08-09): drag & drop nativo HTML5 en `leads/page.tsx` (`draggable`, `onDragStart`/`onDragEnd`, `handleDropToColumn`) — no hizo falta `@dnd-kit`. Corrige el estado de este pendiente, que había quedado desactualizado |
| ~~08-P-03~~ | ~~Formulario `/contacto` crea lead~~ | ✅ **Implementado**: `lead-form.tsx` refactor — usa `requestPublic` (proxy de Next.js) en vez de fetch directo con URL hardcoded `:8021`. Agregados inputs `phone` y `interest_area`. Confirmado: `/contacto` HTTP 200 |
| ~~08-P-04~~ | ~~Fuente del lead (`source`) en el modal de detalle~~ | ✅ **Implementado**: nuevo `<select>` en el modal con 7 opciones (linkedin/referral/website/event/google_ads/cold_outreach/other). Se carga desde `lead.source` al abrir y se persiste vía `updateLead` |
| 08-P-05 | Sin estado de error visible si falla la carga de leads | `leads/page.tsx:71` destructura `useQuery` sin `error`, a diferencia de otras vistas que sí renderizan `{error && <p className="form-error">...}`. Un fetch fallido se ve igual que "sin leads todavía". Comparte issue con `10-P-07` |
