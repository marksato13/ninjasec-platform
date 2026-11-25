import type { AreaCert } from "@/lib/api";

export const AREAS: { value: AreaCert; label: string }[] = [
  { value: "sec", label: "Ninja Sec" },
  { value: "dev", label: "Ninja Dev" },
  { value: "both", label: "Ambas áreas" },
];

export function areaLabel(area: AreaCert | null | undefined): string | null {
  return AREAS.find((a) => a.value === area)?.label ?? null;
}

export function fecha(valor: string | null | undefined): string {
  if (!valor) return "—";
  const d = new Date(valor);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" });
}

/** Dias que avisan de un vencimiento proximo. */
export const AVISO_DIAS = 60;

export type EstadoCert = { texto: string; tono: "ok" | "pendiente" | "rechazada" | "vencida" | "aviso" };

export function estadoCertificacion(c: {
  effective_status: string;
  days_until_expiry: number | null;
}): EstadoCert {
  if (c.effective_status === "expired") return { texto: "Vencida", tono: "vencida" };
  if (c.effective_status === "rejected") return { texto: "Rechazada", tono: "rechazada" };
  if (c.effective_status === "pending") return { texto: "En validación", tono: "pendiente" };
  if (c.days_until_expiry !== null && c.days_until_expiry <= AVISO_DIAS) {
    return { texto: `Vence en ${c.days_until_expiry} d`, tono: "aviso" };
  }
  return { texto: "Validada", tono: "ok" };
}

export const TIPOS_CERTIFICADO = ["application/pdf", "image/png", "image/jpeg", "image/webp"];
export const MAX_CERTIFICADO = 5 * 1024 * 1024;

/** Valida en el navegador lo mismo que el servidor, para avisar antes de subir. */
export function errorDeArchivo(file: File): string | null {
  if (!TIPOS_CERTIFICADO.includes(file.type)) return "Sube el certificado en PDF, PNG, JPG o WEBP.";
  if (file.size > MAX_CERTIFICADO) return "El archivo pasa de 5 MB. Exporta el PDF con menos resolución.";
  return null;
}

/** Plataforma oficial donde se prepara cada certificación. La formación se hace allí, no aquí. */
const PLATAFORMAS: { patron: RegExp; nombre: string; url: string }[] = [
  { patron: /fortinet|nse|fcp|fcss/i, nombre: "Fortinet Training Institute", url: "https://training.fortinet.com" },
  { patron: /cisco|ccna|ccnp|cyberops/i, nombre: "Cisco Networking Academy", url: "https://www.netacad.com" },
  { patron: /aws|amazon/i, nombre: "AWS Skill Builder", url: "https://skillbuilder.aws" },
  { patron: /azure|microsoft|az-|sc-/i, nombre: "Microsoft Learn", url: "https://learn.microsoft.com/training" },
  { patron: /google cloud|gcp/i, nombre: "Google Cloud Skills Boost", url: "https://www.cloudskillsboost.google" },
  { patron: /pfsense|netgate/i, nombre: "Netgate Training", url: "https://www.netgate.com/training" },
  { patron: /mikrotik|mtcna/i, nombre: "MikroTik Training", url: "https://mikrotik.com/training" },
  { patron: /comptia|security\+|network\+/i, nombre: "CompTIA", url: "https://www.comptia.org/training" },
  { patron: /iso|27001|27002/i, nombre: "PECB / ISO", url: "https://pecb.com/en/education-and-certification-for-individuals/iso-iec-27001" },
];

export function plataformaDe(...textos: (string | null | undefined)[]): { nombre: string; url: string } | null {
  const texto = textos.filter(Boolean).join(" ");
  return PLATAFORMAS.find((p) => p.patron.test(texto)) ?? null;
}
