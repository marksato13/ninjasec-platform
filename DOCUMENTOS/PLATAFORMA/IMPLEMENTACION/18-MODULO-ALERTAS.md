# Implementación — Módulo Alertas

> Basado en: `PLANIFICACION/18-MODULO-ALERTAS.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Motor de alertas derivadas

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | `GET /alerts/active` con filtro opcional `client_id` | ✅ | `modules/alerts/routers/router.py:31` |
| 2 | Alerta `license_expired` (integración con licencia vencida) | ✅ | `router.py:_license_expired_alerts` |
| 3 | Alerta `critical_finding_open` | ✅ | `router.py:_critical_finding_alerts` |
| 4 | Alerta `ticket_overdue` (>7 días) | ✅ | `router.py:_ticket_overdue_alerts` |
| 5 | Supresión: hallazgo con ticket **o** recomendación no alerta | ✅ | `router.py` → sets `ticketed` / `recommended` |
| 6 | Orden critical → warning → info impuesto por el backend | ✅ | `router.py:53-55` |
| 7 | Severidad derivada del nivel del hallazgo | ✅ | `critical` si CRITICAL, `warning` si HIGH |
| 8 | **Sin tabla `alerts`** — todo se calcula al vuelo | ✅ | Verificado: no existe modelo de alerta |

### Refresh en batch

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 9 | `POST /alerts/refresh` restringido a super_admin | ✅ | `router.py:69` |
| 10 | Integraciones con licencia vencida → `status = "risk"` | ✅ | `router.py:85-95` |
| 11 | Devices sin revisión >30 días → `pending_review` | ✅ | `router.py:97-125` |
| 12 | Exclusión de devices `retired` / `inactive` | ✅ | `_INACTIVE_DEVICE` |
| 13 | Registro en audit log con conteos | ✅ | `AuditService(db).record(..., "alerts.refresh", ...)` |
| 14 | Respuesta con `integrations_marked_risk` + `devices_marked_pending_review` | ✅ | `schemas/alert.py` |

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 15 | Widget de alertas en el dashboard | ✅ | `components/dashboard/dashboard-widgets.tsx` |
| 16 | Auto-refresh 60 s con toggle persistido | ✅ | `dashboard-shell.tsx` → `localStorage.ninjasec_dashboard_autorefresh` |
| 17 | Mensajes ya redactados en español desde el backend | ✅ | `router.py` (f-strings en español) |
| 18 | Alertas no visibles para el rol `client` | ✅ | `require_roles` excluye CLIENT |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| 18-P-01 | **WebSocket en lugar de polling** | 🟡 Media | Hoy 60 s de latencia y una consulta completa por cliente conectado. Heredado de `02-P-05` |
| ~~18-P-02~~ | ~~**Umbrales configurables por organización**~~ | — | ✅ **Resuelto 2026-08-08**: tabla `organization_alert_thresholds`, `GET/PUT /alerts/thresholds` restringidos a admin y motor de alertas con fallback 7/30. Tests en `tests/test_alert_thresholds.py` |
| 18-P-03 | Alerta de certificación por vencer | 🟡 Media | `user_certifications.expires_at` existe y nadie lo vigila (conecta con `17-P-05`) |
| 18-P-04 | Alerta de dispositivo crítico caído | 🔴 Alta | `Device.criticality` ya existe; un `critical` en `offline` debería ser alerta roja inmediata |
| 18-P-05 | Alerta de garantía vencida | 🟢 Baja | Requiere el campo `warranty_expires_at`, aún no implementado |
| 18-P-06 | Notificación por correo de alertas críticas | 🟡 Media | Hoy solo se ven entrando al dashboard. Conecta con la idea "SOC as a report" |
| 18-P-07 | Job programado para `refresh` | 🟡 Media | Requiere ejecución manual por super_admin; debería correr por cron nocturno |

---

## Observación de diseño

La decisión de **no persistir alertas** es acertada y hay que preservarla: elimina las alertas zombi y la necesidad de un flujo de "cerrar alerta". El costo es que no existe histórico — no se puede responder "¿cuántas alertas críticas tuvimos en julio?".

Si se necesita esa métrica, la vía correcta es una tabla `alert_snapshots` que guarde el conteo diario por tipo y severidad, **sin** convertir las alertas en entidades gestionables.
