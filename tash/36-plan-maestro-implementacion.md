# Plan Maestro de Implementación — NinjaSec

**Estado al 2026-05-08** | 32/36 páginas implementadas (85%)

---

## Resumen ejecutivo del estado actual

| Sección | Total | Implementadas | Placeholders |
|---------|-------|---------------|--------------|
| `(admin)/dashboard/` | 14 | 13 | 1 (Settings) |
| `(portal)/portal/` | 11 | 8 | 3 (Resources, Support, Tasks) |
| **Total** | **25** | **21** | **4** |

**Páginas placeholder a completar:**
- `/dashboard/settings`
- `/portal/support`
- `/portal/resources`
- `/portal/tasks`

**Páginas implementadas con mejoras pendientes:**
- Todos los módulos necesitan role-guards visuales (UI diferente según rol)
- Algunos módulos muestran acciones que no deberían estar disponibles para ciertos roles
- El módulo de reportes no tiene la nueva ruta PDF (`consolidated-pdf`) en la UI

---

## Principios de implementación

### Roles del sistema
```
super_admin  → Acceso total, incluye Auditoría y Configuración global
admin        → Acceso operativo completo sin Auditoría
collaborator → Solo módulos de su trabajo personal y proyectos asignados
client       → Solo portal: empresa, dispositivos, reviews, tickets, reportes
```

### Patrón de acceso por componente
Cada página aplica 3 niveles de control:

```typescript
// 1. Guard de ruta (ya implementado: DashboardGuard / PortalGuard)
// 2. Guard visual: ocultar acciones según rol
const { role } = getStoredUser();
const canEdit   = role === "admin" || role === "super_admin";
const canDelete = role === "super_admin";

// 3. Restricción de datos: la API ya filtra por organization_id
// El frontend NO envía datos de otras organizaciones
```

### Stack de implementación
```
Estado servidor:  TanStack Query v5  (useQuery, useMutation)
Formularios:      React Hook Form + Zod
Confirmaciones:   lib/alerts.ts (confirmDelete, confirmApprove, notifySuccess)
Estilos:          globals.css — clases existentes (.button-danger, .card, .panel, etc.)
Íconos:           lucide-react
MCPs a usar:      context7 (docs), postgres-ninjasec (explorar esquema), playwright (QA)
```

---

## Fases de implementación

```
FASE 1 — Completar placeholders          (4 páginas)
FASE 2 — Role-guards visuales            (todos los módulos existentes)
FASE 3 — Mejoras de UX/features          (módulos con gaps)
FASE 4 — Reportes PDF en UI              (módulo reports)
FASE 5 — Mejoras al portal               (portal completo)
```

---

## FASE 1 — Completar páginas placeholder

### 1.1 `/dashboard/settings` — Configuración del sistema

**Roles:** `super_admin`, `admin`
**Estado actual:** `OverviewPage` estático

**Secciones a implementar:**

#### Pestaña: Organización
```
- Nombre de la organización (solo lectura por ahora)
- Plan activo (enterprise / pro / basic)
- Estado de la organización
API: GET /api/v1/organizations/{id}
```

#### Pestaña: Usuarios del sistema
```
- Listado rápido de usuarios activos (sin el CRUD completo — ese está en /users)
- Botón "Ir a gestión de usuarios" → /dashboard/users
API: GET /api/v1/users/
```

#### Pestaña: Catálogos
```
- Tipos de proyecto (crear, activar/desactivar)
- Áreas (crear, activar/desactivar)
- Tipos de documento (crear, activar/desactivar)
API: /api/v1/project-types, /api/v1/areas, /api/v1/doc-types
```

#### Pestaña: Seguridad
```
- JWT expiry visible (solo lectura — valor de config)
- CORS origins (solo super_admin, solo lectura por seguridad)
- Nota: "Para cambios de seguridad, modificar variables de entorno"
```

**Accesos por rol:**
```
super_admin → todas las pestañas
admin       → solo Catálogos (crear tipos de proyecto, áreas, doc-types)
```

---

### 1.2 `/portal/support` — Soporte del portal

**Roles:** `collaborator`, `client`
**Estado actual:** Información estática de contacto

**Lo que debe hacer:**
```
- Mostrar tickets del usuario autenticado (los propios)
- Formulario de creación de nuevo ticket
- Estado de tickets: abierto / en proceso / resuelto
- Botón para ver el detalle de cada ticket
```

**Diferencia por rol:**
```
client       → solo sus tickets, no puede asignar a técnico
collaborator → sus tickets + puede filtrar por proyecto
```

**API:** `GET /api/v1/support-tickets/` (ya filtra por org), `POST /api/v1/support-tickets/`

---

### 1.3 `/portal/resources` — Recursos y documentación

**Roles:** `collaborator`
**Estado actual:** Placeholder con "Sección en preparación"

**Lo que debe mostrar:**
```
- Documentos de proyectos donde el colaborador es miembro
  (visibility = "internal" o "client" según el caso)
- Filtros: por proyecto, por tipo de documento, por estado
- Vista de detalle con preview del markdown si existe
- Botón de GitHub si el doc tiene github_url
```

**API:** `GET /api/v1/project-docs?visibility=internal`

---

### 1.4 `/portal/tasks` — Tareas del colaborador

**Roles:** `collaborator`
**Estado actual:** Placeholder con "Módulo en preparación"

**Lo que debe mostrar:**
```
- Proyectos donde el colaborador es miembro (ProjectMember)
- Por cada proyecto: su rol en el proyecto, % de asignación
- Estado del proyecto
- Botón para ir al detalle del proyecto en el portal
```

**Nota:** No hay un modelo de Task individual en la DB. Esta sección muestra la asignación del colaborador a proyectos como si fueran "tareas activas".

**API:** `GET /api/v1/projects/` (filtra en backend por pertenencia)

---

## FASE 2 — Role-guards visuales en módulos existentes

### Patrón de implementación estándar

Cada página existente debe aplicar este patrón en los botones de acción:

```typescript
"use client";
import { getStoredUser } from "@/lib/auth";

// Al inicio del componente:
const user = getStoredUser();
const isAdmin = user?.role === "admin" || user?.role === "super_admin";
const isSuperAdmin = user?.role === "super_admin";

// En el JSX:
{isAdmin && (
  <button className="button button-danger button-sm" onClick={handleDelete}>
    Eliminar
  </button>
)}
```

### Módulos y sus restricciones visuales

#### `/dashboard/users`
```
super_admin → puede crear, editar, eliminar cualquier usuario
admin       → puede crear y editar (NO eliminar)
Ocultar: botón "Eliminar" si role !== "super_admin"
```

#### `/dashboard/clients`
```
admin / super_admin → CRUD completo
Ocultar: botón eliminar para admin (solo super_admin)
```

#### `/dashboard/projects`
```
admin / super_admin → CRUD completo + asignar colaboradores
collaborator (portal) → solo ver proyectos asignados
Ocultar: "Nuevo proyecto" si role !== admin/super_admin
```

#### `/dashboard/integrations`
```
admin / super_admin → CRUD + recolectar datos + test conexión
Restricción: solo admin puede crear integraciones
```

#### `/dashboard/devices`
```
admin / super_admin → CRUD + exportar xlsx
collaborator        → solo lectura (en portal/inventory)
Ocultar: botones crear/editar/eliminar si role !== admin
```

#### `/dashboard/security-reviews`
```
admin / super_admin → crear, cerrar, asignar reviewer
collaborator        → solo ver reviews donde es reviewer
Ocultar: "Nueva revisión" si role !== admin
```

#### `/dashboard/support-tickets`
```
admin / super_admin → ver todos los tickets, asignar, cerrar
collaborator        → ver sus tickets asignados
client (portal)     → solo sus tickets
Ocultar: selector de asignación si role === "client"
```

#### `/dashboard/reports`
```
admin / super_admin → generar todos los reportes
client (portal)     → solo sus reportes consolidados
Agregar: botón "Descargar PDF" (usa el nuevo endpoint /consolidated-pdf)
```

#### `/dashboard/collaborators`
```
admin / super_admin → CRUD completo
Restricción: solo admin puede crear perfiles de colaborador
```

#### `/dashboard/applications`
```
admin / super_admin → ver todas, cambiar status, asignar reviewer
collaborator        → solo ver la propia (en portal)
```

#### `/dashboard/leads`
```
admin / super_admin → CRUD completo
Restricción: leads son solo para admins
```

#### `/dashboard/approvals`
```
admin / super_admin → aprobar/rechazar skills y certifications
Restricción: solo admins ven esta sección
```

#### `/dashboard/audit`
```
super_admin → acceso total
admin       → no tiene acceso (sidebar ya lo oculta)
```

---

## FASE 3 — Mejoras de UX y features faltantes

### 3.1 Dashboard principal (`/dashboard`)
**Mejoras:**
```
- KPI cards con colores: verde=ok, rojo=crítico, ámbar=advertencia
- Gráfico de distribución de hallazgos por severidad (tabla visual)
- Acceso rápido a los últimos 5 tickets abiertos
- Alerta prominente si hay licencias vencidas
Componentes afectados: dashboard-shell.tsx
```

### 3.2 Módulo de Proyectos — detalle
**Mejoras en `[projectId]/page.tsx`:**
```
- Sección "Documentos del proyecto" más visual (previews de markdown)
- Progreso del proyecto (% basado en tareas o fechas)
- Historial de cambios de estado
```

### 3.3 Módulo de Clientes — detalle
**Mejoras en `[id]/page.tsx`:**
```
- Tab "Resumen ejecutivo" con KPIs del cliente (tickets, reviews, devices)
- Botón "Generar reporte" directo desde el detalle del cliente
- Timeline de actividad reciente del cliente
```

### 3.4 Módulo de Integraciones — detalle
**Mejoras en `[id]/page.tsx`:**
```
- Estado de salud más visual (semáforo: verde/ámbar/rojo)
- Última sincronización con tiempo relativo (hace 2 horas)
- Historial de snaps recientes
```

### 3.5 Módulo de Tickets
**Features faltantes:**
```
- Filtro por "asignado a mí"
- Vista Kanban simple: Abierto | En proceso | Resuelto
- Creación de ticket directamente desde un hallazgo (ya existe en API)
```

### 3.6 Módulo de Security Reviews — detalle
**Features faltantes:**
```
- Generación de PDF del reporte de revisión (nueva ruta /consolidated-pdf)
- Botón "Crear ticket desde hallazgo" más visible
- Resumen ejecutivo imprimible
```

---

## FASE 4 — Reportes PDF en UI

### Archivo: `/dashboard/reports/page.tsx`
**Agregar:**
```typescript
// Nuevo botón junto al xlsx
<button
  className="button button-danger button-sm"
  onClick={() => exportConsolidatedReportPdf(token, { client_id, date_from, date_to })}
>
  <FileDown size={14} /> PDF
</button>

// Importar la nueva función
import { exportConsolidatedReportPdf } from "@/lib/api";
```

---

## FASE 5 — Mejoras al portal

### 5.1 Portal principal (`/portal`)
**Mejoras:**
```
- Sección "Mis alertas" con los tickets abiertos del cliente
- Acceso rápido a la última revisión de seguridad
- Indicador de licencias vencidas (si tiene integraciones)
```

### 5.2 Portal — Perfil (`/portal/profile`)
**Mejoras:**
```
- Progress bar de completitud del perfil
- Badges visuales para skills aprobadas vs pendientes
- Sección de certificaciones con estado (approved/pending/rejected) más claro
```

### 5.3 Portal — Proyectos (`/portal/projects`)
**Mejoras:**
```
- Vista de tarjetas (card grid) en lugar de lista
- Indicador de mi rol en cada proyecto
- Acceso a documentos del proyecto directamente
```

---

## Orden de prioridad de implementación

```
PRIORIDAD ALTA (impacto inmediato en funcionalidad)
────────────────────────────────────────────────
1.  /portal/support         → clientes y colaboradores necesitan crear tickets
2.  Role-guards en /users   → evitar que admin elimine usuarios
3.  Role-guards en /clients → permisos correctos
4.  Botón PDF en /reports   → el endpoint ya existe, solo falta la UI
5.  /dashboard/settings     → catálogos son necesarios para otros módulos

PRIORIDAD MEDIA (mejora de UX)
────────────────────────────────────────────────
6.  /portal/resources       → colaboradores necesitan acceder a documentos
7.  /portal/tasks           → vista de asignaciones para colaboradores
8.  Role-guards en /tickets → cliente no debe ver selector de asignación
9.  Mejoras al dashboard principal (KPIs con colores)
10. Mejoras al detalle de cliente (tab resumen ejecutivo)

PRIORIDAD BAJA (polish)
────────────────────────────────────────────────
11. Mejoras al detalle de proyectos
12. Mejoras al detalle de integraciones
13. Vista Kanban en tickets
14. Progress bar en perfil del portal
15. Mejoras al portal principal
```

---

## Especificaciones técnicas por implementación

### Patrón de página completa (estándar)

```tsx
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getStoredToken, getStoredUser } from "@/lib/auth";
import { confirmDelete, notifySuccess, notifyError } from "@/lib/alerts";

export default function ModulePage() {
  const token        = getStoredToken() ?? "";
  const user         = getStoredUser();
  const isAdmin      = user?.role === "admin" || user?.role === "super_admin";
  const isSuperAdmin = user?.role === "super_admin";
  const queryClient  = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["module-key"],
    queryFn:  () => getModuleData(token),
    enabled:  !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteItem(token, id),
    onSuccess: () => {
      notifySuccess("Eliminado correctamente");
      queryClient.invalidateQueries({ queryKey: ["module-key"] });
    },
    onError: (err) => notifyError("Error", err instanceof Error ? err.message : "Error desconocido"),
  });

  async function handleDelete(id: number) {
    const confirmed = await confirmDelete();
    if (confirmed) deleteMutation.mutate(id);
  }

  if (isLoading) return <div className="state-panel">Cargando...</div>;
  if (error)     return <div className="state-panel state-error">Error al cargar datos</div>;

  return (
    <div>
      {/* page-header con título + acciones role-aware */}
      <div className="section-heading">
        <div>
          <p className="eyebrow">Sección</p>
          <h2>Título</h2>
        </div>
        {isAdmin && (
          <button className="button button-primary">+ Nuevo</button>
        )}
      </div>

      {/* contenido */}
    </div>
  );
}
```

### Uso de MCPs durante implementación

```
context7          → Antes de escribir código con TanStack Query, React Hook Form, Next.js
                    Ejemplo: "How to use useMutation with optimistic updates in TanStack Query v5"

postgres-ninjasec → Para verificar estructura de tablas antes de implementar
                    Ejemplo: explorar qué columnas tiene support_tickets antes de hacer el form

playwright        → Para verificar flujos después de implementar
                    Ejemplo: login → navegar a /portal/support → crear ticket → verificar

sequential-thinking → Para módulos complejos (settings con pestañas, dashboard KPIs)
                      Activar cuando el módulo requiera >3 componentes o lógica compleja
```

### Uso de Skills

```
karpathy-guidelines → Activar antes de implementar cualquier módulo
                      Evita over-engineering y mantiene cambios quirúrgicos

simplify            → Después de completar un módulo, revisar el código para reducir redundancia

security-review     → Antes de cualquier merge a main
                      Verificar que no hay rutas expuestas sin auth, tokens en logs, etc.
```

---

## Convenciones de código

### Naming
```
Queries:   queryKey = ["resource-name"]            e.g. ["support-tickets"]
           queryKey = ["resource-name", id]         e.g. ["client", 42]
Mutations: mutationFn recibe solo los datos        (no el token — se cierra sobre él)
Handlers:  handleCreate, handleEdit, handleDelete  (verbos en inglés)
Loading:   isLoading → <div className="state-panel">Cargando...</div>
Error:     error     → <div className="state-panel state-error">{message}</div>
```

### Estructura de una página con tabs
```tsx
const [activeTab, setActiveTab] = useState<"tab1" | "tab2">("tab1");

<div className="tab-list">
  <button className={`tab ${activeTab === "tab1" ? "tab-active" : ""}`} onClick={() => setActiveTab("tab1")}>
    Tab 1
  </button>
</div>

{activeTab === "tab1" && <Tab1Content />}
```

### Confirmaciones de acción
```typescript
// Siempre usar las funciones de lib/alerts.ts
const ok = await confirmDelete({ title: "¿Eliminar ticket #42?" });
if (!ok) return;

// Para aprobaciones
const ok = await confirmApprove({ title: "¿Aprobar skill 'FortiGate'?" });
if (!ok) return;
```

---

## Checklist por módulo antes de marcar como completo

```
[ ] Carga datos reales desde API (useQuery)
[ ] Estado de loading visible
[ ] Estado de error visible con mensaje
[ ] Acciones CRUD con confirmación (confirmDelete para eliminar)
[ ] Feedback de éxito/error (notifySuccess / notifyError)
[ ] Role-guards aplicados (isAdmin, isSuperAdmin)
[ ] No muestra botones de acción para roles sin permiso
[ ] Formularios con validación Zod + React Hook Form
[ ] TypeScript sin errores (npx tsc --noEmit)
[ ] Sin console.log en producción
```
