"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Bell } from "lucide-react";
import Link from "next/link";

import { AlertItem, getAlerts } from "@/lib/api";
import { useAlertsSocket } from "@/lib/hooks/use-alerts-socket";
import { QK } from "@/lib/query-keys";
import { ListRow } from "./dashboard-widgets";

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Crítica", high: "Alta", medium: "Media", low: "Baja", info: "Info",
};

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical": return "var(--danger)";
    case "high":     return "#F59E0B";
    case "medium":   return "var(--warning)";
    default:         return "var(--success)";
  }
}

export function formatRelativeDate(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Math.floor((Date.now() - d.getTime()) / 60000);
  if (diff < 1)    return "ahora mismo";
  if (diff < 60)   return `hace ${diff} min`;
  if (diff < 1440) return `hace ${Math.floor(diff / 60)} h`;
  return `hace ${Math.floor(diff / 1440)} días`;
}

type AlertsWidgetProps = {
  alerts: AlertItem[];
};

/** Panel completo de alertas activas — usado en el dashboard general. */
export function AlertsWidget({ alerts }: AlertsWidgetProps) {
  return (
    <article className="panel">
      <div className="panel-head">
        <div><p className="eyebrow">Alertas activas</p><h3>Licencias, tickets y hallazgos</h3></div>
        <span className="muted-small">{alerts.length} alerta{alerts.length !== 1 ? "s" : ""}</span>
      </div>
      {alerts.length === 0 ? (
        <div className="empty-state" style={{ color: "var(--success)" }}>✓ Sin alertas activas — todo en orden</div>
      ) : (
        <div className="stack-gap-sm">
          {alerts.map((alert) => (
            <ListRow
              key={`${alert.type}-${alert.entity_id}`}
              icon={<AlertTriangle size={16} />}
              iconColor={severityColor(alert.severity)}
              title={alert.message}
              subtitle={alert.entity_type}
              meta={formatRelativeDate(alert.created_at)}
              badge={{ label: SEVERITY_LABEL[alert.severity] ?? alert.severity, color: severityColor(alert.severity) }}
            />
          ))}
        </div>
      )}
    </article>
  );
}

const BELL_PREVIEW_LIMIT = 6;

/** Campana de notificaciones — visible en el topbar de todas las páginas del dashboard. */
export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const { data: alertsRaw = [] } = useQuery<AlertItem[]>({
    queryKey: QK.alerts(undefined),
    queryFn: () => getAlerts(undefined),
    refetchInterval: 60_000,
  });
  const { pushedAlerts } = useAlertsSocket(true);
  const alerts = pushedAlerts ?? alertsRaw;

  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const totalCount = alerts.length;

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div className="notification-center" ref={rootRef}>
      <button
        type="button"
        className={`notification-bell ${criticalCount > 0 ? "notification-bell--critical" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-label={`Notificaciones${totalCount > 0 ? `, ${totalCount} activas` : ""}`}
        aria-expanded={open}
      >
        <Bell size={18} />
        {totalCount > 0 && (
          <span className={`notification-bell__count ${criticalCount > 0 ? "notification-bell__count--critical" : ""}`}>
            {totalCount > 9 ? "9+" : totalCount}
          </span>
        )}
      </button>

      {open && (
        <div className="notification-panel">
          <div className="notification-panel__head">
            <strong>Notificaciones</strong>
            <span className="muted-small">{totalCount} activa{totalCount !== 1 ? "s" : ""}</span>
          </div>
          <div className="notification-panel__body">
            {alerts.length === 0 ? (
              <div className="empty-state" style={{ color: "var(--success)" }}>✓ Sin alertas activas</div>
            ) : (
              alerts.slice(0, BELL_PREVIEW_LIMIT).map((alert) => (
                <ListRow
                  key={`${alert.type}-${alert.entity_id}`}
                  icon={<AlertTriangle size={16} />}
                  iconColor={severityColor(alert.severity)}
                  title={alert.message}
                  subtitle={alert.entity_type}
                  meta={formatRelativeDate(alert.created_at)}
                  badge={{ label: SEVERITY_LABEL[alert.severity] ?? alert.severity, color: severityColor(alert.severity) }}
                />
              ))
            )}
          </div>
          {alerts.length > 0 && (
            <Link href="/dashboard" className="notification-panel__footer" onClick={() => setOpen(false)}>
              Ver todas en el dashboard
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
