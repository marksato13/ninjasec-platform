"use client";

/**
 * Primitivas visuales del panel. Aquí no hay datos: quien las usa pasa valores
 * reales del backend. (Antes este archivo traía constantes simuladas que se pintaban como si
 * fueran reales cuando la base estaba vacía; se eliminaron.)
 */

import Link from "next/link";
import type { ReactNode } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

/** Fondo suave del color dado. Funciona con hex y con var(--x); el viejo `${color}1A` no
 *  servia con variables CSS (generaba "var(--primary)1A", que el navegador descarta). */
function tint(color: string, pct: number) {
  return `color-mix(in srgb, ${color} ${pct}%, transparent)`;
}

type KpiCardProps = {
  icon: ReactNode;
  label: string;
  value: string | number;
  sublabel?: string;
  color?: string;
  trend?: { value: number; direction: "up" | "down" };
};

export function KpiCard({ icon, label, value, sublabel, color, trend }: KpiCardProps) {
  return (
    <article className="metric-card panel kpi-card">
      <div className="kpi-card__head">
        <span className="kpi-card__icon" style={{ background: tint(color ?? "var(--primary)", 12), color: color ?? "var(--primary)" }}>
          {icon}
        </span>
        <span className="kpi-card__label">{label}</span>
      </div>
      <div className="kpi-card__value-row">
        <strong className="kpi-card__value">{value}</strong>
        {trend ? (
          <span
            className="kpi-card__trend"
            style={{
              color: trend.direction === "up" ? "var(--success)" : "var(--danger)",
              background: tint(trend.direction === "up" ? "var(--success)" : "var(--danger)", 12),
            }}
          >
            {trend.direction === "up" ? <TrendingUp size={11} aria-hidden="true" /> : <TrendingDown size={11} aria-hidden="true" />}
            <span className="sr-only">{trend.direction === "up" ? "Sube" : "Baja"}</span>
            {trend.value}%
          </span>
        ) : null}
      </div>
      {sublabel ? <span className="kpi-card__sublabel">{sublabel}</span> : null}
    </article>
  );
}

type SparkBarProps = {
  data: number[];
  color?: string;
  height?: number;
  /** Que mide la serie, para el lector de pantalla (p. ej. "Tickets por semana"). */
  label?: string;
};

/**
 * Mini grafico de barras. Un solo tono: la magnitud la dice la altura, no la
 * opacidad. La ultima barra (el periodo actual) se resalta. Sin datos, lo dice.
 */
export function SparkBar({ data, color = "var(--primary)", height = 36, label = "Serie" }: SparkBarProps) {
  const max = Math.max(...data, 0);
  if (data.length === 0 || max === 0) {
    return <div className="sparkbar sparkbar--empty" style={{ height }}>Sin datos todavía</div>;
  }
  return (
    <div className="sparkbar" style={{ height }} role="img" aria-label={`${label}: ${data.join(", ")}`}>
      {data.map((v, i) => (
        <span
          key={i}
          className={`sparkbar__bar${i === data.length - 1 ? " is-current" : ""}`}
          title={String(v)}
          style={{
            height: `${Math.max(4, (v / max) * 100)}%`,
            background: i === data.length - 1 ? color : tint(color, 45),
          }}
        />
      ))}
    </div>
  );
}

type ProgressRowProps = {
  label: string;
  value: number;
  total: number;
  color?: string;
  href?: string;
};

export function ProgressRow({ label, value, total, color = "var(--primary)", href }: ProgressRowProps) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  const Wrapper: React.ElementType = href ? Link : "div";
  const wrapperProps = href ? { href, className: "progress-row progress-row--link", title: `Ver ${label}` } : { className: "progress-row" };
  return (
    <Wrapper {...wrapperProps}>
      <div className="progress-row__head">
        <span className="progress-row__label">{label}</span>
        <span className="progress-row__count">
          {value}
          {total > 0 ? <span className="progress-row__pct"> · {pct} %</span> : null}
        </span>
      </div>
      <div
        className="progress-row__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={value}
      >
        <div className="progress-row__fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </Wrapper>
  );
}

type ListRowProps = {
  icon: ReactNode;
  iconColor?: string;
  title: string;
  subtitle?: string;
  meta?: string;
  badge?: { label: string; color: string };
};

export function ListRow({ icon, iconColor, title, subtitle, meta, badge }: ListRowProps) {
  return (
    <div className="list-row">
      <span className="list-row__icon" style={{ background: tint(iconColor ?? "var(--primary)", 12), color: iconColor ?? "var(--primary)" }}>
        {icon}
      </span>
      <div className="list-row__body">
        <div className="list-row__title">{title}</div>
        {subtitle ? <div className="list-row__subtitle">{subtitle}</div> : null}
      </div>
      <div className="list-row__right">
        {badge ? (
          <span className="list-row__badge" style={{ color: badge.color, background: tint(badge.color, 12), borderColor: tint(badge.color, 34) }}>
            {badge.label}
          </span>
        ) : null}
        {meta ? <span className="list-row__meta">{meta}</span> : null}
      </div>
    </div>
  );
}
