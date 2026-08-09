import { ParseResult } from "./types";

export type HygieneAlert = {
  type: "sin_descripcion" | "vlan_no_declarada" | "interfaz_apagada_configurada";
  message: string;
  interfaceName?: string;
};

/** 23-P4: resumen ejecutivo en lenguaje natural de una configuración parseada. */
export function summarizeConfig(result: ParseResult): string {
  const parts: string[] = [];
  const activeInterfaces = result.interfaces.filter((i) => i.adminStatus === "up");
  const trunks = result.interfaces.filter((i) => i.mode === "trunk");
  const accessPorts = result.interfaces.filter((i) => i.mode === "access");
  const managementWithoutIp = result.interfaces.filter(
    (i) => !i.ipAddress && i.mode !== "trunk" && i.mode !== "access" && i.name.toLowerCase().includes("vlan"),
  );

  parts.push(`${result.interfaces.length} interfaz${result.interfaces.length === 1 ? "" : "es"} configurada${result.interfaces.length === 1 ? "" : "s"} (${activeInterfaces.length} activa${activeInterfaces.length === 1 ? "" : "s"})`);
  parts.push(`${result.vlans.length} VLAN${result.vlans.length === 1 ? "" : "s"} declarada${result.vlans.length === 1 ? "" : "s"}`);
  if (trunks.length) parts.push(`${trunks.length} puerto${trunks.length === 1 ? "" : "s"} troncal${trunks.length === 1 ? "" : "es"}`);
  if (accessPorts.length) parts.push(`${accessPorts.length} puerto${accessPorts.length === 1 ? "" : "s"} de acceso`);
  if (result.staticRoutes.length) parts.push(`${result.staticRoutes.length} ruta${result.staticRoutes.length === 1 ? "" : "s"} estática${result.staticRoutes.length === 1 ? "" : "s"}`);
  if (managementWithoutIp.length) parts.push(`${managementWithoutIp.length} interfaz de gestión sin IP asignada`);

  return parts.join(", ") + ".";
}

/** 23-P4: detecta problemas de higiene sobre lo que el parser extrajo. */
export function hygieneAlerts(result: ParseResult): HygieneAlert[] {
  const alerts: HygieneAlert[] = [];

  for (const iface of result.interfaces) {
    if (!iface.description || !iface.description.trim()) {
      alerts.push({
        type: "sin_descripcion",
        interfaceName: iface.name,
        message: `${iface.name} no tiene descripción configurada.`,
      });
    }
  }

  const declaredVlanIds = new Set(result.vlans.map((v) => v.id));
  const usedVlanIds = new Set<number>();
  for (const iface of result.interfaces) {
    if (iface.accessVlan) usedVlanIds.add(iface.accessVlan);
    if (iface.nativeVlan) usedVlanIds.add(iface.nativeVlan);
    if (iface.allowedVlans) {
      for (const token of iface.allowedVlans.split(",")) {
        const id = Number(token.trim());
        if (Number.isFinite(id) && id > 0) usedVlanIds.add(id);
      }
    }
  }
  for (const vlanId of usedVlanIds) {
    if (!declaredVlanIds.has(vlanId)) {
      alerts.push({
        type: "vlan_no_declarada",
        message: `La VLAN ${vlanId} se usa en al menos una interfaz pero no está declarada globalmente (sin \`vlan ${vlanId}\`).`,
      });
    }
  }

  for (const iface of result.interfaces) {
    const isConfigured = Boolean(iface.ipAddress || iface.accessVlan || iface.mode === "trunk");
    if (iface.adminStatus === "down" && isConfigured) {
      alerts.push({
        type: "interfaz_apagada_configurada",
        interfaceName: iface.name,
        message: `${iface.name} está apagada (\`shutdown\`) pero tiene configuración activa (IP, VLAN o modo troncal) — revisa si debería estar activa.`,
      });
    }
  }

  return alerts;
}
