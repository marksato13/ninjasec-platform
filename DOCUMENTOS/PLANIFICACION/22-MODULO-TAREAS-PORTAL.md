# Módulo: Tareas y Asignaciones del Portal

**Ruta:** `/portal/tasks`
**Acceso:** usuarios del portal con proyectos asignados
**Backend:** `modules/projects` — reutiliza `/projects` con filtrado por membresía

---

## ¿Qué es?

Vista personal de "mis proyectos" dentro del portal. Muestra únicamente aquello en lo que el usuario autenticado participa, resolviendo la pregunta cotidiana: **¿en qué estoy asignado y en qué estado va?**

No es un gestor de tareas granular tipo Jira: es una vista de asignaciones a nivel de proyecto.

---

## Origen de los datos

No existe tabla `tasks`. La vista se construye llamando a `GET /projects` — el backend ya filtra por membresía (`project_members`) según el rol del solicitante. La UI no filtra nada: recibe solo lo que le corresponde.

Esa decisión mantiene una sola fuente de verdad (el módulo Proyectos) y evita duplicar reglas de permisos.

---

## Estados visibles

| Estado | Etiqueta en UI | Badge |
|---|---|---|
| `planning` | Planificación | `badge-draft` |
| `active` | Activo | `badge-active` |
| `paused` | Pausado | `badge-paused` |
| `completed` | Completado | `badge-archived` |

---

## Funcionalidades

### KPIs de cabecera
Cuatro contadores calculados en cliente sobre los proyectos ya recibidos: Activos · Planificación · Completados · Total.

### Filtro por estado
Selector simple que acota el listado sin llamada adicional al backend.

### Formato de fechas peruano
`toLocaleDateString("es-PE")` — formato `05 ago 2026`, consistente con el resto del portal.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver mis proyectos asignados | ✅ | ✅ | ✅ | ✅ |
| Filtrar por estado | ✅ | ✅ | ✅ | ✅ |
| Ver proyectos de otros | ❌ | ❌ | ❌ | ❌ |
| Editar el proyecto desde el portal | ❌ | ❌ | ❌ | ❌ |

El portal es **solo lectura** para esta vista. La edición vive en `/dashboard/projects`.

---

## Reglas de negocio

1. **El filtrado ocurre en el backend.** La UI nunca recibe proyectos ajenos, ni siquiera para descartarlos.
2. Un usuario sin asignaciones ve la vista vacía con su estado correspondiente, no un error.
3. Los KPIs se calculan sobre el conjunto ya filtrado — reflejan la realidad del usuario, no la de la organización.
4. Sin membresía en `project_members` no hay visibilidad, sin importar el rol.

---

## Limitación conocida

La vista se llama "Tareas" pero opera a nivel de **proyecto**, no de tarea. Para llegar a tareas reales haría falta:

- Tabla `project_tasks` (título, responsable, estado, fecha límite, prioridad)
- Endpoints CRUD con guard por membresía
- Vista Kanban o lista con agrupación por estado
- Vínculo opcional con tickets de soporte y con hallazgos de revisiones

Queda registrado como ampliación futura del módulo **12 — Proyectos**, no como módulo independiente.
