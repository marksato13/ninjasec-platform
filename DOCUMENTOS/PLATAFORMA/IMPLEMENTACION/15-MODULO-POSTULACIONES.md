# Implementación — Módulo Postulaciones

> Basado en: `PLANIFICACION/15-MODULO-POSTULACIONES.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Entidades y persistencia

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `JobApplication` con 8 estados | ✅ | `db/models/job_application.py` |
| 2 | Modelo `ApplicationAssignment` (revisor + asignador) | ✅ | `db/models/application_assignment.py` |
| 3 | Modelo `ApplicationReview` (score + recomendación) | ✅ | `db/models/application_review.py` |
| 4 | Modelo `ApplicationNote` con `visibility` | ✅ | `db/models/application_note.py` |
| 5 | Modelo `ApplicationAttachment` | ✅ | `db/models/application_attachment.py` |
| 6 | Modelo `ApplicationEvent` (timeline append-only) | ✅ | `db/models/application_event.py` |
| 7 | Enums `JobApplicationStatus` y `ApplicationRecommendation` | ✅ | `db/models/enums.py` |

### Endpoints

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 8 | `GET /job-applications/` con filtros status/rol/revisor/fechas | ✅ | `modules/recruitment/routers/router.py:98` |
| 9 | `POST /job-applications/` **público** — fuerza estado `new` | ✅ | `router.py:152` |
| 10 | `GET /{id}` con guard de acceso | ✅ | `router.py:167` |
| 11 | `PATCH /{id}` cambio de estado | ✅ | `router.py:183` |
| 12 | `POST /{id}/assignments` — solo admin/super_admin | ✅ | `router.py:241` |
| 13 | `GET /{id}/assignments` | ✅ | `router.py:303` |
| 14 | `POST /{id}/reviews` + `GET /{id}/reviews` | ✅ | `router.py:329` / `:382` |
| 15 | `POST /{id}/notes` + `GET /{id}/notes` | ✅ | `router.py:405` / `:448` |
| 16 | `POST /{id}/attachments` + `GET /{id}/attachments` | ✅ | `router.py:469` / `:512` |
| 17 | `GET /{id}/timeline` | ✅ | `router.py:538` |

### Permisos y aislamiento

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 18 | Collaborator solo ve sus asignadas (filtro en el query, con `join` + `distinct`) | ✅ | `router.py:114-123` |
| 19 | Acceso denegado devuelve **404**, no 403 (no filtra existencia) | ✅ | `router.py:_ensure_application_access` |
| 20 | Filtro `reviewer_id` restringido a admin/super_admin | ✅ | `router.py:126-135` |

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 21 | Listado backoffice con 5 filtros | ✅ | `(admin)/dashboard/applications/page.tsx` |
| 22 | Etiquetas de estado en español | ✅ | `applications/page.tsx` → `statusOptions` |
| 23 | Vista portal de postulaciones | ✅ | `(portal)/portal/applications/page.tsx` |
| 24 | Badges de estado con `getStatusBadgeClass` | ✅ | `lib/role-utils.ts` |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| 15-P-01 | **Conversión `hired` → Colaborador** | 🔴 Alta | Al marcar `hired` no se crea el usuario ni el `collaborator_profile`. Hoy es manual y se pierde la trazabilidad del origen |
| 15-P-02 | Upload real de CV | 🟡 Media | `cv_url` y `attachments` guardan solo URL; no hay almacenamiento (comparte bloqueo con `10-P-05`) |
| 15-P-03 | Score agregado por postulación | 🟡 Media | Hay reviews individuales pero no promedio ni consolidado en el listado |
| 15-P-04 | Notificación por correo al candidato | 🟢 Baja | Los cambios de estado no notifican a nadie |
| ~~15-P-05~~ | ~~**Rate limiting en el endpoint público**~~ | — | ✅ **Resuelto 2026-08-06**: `app/common/rate_limit.py` — ventana deslizante en memoria, 5 postulaciones/hora por IP, respeta `X-Forwarded-For`. ⚠️ Es por proceso: con varios workers o réplicas hay que migrarlo a Redis o a Caddy. Tests en `tests/test_public_application_rate_limit.py` (4) |
| 15-P-06 | Vista de detalle con timeline | 🟡 Media | El endpoint `/timeline` existe pero no hay UI que lo consuma |

---

## Nota de seguridad

El endpoint de creación es el **único sin autenticación** de todo el módulo. Antes de exponer la plataforma públicamente (FASE 2.8/2.9 del deploy) hay que resolver `15-P-05`: sin throttling ni CAPTCHA, la tabla `job_applications` es un vector de inundación trivial.
