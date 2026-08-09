import { VendorDetection } from "./types";

// El parseo ocurre siempre en el navegador: la configuración no viaja al
// servidor salvo que el usuario decida guardarla explícitamente después.
export function detectVendor(rawText: string): VendorDetection {
  const text = rawText.trim();
  if (!text) return "unsupported";

  if (/^<\?xml/.test(text) || /<pfsense>/i.test(text)) {
    return "pfsense";
  }
  if (/^\/interface\b/m.test(text) || /^\/ip\s+(address|route|firewall)\b/m.test(text)) {
    return "mikrotik";
  }
  if (
    /^interface\s+\S+/m.test(text) ||
    /^hostname\s+\S+/m.test(text) ||
    /^!\s*$/m.test(text) ||
    /^version\s+\d/m.test(text)
  ) {
    return "cisco_ios";
  }
  return "unsupported";
}
