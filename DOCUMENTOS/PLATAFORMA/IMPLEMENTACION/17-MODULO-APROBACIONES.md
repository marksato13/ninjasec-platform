# Implementación — Módulo Aprobaciones

> Basado en: `PLANIFICACION/17-MODULO-APROBACIONES.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Vista consolidada

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Carga en paralelo de skills, certs, doc-types, docs y proyectos | ✅ | `(admin)/dashboard/approvals/page.tsx` → `Promise.all` de 5 queries |
| 2 | Query key única `["approvals"]` | ✅ | `approvals/page.tsx` |
| 3 | Filtro de documentos por proyecto | ✅ | `approvals/page.tsx` → `docProjectFilter` |
| 4 | Modal de alta de tipo de documento | ✅ | `approvals/page.tsx` + `components/ui/modal.tsx` |

### Endpoints de verificación

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 5 | `POST /skills/user-skills/{id}/verify` — solo super_admin | ✅ | `modules/skills/routers/router.py:220` |
| 6 | `POST /user-certifications/{id}/verify` — solo super_admin | ✅ | `modules/certifications/routers/router.py:125` |
| 7 | `POST /project-docs/{id}/verify` — solo super_admin | ✅ | `modules/docs/routers/router.py:276` |
| 8 | `POST /project-docs/{id}/toggle` (activar/desactivar) | ✅ | `modules/docs/routers/router.py:324` |
| 9 | `POST /doc-types` + `PUT /doc-types/{id}` — solo super_admin | ✅ | `modules/docs/routers/router.py:65` / `:90` |

### Sello de verificación

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | `verified_by` + `verified_at` en `user_skills` | ✅ | `db/models/user_skill.py` |
| 11 | `verified_by` + `verified_at` en `user_certifications` | ✅ | `db/models/user_certification.py` |
| 12 | `verified_by` + `verified_at` en `project_docs` | ✅ | `db/models/project_doc.py` |
| 13 | Registro en audit log tras cada verificación | ✅ | vía `AuditService` |

### Notificaciones

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 14 | `notifySuccess` / `notifyError` (nunca `alert()`) | ✅ | `lib/alerts.ts` |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| 17-P-01 | **Contador de pendientes en el sidebar** | 🔴 Alta | Hoy hay que entrar a la bandeja para saber si hay algo. Un badge con el conteo de `pending` evitaría que se acumulen |
| 17-P-02 | Rechazo con motivo obligatorio | 🔴 Alta | Se puede pasar a `rejected` sin explicar por qué. Sin motivo, el colaborador no sabe qué corregir |
| 17-P-03 | Aprobación en lote | 🟡 Media | Verificar 20 skills exige 20 clics |
| 17-P-04 | **Re-verificación al editar** | 🔴 Alta | Editar una skill ya aprobada **no** la devuelve a `pending` — se puede aprobar "Cisco básico" y editarlo a "CCIE" sin nueva revisión ⚠️ · **Duplicado de `21-P-01`: se arregla una sola vez** |
| 17-P-05 | **Expiración automática de certificaciones** | 🔴 Alta | `expires_at` se guarda pero nada lo evalúa; una cert vencida sigue figurando como aprobada · **Duplicado de `21-P-02`: se arregla una sola vez** |
| 17-P-06 | Notificación al declarante | 🟢 Baja | El colaborador no se entera de la resolución |

---

## Riesgo abierto

**`17-P-04` es un agujero de integridad real.** El flujo `declarar → aprobar → editar` permite elevar una capacidad ya verificada sin pasar de nuevo por revisión. Como el directorio de colaboradores es material de cara al cliente, esto compromete la confiabilidad del dato.

**Fix propuesto:** en `PUT /skills/user-skills/{id}` y en el equivalente de certificaciones, si el registro está en `approved` y cambia `skill_id`, `level` o `name`, forzar `status = pending` y limpiar `verified_by` / `verified_at`.
