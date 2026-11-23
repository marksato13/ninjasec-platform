# Implementación — Módulo Revisiones de Seguridad

> Basado en: `DOCUMENTOS/06-MODULO-REVISIONES.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Listado `/dashboard/security-reviews`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Ver todas las revisiones (admin/super_admin) | ✅ | `security-reviews/page.tsx` |
| 2 | Ver solo revisiones asignadas (collaborator) | ✅ | `security_reviews/routers/router.py` → filtro `reviewer_user_id == current_user.id` |
| 3 | Filtro por cliente | ✅ | `security-reviews/page.tsx` |
| 4 | Filtro por estado | ✅ | `security-reviews/page.tsx` |
| 5 | KPI strip clickable (scheduled / in_progress / closed / total) | ✅ | `security-reviews/page.tsx` |
| 6 | Crear revisión (admin/super_admin) | ✅ | `security-reviews/page.tsx` → modal + `createSecurityReview()` |
| 7 | Eliminar revisión (solo super_admin) | ✅ | `security-reviews/page.tsx` + backend `DELETE /security-reviews/{id}` |
| 8 | Exportar XLSX del listado | ✅ | `security-reviews/page.tsx` → `exportSecurityReviewsXlsx()` |

### Detalle `/dashboard/security-reviews/[id]`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 9 | Tab Info — datos generales (estado, revisor, fechas, notas) | ✅ | `security-reviews/[id]/page.tsx` |
| 10 | Tab Checklist — ítems de verificación (pass/fail/n/a/partial) | ✅ | `security-reviews/[id]/page.tsx` |
| 11 | Tab Hallazgos — severidad, título, descripción, estado | ✅ | `security-reviews/[id]/page.tsx` |
| 12 | Tab Hallazgos — severidad `info` renderiza correctamente | ✅ | `security-reviews/[id]/page.tsx` → `SEVERITY_BADGE.info` agregado |
| 13 | Tab Hallazgos — crear ticket desde hallazgo crítico/alto | ✅ | `security-reviews/[id]/page.tsx` → `createTicketFromFinding()` |
| 14 | Tab Recomendaciones — agregar con responsable y fecha límite | ✅ | `security-reviews/[id]/page.tsx` |
| 15 | Tab Adjuntos (evidencia) — agregar por URL | ✅ | `security-reviews/[id]/page.tsx` |
| 16 | Tab Tickets — lista de tickets vinculados a esta revisión | ✅ | `security-reviews/[id]/page.tsx` |
| 17 | Mini KPIs: críticos abiertos, hallazgos abiertos, checklist % | ✅ | `security-reviews/[id]/page.tsx` |
| 18 | Cerrar revisión (todos los roles según documento) | ✅ | `security-reviews/[id]/page.tsx` → `updateSecurityReview(status: "closed")` |
| 19 | Eliminar revisión — botón solo para super_admin | ✅ | `security-reviews/[id]/page.tsx` → `isSuperAdmin` + redirect |
| 20 | Exportar PDF del reporte | ✅ | `GET /security-reviews/{id}/pdf` con ReportLab + frontend `exportSecurityReviewPdf()` + botón en el detalle |

### Hallazgos y estados

| # | Severidad/Estado | Implementado |
|---|-----------------|-------------|
| 21 | critical → rojo | ✅ `badge-rejected` |
| 22 | high → naranja | ✅ `badge-pending` |
| 23 | medium → amarillo | ✅ `badge-draft` |
| 24 | low → verde | ✅ `badge-active` |
| 25 | info → azul | ✅ `badge-info` (clase propia con azul claro #93c5fd) |

### Impacto en Dashboard

| # | Requisito | Estado |
|---|-----------|--------|
| 26 | Hallazgos críticos abiertos → KPI dashboard | ✅ `backend/dashboard/router.py` |
| 27 | % revisiones ejecutadas → KPI dashboard | ✅ `backend/dashboard/router.py` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/security_reviews/routers/router.py` | Filtro collaborator (`reviewer_user_id == current_user.id`) en `list_reviews`; nuevo `DELETE /security-reviews/{id}` — solo super_admin. Nuevo `GET /security-reviews/{id}/pdf` con guard de rol: collaborator solo sus asignadas, cliente solo cerradas de su empresa. Audit log `security_review.exported_pdf` |
| `backend/app/modules/reports/services/pdf_service.py` | Nueva función `generate_security_review_pdf()` — resumen ejecutivo con veredicto coloreado (✓/○/✗), datos de revisión, estadísticas por severidad/estado, checklist tabla, hallazgos en detalle con severidad coloreada, recomendaciones y notas internas |
| `frontend/src/lib/api/reviews.ts` | Agregado `deleteSecurityReview()` → `DELETE /security-reviews/{id}`. Nuevo `exportSecurityReviewPdf(id)` → `GET /security-reviews/{id}/pdf` |
| `frontend/src/app/(admin)/dashboard/security-reviews/page.tsx` | Botón export XLSX, botón eliminar por card (super_admin), función `handleDelete()` |
| `frontend/src/app/(admin)/dashboard/security-reviews/[id]/page.tsx` | `SEVERITY_BADGE.info` → `badge-info`. Botón "Exportar PDF" en el header del detalle. Botón eliminar en heading (super_admin + redirect) |
| `frontend/src/app/globals.css` | Nueva clase `.badge-info` con azul `#93c5fd` y borde — diferencia visual real respecto a `medium` |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/reviews.ts` | Todas las funciones de reviews: create, update, findings, checklist, recommendations, attachments |
| `backend/app/modules/security_reviews/schemas/` | `SecurityReviewDetail` incluye findings, checklist, recommendations, attachments |
| `backend/app/modules/security_reviews/routers/router.py` | Validación: cerrar requiere `reviewer_user_id`; critical/high findings requieren recomendación o ticket |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~06-P-01~~ | ~~Exportar PDF del reporte individual~~ | ✅ **Implementado**: `GET /security-reviews/{id}/pdf` con ReportLab. Verificado vía API: devuelve 4.9 KB de PDF con magic `%PDF`. Botón "Exportar PDF" en el header del detalle (visible a admin/super_admin/collaborator/client, con guards por rol en backend) |
| ~~06-P-02~~ | ~~Collaborator puede editar solo sus propias revisiones~~ | ✅ **Implementado** en sesión anterior |
| ~~06-P-03~~ | ~~Resumen ejecutivo / notas de cierre en PDF~~ | ✅ **Implementado**: el PDF abre con sección "RESUMEN EJECUTIVO" con (1) veredicto coloreado — verde ✓ "postura adecuada" / amarillo ○ "aceptable con observaciones" / rojo ✗ "atención inmediata" — calculado a partir del conteo de hallazgos críticos/altos abiertos; (2) párrafo descriptivo con conteo por severidad y % de cumplimiento checklist. Luego: datos de revisión, estadísticas, checklist, hallazgos en detalle con severidad coloreada, recomendaciones, y notas internas si las hay |
| ~~06-P-04~~ | ~~Severidad `info` diferenciada visualmente del color de `medium`~~ | ✅ **Implementado**: clase `.badge-info` (azul claro `#93c5fd` con borde) y `SEVERITY_BADGE.info = "badge-info"` en lugar del `badge-draft` compartido. Ahora info se distingue de medium |
| 06-P-05 | Exportar PDF también desde el listado (XLSX ya está) | Mejora UX: agregar columna de acción "PDF" en el listado para descargar sin entrar al detalle |
