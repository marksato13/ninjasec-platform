import { SEVERITY_LABEL, type SeverityTone } from "./severity";

/** Insignia de severidad: color del tema + texto, nunca solo color. */
export function SeverityBadge({ tone, children }: { tone: SeverityTone; children?: React.ReactNode }) {
  return <span className={`sev-badge sev-${tone}`}>{children ?? SEVERITY_LABEL[tone]}</span>;
}
