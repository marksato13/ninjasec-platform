# Módulo: Postulaciones (Reclutamiento)

**Ruta:** `/dashboard/applications` · `/portal/applications`
**Acceso:** `super_admin`, `admin`, `collaborator` (solo las asignadas a él)
**Backend:** `modules/recruitment` · prefijo `/job-applications`

---

## ¿Qué es?

Pipeline de reclutamiento de Ninja Tech. Captura postulaciones desde el sitio público (formulario "Colabora"), las asigna a revisores del equipo, recoge evaluaciones con puntaje y recomendación, y mantiene una bitácora inmutable de todo el proceso.

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
| `hired` | Contratado — dispara la conversión automática a colaborador |
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

### Conversión automática a colaborador
Cuando un admin o super_admin cambia una postulación a `hired`, el backend convierte al candidato en colaborador dentro de la misma transacción del cambio de estado:

- Crea un `User` con rol `collaborator`, `organization_id` del actor que contrata, nombre y email de la postulación.
- Crea su `collaborator_profile` con cargo inicial desde `desired_role`, resumen inicial desde `skills_summary`, `portfolio_url` de la postulación y disponibilidad `available`.
- Mantiene trazabilidad explícita con la postulación de origen en `collaborator_profiles.source_application_id`.
- Registra el cambio de estado en el timeline y en auditoría global, incluyendo el colaborador creado.

La operación es idempotente respecto al estado: si la postulación ya está en `hired`, repetir el mismo `PATCH` no crea otro usuario ni otro perfil.

### Conflicto por email duplicado
El email de `users` es único. Si al contratar ya existe un usuario con el mismo email, el backend rechaza la transición a `hired` con **409 Conflict** y no cambia el estado de la postulación. Esta política evita enlazar automáticamente una postulación nueva a una identidad previa sin revisión humana, porque podría mezclar trazabilidad, permisos y datos de otra persona.

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
5. Al pasar a `hired`, el candidato se da de alta automáticamente en Usuarios y Colaboradores.
6. Cada colaborador creado desde reclutamiento conserva `source_application_id` para auditar la postulación que originó el alta.
7. Si el email del candidato ya existe en `users`, la contratación falla con 409 y no se crea ni vincula ningún colaborador.
