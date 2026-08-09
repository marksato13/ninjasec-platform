import { ParsedInterface, ParsedStaticRoute, ParsedVlan, ParseResult } from "./types";

const INTERFACE_RE = /^interface\s+(\S+)\s*$/;
const VLAN_RE = /^vlan\s+(\d+)\s*$/;
const IP_ROUTE_RE = /^ip\s+route\s+(\S+)\s+(\S+)\s+(\S+)/;

function newInterface(name: string): ParsedInterface {
  return { name, adminStatus: "up" };
}

// Interpreta una sub-línea de un bloque "interface X" ya sin la
// indentación. Devuelve false si no reconoce el comando -- el llamador
// la manda a `warnings`.
function applyInterfaceLine(iface: ParsedInterface, line: string): boolean {
  let m: RegExpMatchArray | null;

  if (line === "shutdown") {
    iface.adminStatus = "down";
    return true;
  }
  if (line === "no shutdown") {
    iface.adminStatus = "up";
    return true;
  }
  if ((m = line.match(/^description\s+(.+)$/))) {
    iface.description = m[1].trim();
    return true;
  }
  if ((m = line.match(/^ip address\s+(\S+)\s+(\S+)/))) {
    iface.ipAddress = m[1];
    iface.subnetMask = m[2];
    iface.mode = iface.mode ?? "routed";
    return true;
  }
  if (line === "no ip address") {
    return true;
  }
  if ((m = line.match(/^switchport mode (trunk|access)$/))) {
    iface.mode = m[1] as "trunk" | "access";
    return true;
  }
  if ((m = line.match(/^switchport trunk allowed vlan\s+(?:add\s+)?(.+)$/))) {
    iface.allowedVlans = iface.allowedVlans ? `${iface.allowedVlans},${m[1].trim()}` : m[1].trim();
    return true;
  }
  if ((m = line.match(/^switchport trunk native vlan\s+(\d+)$/))) {
    iface.nativeVlan = Number(m[1]);
    return true;
  }
  if ((m = line.match(/^switchport access vlan\s+(\d+)$/))) {
    iface.accessVlan = Number(m[1]);
    iface.mode = iface.mode ?? "access";
    return true;
  }
  return false;
}

/**
 * Parsea un running-config de Cisco IOS. Reconoce interfaces (modo,
 * VLANs, IP, estado admin), VLANs top-level y rutas estáticas. Cualquier
 * sub-línea de un bloque interface/vlan que no calce con lo soportado
 * queda registrada en `warnings` con el contexto -- nunca se descarta en
 * silencio ni se inventa un valor.
 */
export function parseCiscoIOS(rawText: string): ParseResult {
  const lines = rawText.replace(/\r\n/g, "\n").split("\n");
  const interfaces: ParsedInterface[] = [];
  const vlans: ParsedVlan[] = [];
  const staticRoutes: ParsedStaticRoute[] = [];
  const warnings: string[] = [];

  let currentInterface: ParsedInterface | null = null;
  let currentVlan: ParsedVlan | null = null;

  const closeBlocks = () => {
    if (currentInterface) interfaces.push(currentInterface);
    if (currentVlan) vlans.push(currentVlan);
    currentInterface = null;
    currentVlan = null;
  };

  for (const rawLine of lines) {
    if (!rawLine.trim()) continue;
    const isIndented = /^\s/.test(rawLine);
    const line = rawLine.trim();

    if (!isIndented) {
      // Nueva línea de nivel superior: cierra cualquier bloque abierto.
      let m: RegExpMatchArray | null;
      if ((m = line.match(INTERFACE_RE))) {
        closeBlocks();
        currentInterface = newInterface(m[1]);
        continue;
      }
      if ((m = line.match(VLAN_RE))) {
        closeBlocks();
        currentVlan = { id: Number(m[1]) };
        continue;
      }
      if ((m = line.match(IP_ROUTE_RE))) {
        closeBlocks();
        staticRoutes.push({ destination: m[1], mask: m[2], nextHop: m[3] });
        continue;
      }
      // Cualquier otro comando de nivel superior (hostname, aaa, crypto,
      // ntp, banner, line con/vty, spanning-tree, snmp-server, etc.) está
      // fuera del alcance declarado de este parser -- se ignora sin
      // marcarlo como advertencia, no es sintaxis Cisco que digamos
      // soportar.
      closeBlocks();
      continue;
    }

    // Línea indentada: pertenece al bloque abierto.
    if (currentInterface) {
      if (!applyInterfaceLine(currentInterface, line)) {
        warnings.push(`interface ${currentInterface.name}: sintaxis no reconocida — "${line}"`);
      }
      continue;
    }
    if (currentVlan) {
      const m = line.match(/^name\s+(.+)$/);
      if (m) {
        currentVlan.name = m[1].trim();
      } else {
        warnings.push(`vlan ${currentVlan.id}: sintaxis no reconocida — "${line}"`);
      }
      continue;
    }
    // Indentado sin bloque abierto (banner multi-línea, ACL, etc.) --
    // fuera de alcance, se ignora.
  }
  closeBlocks();

  return { vendor: "cisco_ios", interfaces, vlans, staticRoutes, warnings };
}
