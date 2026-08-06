# Implementación — Módulo Proyectos

> Basado en: `DOCUMENTOS/PLATAFORMA/12-MODULO-PROYECTOS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Vista Cards

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Cards con nombre y cliente asociado | ✅ | `projects/page.tsx` |
| 2 | Badge de estado | ✅ | `projects/page.tsx` → `getStatusBadgeClass()` |
| 3 | Borde izquierdo con color de estado | ✅ | `projects/page.tsx` → `STATUS_COLOR` map (corregido) |
| 4 | Fechas clave (inicio / fin) en las cards | ✅ | `projects/page.tsx` → `item.start_date` / `item.end_date` (agregado) |
| 5 | Tags: tipo, área, servicio | ✅ | `projects/page.tsx` → `card-tags` |
| 6 | Barra de progreso por estado | ✅ | `projects/page.tsx` → `statusProgress()` |

### Filtros

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 7 | Filtro por estado con 5 opciones correctas | ✅ | `projects/page.tsx` → planning / active / on_hold / completed / cancelled (corregido) |
| 8 | Filtro por tipo de proyecto | ✅ | `projects/page.tsx` → dinámico desde `projectTypes` |
| 9 | Filtro por cliente | ✅ | `projects/page.tsx` |
| 10 | Filtro por área | ✅ | `projects/page.tsx` |

### Acciones por rol

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 11 | Ver todos los proyectos: admin/super_admin | ✅ | `projects/page.tsx` |
| 12 | Crear proyecto: admin/super_admin | ✅ | `projects/page.tsx` → `{isAdmin && <button>}` + `<ProjectForm />` |
| 13 | Eliminar proyecto: **solo super_admin** | ✅ | `projects/page.tsx` → `{isSuperAdmin && <button>}` (corregido) |
| 14 | Ver detalle del proyecto | ✅ | Link a `/dashboard/projects/${id}` |

### Estados de proyecto (mapa de colores corregido)

| # | Estado | Color UI |
|---|--------|---------|
| 15 | `planning` → Planificación | 🔵 `#3B82F6` |
| 16 | `active` → Activo | 🟢 `var(--success)` |
| 17 | `on_hold` → En espera | 🟡 `var(--warning)` |
| 18 | `completed` → Completado | ⚫ `var(--muted)` |
| 19 | `cancelled` → Cancelado | 🔴 `var(--danger)` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/db/models/project.py` | Nueva columna `budget_label: String(80) \| None` |
| `backend/app/modules/projects/schemas/project.py` | `ProjectRead/Create/Update` con `budget_label` |
| `backend/app/modules/projects/routers/extras.py` | `GET /project-members` ahora acepta `project_id` opcional; sin filtro devuelve todos los miembros de la org actual (join con `Project` para validar org boundary) |
| `frontend/src/lib/api/projects.ts` | `ProjectItem` con `budget_label`; payloads `createProject`/`updateProject` aceptan `budget_label`. Nueva función `getAllProjectMembers()` |
| `frontend/src/app/(admin)/dashboard/projects/page.tsx` | `isSuperAdmin` constante; `QK.projects()` en queryKey y setQueryData; delete guard `isSuperAdmin`; `STATUS_COLOR` map; `statusProgress` con `on_hold`; filtros con 5 estados correctos; borderLeft + fechas en cards. **Nuevo:** toggle `Lista` ↔ `Kanban` (5 columnas por estado). **Nuevo:** carga `getAllProjectMembers()` y muestra avatares overlapping de hasta 4 miembros por card + conteo. **Nuevo:** chip `💰 budget_label` junto a fechas. **Nuevo:** select inline para cambiar estado por card (visible para `isAdmin`) que llama `updateProject` y notifica |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/projects.ts` | `ProjectItem` con `start_date`, `end_date`; `getProjects()`, `createProject()`, `updateProject()`, `deleteProject()` |
| `frontend/src/components/forms/project-form.tsx` | Formulario de creación de proyecto |
| `frontend/src/app/(admin)/dashboard/projects/[id]/page.tsx` | Página de detalle del proyecto |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~12-P-01~~ | ~~Collaborator ve todos los proyectos~~ | ✅ **Implementado** en sesión anterior |
| ~~12-P-02~~ | ~~Actualizar estado inline desde el listado~~ | ✅ **Implementado**: select de estado en cada card (visible para `isAdmin`) que llama `updateProject({status})` y muestra toast. Disponible en lista y kanban |
| ~~12-P-03~~ | ~~Presupuesto en las cards~~ | ✅ **Implementado**: columna DB `budget_label`, schemas, chip 💰 en las cards. 6 proyectos seedeados con presupuestos demo |
| ~~12-P-04~~ | ~~Vista agrupada por estado (Kanban)~~ | ✅ **Implementado**: toggle Lista/Kanban en el header del panel. Vista Kanban con 5 columnas (planning/active/on_hold/completed/cancelled) cada una con header coloreado, contador y fondo translúcido del color del estado. Las cards de proyecto se renderizan iguales en ambos modos |
| ~~12-P-05~~ | ~~Equipo asignado visible en cards~~ | ✅ **Implementado**: `getAllProjectMembers()` (backend ahora acepta query sin filtro), map agrupado por `project_id`. Cards muestran hasta 4 avatares circulares overlapping (color generado por `user_id * 47 % 360`) + iniciales + total de miembros |
| ~~12-P-06~~ | ~~Migración Alembic para `budget_label`~~ | ✅ **Resuelto** (verificado 2026-08-06): `20260522_01_pending_schema_updates.py:43-44` |
