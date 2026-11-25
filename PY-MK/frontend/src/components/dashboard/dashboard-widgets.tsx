"use client";

/**
 * Primitivas visuales del panel. Aquí no hay datos: quien las usa pasa valores
 * reales del backend. (Antes este archivo traía constantes simuladas que se pintaban como si
 * fueran reales cuando la base estaba vacía; se eliminaron.)
 */

import Link from "next/link";
import type { ReactNode } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

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
        <span className="kpi-card__icon" style={{ background: `${color ?? "var(--primary)"}1A`, color: color ?? "var(--primary)" }}>
          {icon}
        </span>
        <span className="kpi-card__label">{label}</span>
      </div>
      <div className="kpi-card__value-row">
        <strong className="kpi-card__value" style={{ color: color ?? "var(--text)" }}>{value}</strong>
        {trend ? (
          <span
            className="kpi-card__trend"
            style={{
              color: trend.direction === "up" ? "var(--success)" : "var(--danger)",
              background: trend.direction === "up" ? "rgba(52,211,153,0.10)" : "rgba(248,113,113,0.10)",
            }}
          >
            {trend.direction === "up" ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
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
};

export function SparkBar({ data, color = "var(--primary)", height = 36 }: SparkBarProps) {
  const max = Math.max(...data, 1);
  return (
    <div className="sparkbar" style={{ height }}>
      {data.map((v, i) => (
        <span
          key={i}
          className="sparkbar__bar"
          style={{
            height: `${Math.max(8, (v / max) * 100)}%`,
            background: color,
            opacity: 0.35 + 0.65 * (v / max),
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
        <span className="progress-row__count">{value}</span>
      </div>
      <div className="progress-row__track">
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
      <span className="list-row__icon" style={{ background: `${iconColor ?? "var(--primary)"}1A`, color: iconColor ?? "var(--primary)" }}>
        {icon}
      </span>
      <div className="list-row__body">
        <div className="list-row__title">{title}</div>
        {subtitle ? <div className="list-row__subtitle">{subtitle}</div> : null}
      </div>
      <div className="list-row__right">
        {badge ? (
          <span className="list-row__badge" style={{ color: badge.color, background: `${badge.color}1A`, borderColor: `${badge.color}55` }}>
            {badge.label}
          </span>
        ) : null}
        {meta ? <span className="list-row__meta">{meta}</span> : null}
      </div>
    </div>
  );
}
