# Módulo: Postulaciones (Reclutamiento)

**Ruta:** `/dashboard/applications` · `/portal/applications`
**Acceso:** `super_admin`, `admin`, `collaborator` (solo las asignadas a él)
**Backend:** `modules/recruitment` · prefijo `/job-applications`

---

## ¿Qué es?

Pipeline de reclutamiento de NinjaSec. Captura postulaciones desde el sitio público (formulario "Colabora"), las asigna a revisores del equipo, recoge evaluaciones con puntaje y recomendación, y mantiene una bitácora inmutable de todo el proceso.

Nace del origen del proyecto: incorporar estudiantes UPeU de Desarrollo, Infraestructura y Ciberseguridad como colaboradores.

---

## Entidades

| Tabla | Rol |
|---|---|
| `job_applications` | La postulación: datos del candidato, rol deseado, CV, portafolio, estado, origen |
| `application_assignments` | Qué revisor evalúa qué postulación (quién lo asignó y en qué rol) |
| `application_reviews` | Evaluación: `score` numérico + recomendación + notas |
| `application_notes` | Comentarios con `visibility` (`internal` por defecto) |
| `application_attachments` | Archivos adjuntos con tipo y usuario que subió |
| `application_events` | Timeline append-only: cada cambio genera un evento con `payload_json` |

---

## Estados de la postulación

| Estado | Descripción |
|---|---|
| `new` | Recién recibida, sin triaje |
| `screening` | En revisión de perfil / filtro inicial |
| `interview` | Convocado a entrevista |
| `offer` | Con oferta emitida |
| `hired` | Contratado — pasa a ser colaborador |
| `rejected` | Descartado |
| `withdrawn` | El candidato se retiró |
| `on_hold` | Congelado, se retomará después |

## Recomendaciones de evaluación

| Valor | Significado |
|---|---|
| `approve` | Avanzar en el pipeline |
| `reject` | Descartar |
| `hold` | Mantener en espera |

---

## Funcionalidades

### Filtros disponibles
- Por estado
- Por rol deseado (`desired_role`)
- Por revisor asignado (`reviewer_id`) — solo admin/super_admin
- Por rango de fechas (`date_from` / `date_to`)

### Alta pública
`POST /job-applications/` es **el único endpoint sin autenticación** del módulo. Lo consume el formulario público de la web y siempre crea la postulación en estado `new`.

### Asignación de revisores
Admin o super_admin asignan uno o más revisores. A partir de ahí el `collaborator` solo ve las postulaciones donde figura como `reviewer_user_id` — el filtrado ocurre en el query del backend, no en la UI.

### Timeline
Cada acción (cambio de estado, asignación, review, nota, adjunto) inserta una fila en `application_events`. Es el registro de auditoría propio del módulo, complementario al audit log global.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | público |
|---|:---:|:---:|:---:|:---:|
| Crear postulación | ✅ | ✅ | ✅ | ✅ |
| Ver todas las postulaciones | ✅ | ✅ | ❌ | ❌ |
| Ver las asignadas a mí | ✅ | ✅ | ✅ | ❌ |
| Cambiar estado | ✅ | ✅ | ✅¹ | ❌ |
| Asignar revisor | ✅ | ✅ | ❌ | ❌ |
| Registrar evaluación (score + recomendación) | ✅ | ✅ | ✅¹ | ❌ |
| Agregar nota | ✅ | ✅ | ✅¹ | ❌ |
| Subir adjunto | ✅ | ✅ | ✅¹ | ❌ |
| Ver timeline | ✅ | ✅ | ✅¹ | ❌ |

¹ Solo sobre postulaciones donde el usuario tiene una asignación activa. Si no la tiene, el backend responde **404** (no 403) para no filtrar la existencia del registro.

---

## Reglas de negocio

1. Toda postulación nace en `new`, sin importar lo que envíe el cliente.
2. Un colaborador sin asignación no puede saber si una postulación existe.
3. Los eventos del timeline son **append-only** — nunca se editan ni borran.
4. Las notas son `internal` por defecto; cambiar la visibilidad es una decisión explícita.
5. Al pasar a `hired`, el candidato se da de alta automáticamente como usuario `collaborator` y perfil, conservando contacto, CV y una referencia explícita a la postulación de origen. Si el email ya pertenece a un usuario, la API responde `409` y no cambia el estado.
