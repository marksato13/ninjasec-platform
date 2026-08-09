# Implementación — Módulo Dashboard Principal

> Basado en: `DOCUMENTOS/PLATAFORMA/02-MODULO-DASHBOARD.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

| # | Requisito del documento | Estado | Archivos |
|---|------------------------|--------|----------|
| 1 | Barra de alertas críticas con `pulse-critical` | ✅ | `dashboard-shell.tsx` |
| 2 | Barra muestra licencias vencidas + tickets sin resolver | ✅ | `dashboard-shell.tsx` |
| 3 | KPI — Revisiones ejecutadas (%) | ✅ | `dashboard-shell.tsx` + `dashboard/router.py` |
| 4 | KPI — Hallazgos críticos abiertos | ✅ | `dashboard-shell.tsx` + `dashboard/router.py` |
| 5 | KPI — Tickets abiertos | ✅ | `dashboard-shell.tsx` + `dashboard/router.py` |
| 6 | KPI — Activos monitoreados | ✅ | `dashboard-shell.tsx` + `dashboard/router.py` |
| 7 | Accesos rápidos: Revisiones, Tickets, Clientes, Inventario | ✅ | `dashboard-widgets.tsx` (`QuickLinks` — 8 atajos) |
| 8 | Actividad reciente — últimas 5 del audit log | ✅ | `dashboard-shell.tsx` + `audit/router.py` |
| 9 | Panel de alertas detallado (severidad, mensaje, tipo, fecha) | ✅ | `dashboard-shell.tsx` |
| 10 | Filtro por cliente — recalcula todos los KPIs | ✅ | `dashboard-shell.tsx` + `dashboard/router.py` |
| 11 | Refrescar alertas manualmente | ✅ | `dashboard-shell.tsx` → `POST /alerts/refresh` |
| 12 | Sin websocket — refresh manual o recarga | ✅ | Auto-refresh opcional con polling cada 60s (toggle persistido) |
| 13 | Filtro por rango de fechas (date_from / date_to) | ✅ | `dashboard-shell.tsx` (inputs + clear button) |
| 14 | Dashboard tabbed con 5 vistas clasificadas | ✅ | `dashboard-shell.tsx` (`TabKey`) + `dashboard-widgets.tsx` |
| 15 | Vista Seguridad — Hallazgos críticos, MTTR, Score por cliente, Próximas revisiones, Top vulns | ✅ | `dashboard-widgets.tsx` (`SecurityView`) |
| 16 | Vista Comercial — Pipeline, conversión, fuentes de leads, nuevos clientes | ✅ | `dashboard-widgets.tsx` (`CommercialView`) |
| 17 | Vista Operaciones — Tickets, SLA, top colaboradores, categorías | ✅ | `dashboard-widgets.tsx` (`OperationsView`) |
| 18 | Vista Infraestructura — Integraciones health, dispositivos, uptime, licencias por vencer | ✅ | `dashboard-widgets.tsx` (`InfrastructureView`) |
| 19 | KPI cards con trend indicator (up/down + %) | ✅ | `dashboard-widgets.tsx` (`KpiCard` + `kpi-card__trend`) |
| 20 | Sparkline / mini-chart de tendencia 7 días | ✅ | `dashboard-widgets.tsx` (`SparkBar`) |
| 21 | Embudo de conversión visual | ✅ | `dashboard-widgets.tsx` (`.funnel` CSS) |
| 22 | Hallazgos por severidad clickeables → security-reviews?severity=X | ✅ | `dashboard-shell.tsx` + `SecurityView` (ProgressRow con `href`) |
| 23 | Fallback mock data cuando backend devuelve vacío | ✅ | `dashboard-widgets.tsx` (MOCK_* constants) + `dashboard-shell.tsx` (MOCK_ALERTS_FALLBACK, MOCK_AUDIT_FALLBACK) |
| 24 | Banner de alerta crítica reactivo (pulse) | ✅ | `dashboard-shell.tsx` (`.alert-banner.pulse-critical`) |

---

## Archivos involucrados

### Frontend

| Archivo | Rol |
|---------|-----|
| `frontend/src/app/(admin)/dashboard/page.tsx` | Entry point — renderiza `<DashboardShell />` |
| `frontend/src/components/dashboard/dashboard-shell.tsx` | Componente principal — tabs, filtros, vista General, polling |
| `frontend/src/components/dashboard/dashboard-widgets.tsx` | Widgets reusables + 4 vistas (Security, Commercial, Operations, Infrastructure) + mocks |
| `frontend/src/app/globals.css` | Estilos de KPI cards, sparkbar, funnel, list-row, progress-row, severity-row, tabs |
| `frontend/src/lib/api/dashboard.ts` | `getDashboardSummary()` → `GET /dashboard/summary` |
| `frontend/src/lib/api/alerts.ts` | `getAlerts()` → `GET /alerts/active`, `refreshAlerts()` → `POST /alerts/refresh` |
| `frontend/src/lib/api/audit.ts` | `getAuditLogs(limit?)` → `GET /audit-logs/?limit=N` |
| `frontend/src/lib/query-keys.ts` | `QK.dashboardSummary`, `QK.alerts`, `QK.auditLogs(limit?)` |

### Backend

| Archivo | Rol |
|---------|-----|
| `backend/app/modules/dashboard/routers/router.py` | `GET /dashboard/summary` — calcula los 4 KPIs y filtros por cliente/fecha |
| `backend/app/modules/audit/routers/router.py` | `GET /audit-logs/?limit=N` — lista logs paginados, ordenados por `created_at DESC` |
| `backend/app/modules/alerts/routers/router.py` | `GET /alerts/active` y `POST /alerts/refresh` |
| `backend/app/modules/dashboard/schemas/dashboard.py` | `DashboardSummary`, `ReviewSummary`, `FindingSummary`, `TicketSummaryDash`, `InventorySummary` |

---

## Cambios realizados en esta sesión

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/audit/routers/router.py` | Agregado `limit: int \| None` query param + `order_by(created_at.desc())` |
| `frontend/src/components/dashboard/dashboard-shell.tsx` | Reescrito: tabs General/Seguridad/Comercial/Operaciones/Infraestructura, auto-refresh con toggle persistido en `localStorage`, KPIs con `KpiCard`, fallback `MOCK_ALERTS_FALLBACK` + `MOCK_AUDIT_FALLBACK` |
| `frontend/src/components/dashboard/dashboard-widgets.tsx` (NUEVO) | `KpiCard`, `SparkBar`, `ProgressRow` (con `href?` para hacer clickeable), `ListRow`, 4 vistas tabbed, 10 constantes mock para que la UI siempre se vea funcional |
| `frontend/src/app/globals.css` | +250 líneas: `.dashboard-tabs`, `.kpi-card`, `.sparkbar`, `.funnel`, `.severity-row--link`, `.progress-row--link`, `.alert-banner`, `.collab-card`, `.quick-link`, `.spin-slow` |
| `frontend/src/lib/query-keys.ts` | `QK.auditLogs()` ahora acepta `limit?: number` para cachear por tamaño |

---

## Notas de implementación

| # | Nota |
|---|------|
| N-01 | El documento menciona `/api/v1/collection/alerts` — el endpoint real es `/api/v1/alerts/active` (módulo `alerts`, no `collection`) |
| N-02 | `critical_open` en el backend cuenta critical + high abiertos (no solo critical). Es comportamiento más seguro que el documento describe |
| N-03 | El semáforo de colores (`kpiColor`) es: verde ≥ umbral peligro, amarillo ≥ umbral warn, rojo < warn — configurable por KPI |
| N-04 | `AuditLog.order_by(created_at.desc())` agregado en sesión anterior — antes venían en orden de inserción |
| N-05 | Auto-refresh: polling de TanStack Query con `refetchInterval: 60000` cuando el toggle está ON. La preferencia se guarda en `localStorage` con key `ninjasec_dashboard_autorefresh` para que se mantenga entre sesiones del navegador. Estado del toggle visible con `Zap` icon en verde (ON) o gris (OFF) |
| N-06 | Mock data fallback: si `alertsRaw.length === 0` se sustituye por `MOCK_ALERTS_FALLBACK`, idem con audit logs. Esto evita que el dashboard luzca "vacío" en demos/instalaciones nuevas y permite ver el diseño funcional. Cuando el backend devuelve datos reales, prevalecen |
| N-07 | El query string `?severity=X` se navega desde el dashboard pero la página `/dashboard/security-reviews` aún no lee el param (queda como mejora futura para filtrar findings al cargar) |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~02-P-01~~ | ~~Filtro por rango de fechas en el dashboard~~ | ✅ **Implementado** en sesión anterior (`date_from`/`date_to`) |
| ~~02-P-02~~ | ~~Refresh automático de alertas (polling)~~ | ✅ **Implementado**: toggle "Auto ON/OFF" en el header del dashboard. Cuando está ON, refetch cada 60s sobre `getDashboardSummary` y `getAlerts`. Preferencia persistida en `localStorage`. WebSocket sigue siendo trabajo futuro si llegara a ser necesario para latencia < 1min |
| ~~02-P-03~~ | ~~Hallazgos por severidad sin link directo~~ | ✅ **Implementado**: cada fila/barra de severidad es un `<Link>` a `/dashboard/security-reviews?severity={sev}`. Aplica tanto en la vista General como en la vista Seguridad |
| 02-P-04 | La página `/dashboard/security-reviews` debería leer `?severity=X` y aplicar filtro al cargar | Requiere `useSearchParams` y enlazar al state interno del filtro de la página; mejora menor de UX |
| ~~02-P-05~~ | ~~WebSocket / push real-time para alertas críticas (en vez de polling 60s)~~ | ✅ **Resuelto 2026-08-09**: `GET /api/v1/alerts/ws?token=...` (auth por query param, no hay header en el handshake) recalcula alertas cada 12s server-side y solo empuja si el conjunto cambió (firma sin `created_at`, para no emitir de más). Aislado por `organization_id` del token, igual que `/alerts/active` — se refactorizó la lógica común a `compute_active_alerts()`. Frontend: `lib/hooks/use-alerts-socket.ts`, con reconexión automática y fallback transparente al polling existente si no conecta (timeout 5s) o se corta — el toggle "Auto ON/OFF" sigue siendo el único control. Verificado en `tests/test_alerts_websocket.py`: token inválido cierra la conexión, admin recibe alertas reales por el socket, aislamiento cross-tenant (otra organización no ve nada). |
