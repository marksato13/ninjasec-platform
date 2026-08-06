# Implementación — Módulo Tareas del Portal

> Basado en: `PLANIFICACION/22-MODULO-TAREAS-PORTAL.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Vista

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Página `/portal/tasks` "Mis proyectos" | ✅ | `(portal)/portal/tasks/page.tsx` |
| 2 | Consumo de `GET /projects` con filtrado backend por membresía | ✅ | `tasks/page.tsx` → `getProjects()` |
| 3 | Query key `["portal-my-projects"]` | ✅ | `tasks/page.tsx` |
| 4 | 4 KPIs: activos, planificación, completados, total | ✅ | `tasks/page.tsx` → `metrics-grid` |
| 5 | Filtro por estado (client-side, sin refetch) | ✅ | `tasks/page.tsx` → `statusFilter` |
| 6 | Etiquetas de estado en español | ✅ | `STATUS_LABEL` |
| 7 | Badges por estado | ✅ | `getStatusBadgeClass` de `lib/role-utils.ts` |
| 8 | Fechas en formato `es-PE` | ✅ | `formatDate()` |
| 9 | Contador de asignaciones con plural correcto | ✅ | `tasks/page.tsx` |

### Seguridad

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | Sin membresía en `project_members` no hay visibilidad | ✅ | filtro en `modules/projects` |
| 11 | Vista de solo lectura (sin mutaciones) | ✅ | `tasks/page.tsx` no importa mutations |
| 12 | Estado vacío manejado sin error | ✅ | `data = []` por defecto |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| 22-P-01 | **Tareas reales, no solo proyectos** | 🔴 Alta | La vista se llama "Tareas" y muestra proyectos. Requiere tabla `project_tasks` |
| 22-P-02 | Detalle del proyecto desde el portal | 🟡 Media | Las cards no enlazan a ningún detalle |
| 22-P-03 | Vista Kanban | 🟢 Baja | El backoffice ya la tiene en `/dashboard/projects` |
| 22-P-04 | Indicador de progreso | 🟡 Media | Sin tareas no hay porcentaje de avance calculable — depende de `22-P-01` |
| 22-P-05 | Import inconsistente | 🟢 Baja | `getProjectMembers` se importa y no se usa en `tasks/page.tsx` |

---

## Propuesta para `22-P-01`

Si se decide implementar tareas reales, el diseño mínimo viable:

```
project_tasks
├── id
├── project_id          → FK projects
├── title               → título de la tarea
├── description
├── assignee_user_id    → FK users (nullable)
├── status              → todo | in_progress | review | done
├── priority            → low | medium | high | critical
├── due_date
├── finding_id          → FK review_findings (nullable) ← tarea nacida de un hallazgo
├── ticket_id           → FK support_tickets (nullable) ← tarea nacida de un ticket
├── created_by / created_at / updated_at
```

El valor diferencial está en `finding_id` y `ticket_id`: cierra el círculo **hallazgo de seguridad → tarea de remediación → evidencia de cierre**, que es exactamente lo que pide una auditoría ISO 27001 y lo que consumirá el módulo [[26-MODULO-AUDITORIAS-COBIT]].

**Alcance estimado:** 1 tabla + 1 migración + módulo backend (router/schemas/service) + vista Kanban en portal y backoffice ≈ 1-2 sesiones.

⚠️ Decisión previa: implementarlo como ampliación del módulo **12 — Proyectos**, no como módulo numerado aparte.
