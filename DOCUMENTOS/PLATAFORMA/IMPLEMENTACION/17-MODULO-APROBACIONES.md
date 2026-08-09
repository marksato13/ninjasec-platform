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

### `17-P-01` / `17-P-02` — contador y rechazo trazable

| # | Criterio | Estado | Evidencia verificable |
|---|----------|--------|-----------------------|
| 15 | El sidebar muestra un contador de aprobaciones pendientes para el aprobador | ✅ | `frontend/src/components/dashboard/sidebar.tsx` consulta `QK.pendingApprovals()` con `getPendingApprovalsCount()` y pinta el badge junto a **Aprobaciones** solo si `pending > 0` |
| 16 | El contador suma skills y certificaciones en `pending` del tenant actual | ✅ | `backend/app/modules/skills/routers/router.py` expone `GET /skills/approvals/pending-count`; el query filtra por `User.organization_id == current_user.organization_id` y por estados `SkillStatus.PENDING` / `CertificationStatus.PENDING` |
| 17 | Resolver una aprobación conserva el flujo existente e invalida el contador | ✅ | `frontend/src/app/(admin)/dashboard/approvals/page.tsx` mantiene los botones **Aprobar** / **Rechazar**; tras verificar invalida `["approvals"]` y `QK.pendingApprovals()` |
| 18 | Rechazar exige motivo no vacío desde la UI | ✅ | `approvals/page.tsx` abre el modal **Motivo del rechazo**, usa el placeholder **"Explica qué debe corregir el solicitante"** y muestra `notifyError("El motivo de rechazo es obligatorio")` si el texto queda vacío tras `trim()` |
| 19 | Rechazar exige motivo no vacío desde el backend | ✅ | `UserSkillVerify` y `UserCertificationVerify` normalizan `rejection_reason` con `strip()` y devuelven validación 422 con **"El motivo de rechazo es obligatorio"** cuando `status == "rejected"` sin motivo |
| 20 | El motivo se persiste y queda visible para el solicitante | ✅ | Migración `20260808_04_approval_rejection_reason.py` agrega `rejection_reason` a `user_skills` y `user_certifications`; `portal/profile/page.tsx` muestra **"Motivo:"** en skills/certificaciones rechazadas |
| 21 | Aprobar no exige motivo ni hereda un motivo anterior | ✅ | `verify_user_skill()` y `verify_user_certification()` guardan `rejection_reason` solo cuando el estado final es `rejected`; en otro estado lo limpian con `None` |
| 22 | La auditoría conserva el motivo de rechazo | ✅ | Los eventos `user_skill.rejected` y `user_certification.rejected` incluyen `rejection_reason` en `metadata_json` |

**Comportamiento esperado:**

- El flujo de aprobación existente se conserva explícitamente: el `super_admin` puede aprobar skills y certificaciones desde la misma bandeja, usando los botones **Aprobar** sin modal de motivo. La acción sigue grabando `status = approved`, `verified_by`, `verified_at` y audit log.
- El botón **Rechazar** ya no cambia el estado de inmediato. Primero abre el modal **Motivo del rechazo**.
- Si el aprobador confirma el rechazo sin texto útil, la UI muestra **"El motivo de rechazo es obligatorio"** y no llama al endpoint.
- Si alguien llama al endpoint directamente con `{"status": "rejected"}` o con `rejection_reason` vacío/blanco, el backend responde 422 con **"El motivo de rechazo es obligatorio"**.
- Un rechazo válido envía `{"status": "rejected", "rejection_reason": "<motivo>"}`, guarda el motivo, actualiza el registro local e invalida el contador del sidebar.
- El solicitante ve el motivo en `/portal/profile` debajo del skill o certificación rechazada con la etiqueta **"Motivo:"**.
- El badge de **Aprobaciones** se oculta cuando el conteo es `0` y muestra el número de pendientes cuando `pending > 0`.

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~17-P-01~~ | ~~**Contador de pendientes en el sidebar**~~ | — | ✅ **Resuelto 2026-08-08** — endpoint tenant-aware `/skills/approvals/pending-count`, badge visible al aprobador e invalidación inmediata tras resolver |
| ~~17-P-02~~ | ~~Rechazo con motivo obligatorio~~ | — | ✅ **Resuelto 2026-08-08** — validación backend/UI, persistencia en skills y certificaciones, motivo visible al solicitante y evidencia en audit log |
| 17-P-03 | Aprobación en lote | 🟡 Media | Verificar 20 skills exige 20 clics |
| ~~17-P-04~~ | ~~**Re-verificación al editar**~~ | — | ✅ **Resuelto 2026-08-06** junto con `21-P-01` — mismo fix, `app/common/verification.py` |
| ~~17-P-05~~ | ~~**Expiración automática de certificaciones**~~ | — | ✅ **Resuelto 2026-08-06** junto con `21-P-02` — mismo fix, campos derivados en el schema |
| 17-P-06 | Notificación al declarante | 🟢 Baja | El colaborador no se entera de la resolución |

---

## ✅ Riesgo cerrado — 2026-08-06

**`17-P-04` era un agujero de integridad real.** El flujo `declarar → aprobar → editar` permitía elevar una capacidad ya verificada sin pasar de nuevo por revisión. Como el directorio de colaboradores es material de cara al cliente, comprometía la confiabilidad del dato.

**Cerrado** con `app/common/verification.py`. La regla vive en un único sitio para que skills y certificaciones no puedan divergir:

- Editar un campo material de un registro `approved` lo devuelve a `pending` y limpia `verified_by` / `verified_at`
- Reenviar el mismo valor **no** revoca — guardar un formulario sin tocarlo no penaliza al colaborador
- Un registro `rejected` no asciende a `pending` por una edición
- La revocación queda en el audit log con los campos que la motivaron

**Fix propuesto:** en `PUT /skills/user-skills/{id}` y en el equivalente de certificaciones, si el registro está en `approved` y cambia `skill_id`, `level` o `name`, forzar `status = pending` y limpiar `verified_by` / `verified_at`.
