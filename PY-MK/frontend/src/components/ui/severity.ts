/**
 * Una sola escala de severidad para riesgos, vulnerabilidades y puntajes.
 * El color sale de las variables --sev-* de globals.css (siguen al tema);
 * la etiqueta siempre acompaña al color, nunca va sola.
 */
export type SeverityTone = "none" | "low" | "medium" | "high" | "critical";

export const SEVERITY_LABEL: Record<SeverityTone, string> = {
  none: "Sin dato",
  low: "Bajo",
  medium: "Medio",
  high: "Alto",
  critical: "Crítico",
};

/** Riesgo inherente = probabilidad × impacto (1–25), con los cortes de la matriz 5×5. */
export function riskTone(score: number): SeverityTone {
  if (!score) return "none";
  if (score >= 20) return "critical";
  if (score >= 12) return "high";
  if (score >= 6) return "medium";
  return "low";
}

/** Nivel 1–5 de una escala (C/I/D, probabilidad, impacto). */
export function levelTone(level: number): SeverityTone {
  if (level >= 5) return "critical";
  if (level >= 4) return "high";
  if (level >= 3) return "medium";
  if (level >= 1) return "low";
  return "none";
}

/** Severidad textual de una CVE (critical/high/medium/low/unknown). */
export function cveTone(severity: string): SeverityTone {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high" || s === "medium" || s === "low") return s;
  return "none";
}

/** Probabilidad de explotación EPSS (0–1), cortes de FIRST.org de uso común. */
export function epssTone(score: number): SeverityTone {
  if (score >= 0.5) return "critical";
  if (score >= 0.1) return "high";
  if (score >= 0.01) return "medium";
  if (score > 0) return "low";
  return "none";
}
