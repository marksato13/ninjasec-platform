# Implementación — Módulo Tareas del Portal

> Basado en: `PLANIFICACION/22-MODULO-TAREAS-PORTAL.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Vista

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Página `/portal/tasks` "Mis tareas" | ✅ | `(portal)/portal/tasks/page.tsx` |
| 2 | Consumo de `GET /project-tasks` con filtrado backend por rol | ✅ **Actualizado 2026-08-09** | `tasks/page.tsx` → `getProjectTasks()` (antes llamaba `getProjects()`, ver `22-P-01`) |
| 3 | Query key `["portal-my-tasks"]` | ✅ | `tasks/page.tsx` |
| 4 | 4 KPIs: pendientes, en curso, hechas, total | ✅ **Actualizado 2026-08-09** | `tasks/page.tsx` → `metrics-grid` (antes eran KPIs de estado de proyecto) |
| 5 | Filtro por estado (client-side, sin refetch) | ✅ | `tasks/page.tsx` → `statusFilter` |
| 6 | Etiquetas de estado en español | ✅ | `STATUS_LABEL` |
| 7 | Badges por estado | ✅ | `STATUS_BADGE` en `tasks/page.tsx` |
| 9 | Contador de tareas con plural correcto | ✅ | `tasks/page.tsx` |

### Seguridad

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | Sin asignación/membresía no hay visibilidad | ✅ **Actualizado 2026-08-09** | `modules/projects/routers/tasks.py:list_project_tasks` — collaborator filtra por `assigned_user_id`, client por `Project.client_id` vía `ClientProfile` |
| 11 | Vista de solo lectura (sin mutaciones) | ✅ | `tasks/page.tsx` no importa mutations — crear/editar/borrar sigue siendo `super_admin`/`admin` únicamente |
| 12 | Estado vacío manejado sin error | ✅ | `data = []` por defecto |
| 13 | Aislamiento multi-tenant (`organization_id`) | ✅ | `ProjectTask.organization_id` + filtro explícito en cada query del router |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~22-P-01~~ | ~~**Tareas reales, no solo proyectos**~~ | — | ✅ **Resuelto 2026-08-09**: tabla `project_tasks` (migración `20260809_01`), modelo `ProjectTask`, CRUD en `modules/projects/routers/tasks.py` (`POST`/`GET`/`PUT`/`DELETE /project-tasks`). Alcance deliberadamente mínimo (sin `priority`, `due_date`, `finding_id` ni `ticket_id` de la propuesta original — el issue #14 los excluyó explícitamente: "no implementar dependencias entre tareas, subtareas ni tablero kanban"). Validado con `tests/test_project_tasks.py`: colaborador ve solo sus tareas, aislamiento entre organizaciones, cliente ve tareas de sus proyectos (no de otros clientes), solo admin/super_admin crea/edita/borra |
| 22-P-02 | Detalle del proyecto desde el portal | 🟡 Media | Las cards no enlazan a ningún detalle |
| 22-P-03 | Vista Kanban | 🟢 Baja | El backoffice ya la tiene en `/dashboard/projects` |
| 22-P-04 | Indicador de progreso | 🟡 Media | Ya hay `status` por tarea (`pending`/`in_progress`/`done`); falta el cálculo de % de avance por proyecto agregando sus tareas |
| 22-P-06 | `finding_id` / `ticket_id` en la tarea | 🟡 Media | Cierra el círculo hallazgo→remediación→evidencia descrito en la propuesta original; quedó fuera del alcance de `22-P-01` a propósito |

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
