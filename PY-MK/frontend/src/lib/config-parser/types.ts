export type VendorDetection = "cisco_ios" | "mikrotik" | "pfsense" | "unsupported";

export type ParsedInterface = {
  name: string;
  description?: string;
  ipAddress?: string;
  subnetMask?: string;
  mode?: "trunk" | "access" | "routed";
  accessVlan?: number;
  nativeVlan?: number;
  allowedVlans?: string;
  adminStatus: "up" | "down";
};

export type ParsedVlan = { id: number; name?: string };
export type ParsedStaticRoute = { destination: string; mask: string; nextHop: string };

export type ParseResult = {
  vendor: "cisco_ios";
  interfaces: ParsedInterface[];
  vlans: ParsedVlan[];
  staticRoutes: ParsedStaticRoute[];
  warnings: string[];
};

// Comandos que el parser reconoce explícitamente -- lo que no calza acá
// (dentro de un bloque interface/vlan que SÍ tratamos de leer) va a `warnings`.
// Fuera de esos bloques (aaa, crypto, ntp, banner, line con/vty, etc.) se
// ignora en silencio: está documentado como fuera de alcance, no es un
// error de parseo.
export const SUPPORTED_COMMANDS = [
  "interface <nombre>",
  "  description <texto>",
  "  ip address <ip> <máscara>",
  "  switchport mode trunk|access",
  "  switchport trunk allowed vlan <lista>",
  "  switchport trunk native vlan <id>",
  "  switchport access vlan <id>",
  "  shutdown / no shutdown",
  "vlan <id>",
  "  name <texto>",
  "ip route <destino> <máscara> <next-hop>",
];
