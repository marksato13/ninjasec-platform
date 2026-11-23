# Implementación — Módulo Integraciones

> Basado en: `DOCUMENTOS/04-MODULO-INTEGRACIONES.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Listado `/dashboard/integrations`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Nombre de la consola | ✅ | `integrations/page.tsx` |
| 2 | Tipo (pfSense / FortiGate) | ✅ | `integrations/page.tsx` → `connector_type` |
| 3 | Cliente al que pertenece | ✅ | `integrations/page.tsx` → fetch `getClients()` + lookup |
| 4 | Ambiente (prod / dev / lab) | ✅ | `integrations/page.tsx` → `item.environment` |
| 5 | Estado de salud con semáforo (verde / amarillo / rojo) | ✅ | `integrations/page.tsx` → `healthColor()` en `borderLeft` |
| 6 | Días para vencimiento de licencia | ✅ | `integrations/page.tsx` → `licenseDaysLabel()` |
| 7 | Badge usa `effective_status` (no `status` crudo) | ✅ | `integrations/page.tsx` → `item.effective_status \|\| item.status` |
| 8 | Crear integración (admin) | ✅ | `integrations/page.tsx` → `<IntegrationForm />` |
| 9 | Eliminar integración (solo super_admin) | ✅ | `integrations/page.tsx` + backend `DELETE /integrations/{id}` |

### Detalle `/dashboard/integrations/[id]`

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | KPI — Dispositivos activos | ✅ | `integrations/[id]/page.tsx` |
| 11 | KPI — Dispositivos en revisión pendiente | ✅ | `integrations/[id]/page.tsx` |
| 12 | KPI — Días hasta vencimiento de licencia | ✅ | `integrations/[id]/page.tsx` → `licenseRelative` |
| 13 | KPI — Total revisiones + último review | ✅ | `integrations/[id]/page.tsx` → `daysSinceReview` |
| 14 | HealthIndicator (banner verde/amarillo/rojo) | ✅ | `integrations/[id]/page.tsx` → `<HealthIndicator />` |
| 15 | Tipo de licencia | ✅ | `integrations/[id]/page.tsx` → form |
| 16 | Usuario responsable | ✅ | `integrations/[id]/page.tsx` → select usuarios |
| 17 | Ambiente | ✅ | `integrations/[id]/page.tsx` → select environments |
| 18 | Fecha de último review | ✅ | `integrations/[id]/page.tsx` → `daysSinceReview` (warning si > 90 días) |
| 19 | Tabla de activos asociados | ✅ | `integrations/[id]/page.tsx` |
| 20 | Tabla de revisiones | ✅ | `integrations/[id]/page.tsx` |
| 21 | Editar integración | ✅ | `integrations/[id]/page.tsx` → `updateIntegration()` |

### Alertas automáticas

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 22 | Alerta crítica si licencia vencida | ✅ | `backend/alerts/router.py` → `POST /alerts/refresh` |
| 23 | Alerta warning si licencia vence en < 30 días | ✅ | Mismo |
| 24 | Alerta si sin revisión en > 90 días | ✅ | Mismo, + warning color en KPI detalle |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/lib/api/integrations.ts` | Agregado `deleteIntegration()` → `DELETE /integrations/{id}` |
| `frontend/src/app/(admin)/dashboard/integrations/page.tsx` | Reescrito: cliente por nombre, ambiente, semáforo de color, countdown licencia, delete (super_admin), `effective_status` en badge. Botones Test/Collect ahora visibles para colaborador (no solo admin) |
| `frontend/src/app/(admin)/dashboard/integrations/[id]/page.tsx` | KPI revisiones ahora muestra días desde último review con warning si > 90 días. Banner explícito con CTA "Programar revisión" cuando `daysSinceReview > 90` o cuando no hay revisiones ejecutadas |
| `backend/app/modules/integrations/routers/router.py` | Agregado `DELETE /integrations/{id}` — solo super_admin, con audit log. `POST /test-connection` y `POST /{id}/collect` ahora aceptan rol COLLABORATOR |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/integrations.ts` | `IntegrationItem` incluye `license_expires_at`, `is_license_expired`, `effective_status` |
| `backend/app/modules/integrations/schemas/` | `IntegrationRead` calcula `effective_status` e `is_license_expired` via `model_validator` |
| `backend/app/modules/alerts/routers/router.py` | Genera alertas de licencia en `GET /alerts/active` |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~04-P-01~~ | ~~Filtro por cliente en el listado~~ | ✅ **Implementado**: `integrations/page.tsx` → `clientFilter` state + select dropdown en `panel-head`; filtra `items` por `item.client_id`. |
| ~~04-P-02~~ | ~~Test y Collect visibles para collaborator~~ | ✅ **Implementado**: en frontend, `canOperate = isAdmin \|\| role === "collaborator"` controla la visibilidad. En backend, `POST /test-connection` y `POST /{id}/collect` ahora aceptan `RoleCode.COLLABORATOR`. Verificado vía API: collaborator recibe `200 "Collection scheduled"`. |
| ~~04-P-03~~ | ~~Alerta específica para "sin revisión en 90 días" en el detalle~~ | ✅ **Implementado**: banner ámbar visible bajo el HealthIndicator cuando `daysSinceReview > 90` con CTA "Programar revisión" → `/dashboard/security-reviews?integration_id=N`. También se muestra cuando no hay revisiones ejecutadas con CTA "Programar primera revisión". |
