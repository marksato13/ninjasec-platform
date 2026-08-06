# Implementación — Módulo Reportes

> Basado en: `DOCUMENTOS/PLATAFORMA/09-MODULO-REPORTES.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Estructura de la página

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Filtros globales: cliente + rango de fechas | ✅ | `reports/page.tsx` |
| 2 | Cards con icono, gradiente, título, descripción | ✅ | `reports/page.tsx` → `<ReportCard />` |
| 3 | Preview de métricas en cada card | ✅ | `reports/page.tsx` → prop `meta[]` |
| 4 | Spinner durante descarga | ✅ | `reports/page.tsx` → `loadingPdf`/`loadingXlsx` states |
| 5 | Indicador de último reporte generado | ✅ | `reports/page.tsx` → prop `lastRun` + `relativeDate()` |
| 6 | Gráfico de hallazgos por severidad (barras CSS) | ✅ | `reports/page.tsx` → panel al final |
| 7 | Color `info` en barras = azul (no verde) | ✅ | `reports/page.tsx` → `sev === "low" ? var(--success) : "#3B82F6"` (corregido) |

### 6 tipos de reporte del documento

| # | Tipo | Estado | Endpoint |
|---|------|--------|---------|
| 8 | Reporte de Seguridad PDF | ✅ | Card "Reporte de Seguridad (PDF)" con select inline de revisión + botón "Descargar PDF" llama `exportSecurityReviewPdf(id)` |
| 9 | Inventario de Activos XLSX | ✅ | `GET /devices/export-xlsx` |
| 10 | Tickets de Soporte XLSX | ✅ | `GET /support-tickets/export-xlsx` |
| 11 | Reporte Ejecutivo PDF (Consolidado) | ✅ | `GET /reports/consolidated-pdf` |
| 12 | **Pipeline Comercial XLSX** | ✅ | `GET /leads/export-xlsx` (nuevo) |
| 13 | Consolidado Cliente PDF | ✅ | `GET /reports/consolidated-pdf` (requiere cliente) |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/leads/routers/router.py` | Nuevo endpoint `GET /leads/export-xlsx` (admin/super_admin) — genera XLSX con openpyxl, estilo corporativo NinjaSec. **Nuevo:** acepta `date_from`/`date_to` y filtra por `lead.created_at` |
| `frontend/src/lib/api/leads.ts` | Agregado `exportLeadsXlsx(filters?)` con `date_from`/`date_to` opcionales (usa `buildQuery`) |
| `frontend/src/app/(admin)/dashboard/reports/page.tsx` | Card "Pipeline Comercial" nueva; `QK.leads()` + `getLeads()` para métricas; icono `Target`; fix color `info` en gráfico. **Nuevo:** Card "Reporte de Seguridad (PDF)" con select inline de revisiones (lista `getSecurityReviews({client_id?})`) → botón "Descargar PDF" llama `exportSecurityReviewPdf(id)`. **Nuevo:** sistema `trackExport(type)`/`lastExportFor(type)` que persiste en `localStorage` el ISO timestamp de la última descarga por tipo (`consolidated`, `devices`, `tickets`, `reviews`, `leads`, `review-pdf`) y se muestra en `lastRun` de cada card. **Nuevo:** filtro de fechas se pasa a `exportLeadsXlsx` |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/reports.ts` | `exportConsolidatedReportPdf()`, `exportConsolidatedReportXlsx()`, `getReportRuns()` |
| `frontend/src/lib/api/devices.ts` | `exportDevicesXlsx()` |
| `frontend/src/lib/api/tickets.ts` | `exportSupportTicketsXlsx()` |
| `frontend/src/lib/api/reviews.ts` | `exportSecurityReviewsXlsx()` |
| `backend/app/modules/reports/routers/router.py` | Endpoints consolidados PDF/XLSX |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~09-P-01~~ | ~~Card "Reporte de Seguridad PDF"~~ | ✅ **Implementado**: nueva card con select de revisiones (filtradas por `clientId` si está set) y botón que llama `exportSecurityReviewPdf(id)`. El endpoint `GET /security-reviews/{id}/pdf` se implementó en el módulo 06 |
| ~~09-P-02~~ | ~~`lastRun` para todas las cards~~ | ✅ **Implementado**: tracking en `localStorage` (key `ninjasec_last_export`) con timestamp por tipo. Cada `onPdf`/`onXlsx` envuelto en async function que llama `trackExport(type)` después del download. Cards muestran `lastRun` reactivo con `lastExportFor(type)`. 6 tipos tracked: consolidated, devices, tickets, reviews, leads, review-pdf |
| ~~09-P-03~~ | ~~Gráfico de hallazgos sin orden garantizado~~ | ✅ **Implementado** en sesión anterior |
| ~~09-P-04~~ | ~~Filtro de fechas no aplica a Pipeline Comercial~~ | ✅ **Implementado**: backend `GET /leads/export-xlsx` ahora acepta `date_from`/`date_to` y filtra por `lead.created_at`. Frontend pasa los filtros globales `dateFrom`/`dateTo` al `exportLeadsXlsx` |
| 09-P-05 | Persistir `lastRun` server-side (en vez de localStorage) | El tracking actual es por dispositivo. Para histórico compartido entre usuarios habría que insertar un `ReportRun` por descarga, lo cual requiere mapear cada export a un `report_id` |
