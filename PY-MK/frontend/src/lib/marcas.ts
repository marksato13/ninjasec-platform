/**
 * Catálogo de marcas y tecnologías que NinjaSec usa en proyectos y laboratorios.
 *
 * Generado a partir de un inventario (perfil de GitHub, entregables y cursos) y
 * mantenido a mano desde aquí. Cada logo viene de una fuente con licencia libre:
 *
 * - simple-icons@13.21.0 (CC0): SVG de una sola tinta; se pinta con `color`.
 * - devicon@2.16.0 (MIT): SVG a color, para marcas que Simple Icons retiró.
 * - lucide: normas, protocolos y servicios propios, que no tienen logo libre.
 * - pendiente-gpt: sin icono todavía; se muestran las iniciales. El prompt
 *   para generarlo está en `public/marcas/PROMPTS-GPT.md`.
 *
 * Los SVG se descargaron verificando HTTP 200, que empiezan por `<svg`, que
 * pesan más de 100 bytes y que no traen `<script` ni atributos `on*=`.
 */

export type CategoriaMarca =
  | "lenguaje"
  | "framework"
  | "base-de-datos"
  | "sistema-operativo"
  | "red"
  | "seguridad"
  | "nube"
  | "virtualizacion"
  | "monitoreo"
  | "devops"
  | "herramienta"
  | "norma"
  | "servicio";

export type FuenteMarca = "simple-icons" | "devicon" | "lucide" | "pendiente-gpt";

export type LucideMarca =
  | "Activity"
  | "BookOpen"
  | "Boxes"
  | "BrickWall"
  | "Bug"
  | "ClipboardCheck"
  | "ClipboardList"
  | "Cloud"
  | "Code2"
  | "Database"
  | "FileSearch"
  | "Gauge"
  | "GitBranch"
  | "Globe"
  | "KeyRound"
  | "Landmark"
  | "Layers"
  | "LifeBuoy"
  | "ListChecks"
  | "ListOrdered"
  | "Lock"
  | "Network"
  | "Plug"
  | "Radar"
  | "Route"
  | "Router"
  | "Scale"
  | "Shapes"
  | "Sheet"
  | "Shield"
  | "ShieldCheck"
  | "Users"
  | "Waypoints"
  | "Workflow";

export type Marca = {
  slug: string;
  nombre: string;
  categoria: CategoriaMarca;
  /** Color de marca en hex; pinta los SVG de una tinta y los iconos de lucide. */
  color: string;
  fuente: FuenteMarca;
  /** Ruta pública del SVG (simple-icons y devicon). */
  icono?: string;
  /** Nombre del icono de lucide-react. */
  lucide?: LucideMarca;
  /** "oscuro": casi negro, se aclara en temas oscuros. "claro": se oscurece en el claro. */
  tono?: "oscuro" | "claro";
  /** Logo a color con texto oscuro: va sobre una placa clara. */
  placa?: boolean;
  aliases?: string[];
};

export const CATEGORIAS_MARCA: { id: CategoriaMarca; titulo: string }[] = [
  { id: "servicio", titulo: "Servicios NinjaSec" },
  { id: "red", titulo: "Redes y equipos" },
  { id: "seguridad", titulo: "Seguridad" },
  { id: "sistema-operativo", titulo: "Sistemas operativos" },
  { id: "virtualizacion", titulo: "Virtualización y contenedores" },
  { id: "nube", titulo: "Nube" },
  { id: "monitoreo", titulo: "Monitoreo" },
  { id: "lenguaje", titulo: "Lenguajes" },
  { id: "framework", titulo: "Frameworks y librerías" },
  { id: "base-de-datos", titulo: "Bases de datos" },
  { id: "devops", titulo: "DevOps" },
  { id: "herramienta", titulo: "Herramientas" },
  { id: "norma", titulo: "Normas y marcos" },
];

export const MARCAS: Marca[] = [
  { slug: "python", nombre: "Python", categoria: "lenguaje", color: "#3776AB", fuente: "simple-icons", icono: "/marcas/python.svg" },
  { slug: "java", nombre: "Java", categoria: "lenguaje", color: "#ED8B00", fuente: "devicon", icono: "/marcas/java.svg", aliases: ["openjdk"] },
  { slug: "typescript", nombre: "TypeScript", categoria: "lenguaje", color: "#3178C6", fuente: "simple-icons", icono: "/marcas/typescript.svg", aliases: ["ts"] },
  { slug: "javascript", nombre: "JavaScript", categoria: "lenguaje", color: "#F7DF1E", fuente: "simple-icons", icono: "/marcas/javascript.svg", tono: "claro", aliases: ["js"] },
  { slug: "php", nombre: "PHP", categoria: "lenguaje", color: "#777BB4", fuente: "simple-icons", icono: "/marcas/php.svg" },
  { slug: "r", nombre: "R", categoria: "lenguaje", color: "#276DC3", fuente: "simple-icons", icono: "/marcas/r.svg", aliases: ["rstudio", "lenguaje r"] },
  { slug: "bash", nombre: "Bash", categoria: "lenguaje", color: "#4EAA25", fuente: "simple-icons", icono: "/marcas/bash.svg", aliases: ["shell", "shell scripting"] },
  { slug: "powershell", nombre: "PowerShell", categoria: "lenguaje", color: "#5391FE", fuente: "devicon", icono: "/marcas/powershell.svg" },
  { slug: "sql", nombre: "SQL", categoria: "lenguaje", color: "#336791", fuente: "lucide", lucide: "Database" },
  { slug: "spring", nombre: "Spring Boot", categoria: "framework", color: "#6DB33F", fuente: "simple-icons", icono: "/marcas/spring.svg", aliases: ["spring"] },
  { slug: "angular", nombre: "Angular", categoria: "framework", color: "#DD0031", fuente: "simple-icons", icono: "/marcas/angular.svg" },
  { slug: "flutter", nombre: "Flutter", categoria: "framework", color: "#02569B", fuente: "simple-icons", icono: "/marcas/flutter.svg" },
  { slug: "nodejs", nombre: "Node.js", categoria: "framework", color: "#5FA04E", fuente: "simple-icons", icono: "/marcas/nodejs.svg", aliases: ["node", "node js"] },
  { slug: "react", nombre: "React", categoria: "framework", color: "#61DAFB", fuente: "simple-icons", icono: "/marcas/react.svg", tono: "claro", aliases: ["reactjs"] },
  { slug: "nextjs", nombre: "Next.js", categoria: "framework", color: "#000000", fuente: "simple-icons", icono: "/marcas/nextjs.svg", tono: "oscuro", aliases: ["next", "next js"] },
  { slug: "fastapi", nombre: "FastAPI", categoria: "framework", color: "#009688", fuente: "simple-icons", icono: "/marcas/fastapi.svg" },
  { slug: "django", nombre: "Django", categoria: "framework", color: "#092E20", fuente: "simple-icons", icono: "/marcas/django.svg", tono: "oscuro" },
  { slug: "sqlalchemy", nombre: "SQLAlchemy", categoria: "framework", color: "#D71F00", fuente: "simple-icons", icono: "/marcas/sqlalchemy.svg" },
  { slug: "alembic", nombre: "Alembic", categoria: "framework", color: "#6BA81E", fuente: "lucide", lucide: "GitBranch" },
  { slug: "scikit-learn", nombre: "scikit-learn", categoria: "framework", color: "#F7931E", fuente: "simple-icons", icono: "/marcas/scikit-learn.svg", aliases: ["sklearn", "scikit learn"] },
  { slug: "jupyter", nombre: "Jupyter", categoria: "herramienta", color: "#F37626", fuente: "simple-icons", icono: "/marcas/jupyter.svg", aliases: ["jupyter notebook"] },
  { slug: "postgresql", nombre: "PostgreSQL", categoria: "base-de-datos", color: "#4169E1", fuente: "simple-icons", icono: "/marcas/postgresql.svg", aliases: ["postgres"] },
  { slug: "mysql", nombre: "MySQL", categoria: "base-de-datos", color: "#4479A1", fuente: "simple-icons", icono: "/marcas/mysql.svg" },
  { slug: "mongodb", nombre: "MongoDB", categoria: "base-de-datos", color: "#47A248", fuente: "simple-icons", icono: "/marcas/mongodb.svg", aliases: ["mongo"] },
  { slug: "redis", nombre: "Redis", categoria: "base-de-datos", color: "#FF4438", fuente: "simple-icons", icono: "/marcas/redis.svg" },
  { slug: "firebase", nombre: "Firebase", categoria: "base-de-datos", color: "#DD2C00", fuente: "simple-icons", icono: "/marcas/firebase.svg" },
  { slug: "elasticsearch", nombre: "Elasticsearch", categoria: "base-de-datos", color: "#005571", fuente: "simple-icons", icono: "/marcas/elasticsearch.svg", aliases: ["elastic", "elk"] },
  { slug: "linux", nombre: "Linux", categoria: "sistema-operativo", color: "#FCC624", fuente: "simple-icons", icono: "/marcas/linux.svg", tono: "claro", aliases: ["gnu/linux"] },
  { slug: "ubuntu", nombre: "Ubuntu", categoria: "sistema-operativo", color: "#E95420", fuente: "simple-icons", icono: "/marcas/ubuntu.svg", aliases: ["ubuntu server"] },
  { slug: "debian", nombre: "Debian", categoria: "sistema-operativo", color: "#A81D33", fuente: "simple-icons", icono: "/marcas/debian.svg" },
  { slug: "redhat", nombre: "Red Hat", categoria: "sistema-operativo", color: "#EE0000", fuente: "simple-icons", icono: "/marcas/redhat.svg", aliases: ["rhel", "red hat enterprise linux"] },
  { slug: "centos", nombre: "CentOS", categoria: "sistema-operativo", color: "#262577", fuente: "simple-icons", icono: "/marcas/centos.svg", tono: "oscuro" },
  { slug: "kali-linux", nombre: "Kali Linux", categoria: "sistema-operativo", color: "#557C94", fuente: "simple-icons", icono: "/marcas/kali-linux.svg", aliases: ["kali"] },
  { slug: "windows", nombre: "Windows", categoria: "sistema-operativo", color: "#0078D4", fuente: "devicon", icono: "/marcas/windows.svg", aliases: ["windows server"] },
  { slug: "cisco", nombre: "Cisco", categoria: "red", color: "#1BA0D7", fuente: "simple-icons", icono: "/marcas/cisco.svg", aliases: ["cisco ios", "ccna", "cisco packet tracer", "packet tracer"] },
  { slug: "fortinet", nombre: "Fortinet", categoria: "red", color: "#EE3124", fuente: "simple-icons", icono: "/marcas/fortinet.svg", aliases: ["fortigate", "fortios"] },
  { slug: "mikrotik", nombre: "MikroTik", categoria: "red", color: "#293239", fuente: "simple-icons", icono: "/marcas/mikrotik.svg", tono: "oscuro", aliases: ["routeros"] },
  { slug: "pfsense", nombre: "pfSense", categoria: "red", color: "#212121", fuente: "simple-icons", icono: "/marcas/pfsense.svg", tono: "oscuro" },
  { slug: "ubiquiti", nombre: "Ubiquiti UniFi", categoria: "red", color: "#0559C9", fuente: "simple-icons", icono: "/marcas/ubiquiti.svg", aliases: ["unifi", "ubiquiti"] },
  { slug: "openvpn", nombre: "OpenVPN", categoria: "red", color: "#EA7E20", fuente: "simple-icons", icono: "/marcas/openvpn.svg" },
  { slug: "wireguard", nombre: "WireGuard", categoria: "red", color: "#88171A", fuente: "simple-icons", icono: "/marcas/wireguard.svg", tono: "oscuro" },
  { slug: "nginx", nombre: "Nginx", categoria: "red", color: "#009639", fuente: "simple-icons", icono: "/marcas/nginx.svg" },
  { slug: "caddy", nombre: "Caddy", categoria: "red", color: "#1F88C0", fuente: "simple-icons", icono: "/marcas/caddy.svg" },
  { slug: "cloudflare", nombre: "Cloudflare", categoria: "red", color: "#F38020", fuente: "simple-icons", icono: "/marcas/cloudflare.svg" },
  { slug: "vlan", nombre: "VLAN", categoria: "red", color: "#1BA0D7", fuente: "lucide", lucide: "Network", aliases: ["vlans", "802.1q"] },
  { slug: "dns", nombre: "DNS", categoria: "red", color: "#0EA5E9", fuente: "lucide", lucide: "Globe" },
  { slug: "dhcp", nombre: "DHCP", categoria: "red", color: "#0EA5E9", fuente: "lucide", lucide: "Router" },
  { slug: "ospf", nombre: "OSPF", categoria: "red", color: "#6366F1", fuente: "lucide", lucide: "Route" },
  { slug: "bgp", nombre: "BGP", categoria: "red", color: "#6366F1", fuente: "lucide", lucide: "Waypoints" },
  { slug: "ipsec", nombre: "IPsec", categoria: "red", color: "#10B981", fuente: "lucide", lucide: "Lock", aliases: ["vpn ipsec"] },
  { slug: "nftables", nombre: "nftables", categoria: "red", color: "#F59E0B", fuente: "lucide", lucide: "BrickWall", aliases: ["iptables"] },
  { slug: "radius", nombre: "RADIUS", categoria: "seguridad", color: "#8B5CF6", fuente: "lucide", lucide: "KeyRound", aliases: ["freeradius", "802.1x"] },
  { slug: "ldap", nombre: "LDAP", categoria: "seguridad", color: "#8B5CF6", fuente: "lucide", lucide: "Users", aliases: ["active directory", "openldap"] },
  { slug: "wazuh", nombre: "Wazuh", categoria: "seguridad", color: "#3595F9", fuente: "pendiente-gpt" },
  { slug: "suricata", nombre: "Suricata", categoria: "seguridad", color: "#EF5B25", fuente: "pendiente-gpt" },
  { slug: "snort", nombre: "Snort", categoria: "seguridad", color: "#E71D36", fuente: "simple-icons", icono: "/marcas/snort.svg" },
  { slug: "wireshark", nombre: "Wireshark", categoria: "seguridad", color: "#1679A7", fuente: "simple-icons", icono: "/marcas/wireshark.svg" },
  { slug: "splunk", nombre: "Splunk", categoria: "seguridad", color: "#000000", fuente: "simple-icons", icono: "/marcas/splunk.svg", tono: "oscuro" },
  { slug: "keycloak", nombre: "Keycloak", categoria: "seguridad", color: "#4D4D4D", fuente: "simple-icons", icono: "/marcas/keycloak.svg" },
  { slug: "vault", nombre: "HashiCorp Vault", categoria: "seguridad", color: "#FFEC6E", fuente: "simple-icons", icono: "/marcas/vault.svg", tono: "claro", aliases: ["vault"] },
  { slug: "owasp", nombre: "OWASP", categoria: "norma", color: "#000000", fuente: "simple-icons", icono: "/marcas/owasp.svg", tono: "oscuro", aliases: ["owasp top 10"] },
  { slug: "nmap", nombre: "Nmap", categoria: "seguridad", color: "#4682B4", fuente: "lucide", lucide: "Radar" },
  { slug: "aws", nombre: "AWS", categoria: "nube", color: "#FF9900", fuente: "devicon", icono: "/marcas/aws.svg", placa: true, aliases: ["amazon web services", "amazon"] },
  { slug: "oracle-cloud", nombre: "Oracle Cloud", categoria: "nube", color: "#F80000", fuente: "devicon", icono: "/marcas/oracle-cloud.svg", aliases: ["oci", "oracle"] },
  { slug: "minio", nombre: "MinIO", categoria: "nube", color: "#C72E49", fuente: "simple-icons", icono: "/marcas/minio.svg" },
  { slug: "proxmox", nombre: "Proxmox", categoria: "virtualizacion", color: "#E57000", fuente: "simple-icons", icono: "/marcas/proxmox.svg", aliases: ["proxmox ve"] },
  { slug: "vmware", nombre: "VMware ESXi", categoria: "virtualizacion", color: "#607078", fuente: "simple-icons", icono: "/marcas/vmware.svg", aliases: ["vmware", "esxi", "vsphere", "vcenter"] },
  { slug: "virtualbox", nombre: "VirtualBox", categoria: "virtualizacion", color: "#2F61B4", fuente: "simple-icons", icono: "/marcas/virtualbox.svg" },
  { slug: "docker", nombre: "Docker", categoria: "virtualizacion", color: "#2496ED", fuente: "simple-icons", icono: "/marcas/docker.svg", aliases: ["docker compose"] },
  { slug: "kubernetes", nombre: "Kubernetes", categoria: "virtualizacion", color: "#326CE5", fuente: "simple-icons", icono: "/marcas/kubernetes.svg", aliases: ["k8s"] },
  { slug: "eve-ng", nombre: "EVE-NG", categoria: "virtualizacion", color: "#1E40AF", fuente: "lucide", lucide: "Boxes", aliases: ["eve ng"] },
  { slug: "gns3", nombre: "GNS3", categoria: "virtualizacion", color: "#1E40AF", fuente: "lucide", lucide: "Boxes" },
  { slug: "zabbix", nombre: "Zabbix", categoria: "monitoreo", color: "#CC2936", fuente: "pendiente-gpt" },
  { slug: "grafana", nombre: "Grafana", categoria: "monitoreo", color: "#F46800", fuente: "simple-icons", icono: "/marcas/grafana.svg" },
  { slug: "prometheus", nombre: "Prometheus", categoria: "monitoreo", color: "#E6522C", fuente: "simple-icons", icono: "/marcas/prometheus.svg" },
  { slug: "nagios", nombre: "Nagios", categoria: "monitoreo", color: "#000000", fuente: "pendiente-gpt", tono: "oscuro" },
  { slug: "glpi", nombre: "GLPI", categoria: "herramienta", color: "#2E3F5C", fuente: "lucide", lucide: "ClipboardList", tono: "oscuro" },
  { slug: "git", nombre: "Git", categoria: "devops", color: "#F05032", fuente: "simple-icons", icono: "/marcas/git.svg" },
  { slug: "github", nombre: "GitHub", categoria: "devops", color: "#181717", fuente: "simple-icons", icono: "/marcas/github.svg", tono: "oscuro", aliases: ["github actions"] },
  { slug: "ansible", nombre: "Ansible", categoria: "devops", color: "#EE0000", fuente: "simple-icons", icono: "/marcas/ansible.svg" },
  { slug: "terraform", nombre: "Terraform", categoria: "devops", color: "#844FBA", fuente: "simple-icons", icono: "/marcas/terraform.svg" },
  { slug: "postman", nombre: "Postman", categoria: "herramienta", color: "#FF6C37", fuente: "simple-icons", icono: "/marcas/postman.svg" },
  { slug: "drawio", nombre: "draw.io", categoria: "herramienta", color: "#F08705", fuente: "simple-icons", icono: "/marcas/drawio.svg", aliases: ["diagrams.net", "draw io"] },
  { slug: "excel", nombre: "Excel", categoria: "herramienta", color: "#217346", fuente: "lucide", lucide: "Sheet", aliases: ["microsoft excel"] },
  { slug: "visio", nombre: "Visio", categoria: "herramienta", color: "#3955A3", fuente: "lucide", lucide: "Shapes", aliases: ["microsoft visio"] },
  { slug: "iso-27001", nombre: "ISO/IEC 27001", categoria: "norma", color: "#0F766E", fuente: "lucide", lucide: "ShieldCheck", aliases: ["iso 27001", "iso27001", "sgsi"] },
  { slug: "iso-27002", nombre: "ISO/IEC 27002", categoria: "norma", color: "#0F766E", fuente: "lucide", lucide: "ListChecks", aliases: ["iso 27002", "iso27002"] },
  { slug: "iso-19011", nombre: "ISO 19011", categoria: "norma", color: "#0F766E", fuente: "lucide", lucide: "ClipboardCheck", aliases: ["iso 19011", "auditoria iso"] },
  { slug: "nist", nombre: "NIST CSF", categoria: "norma", color: "#1D4ED8", fuente: "lucide", lucide: "Landmark", aliases: ["nist", "nist csf"] },
  { slug: "cis-controls", nombre: "CIS Controls", categoria: "norma", color: "#1D4ED8", fuente: "lucide", lucide: "ListOrdered", aliases: ["cis", "cis benchmarks"] },
  { slug: "itil", nombre: "ITIL", categoria: "norma", color: "#7C3AED", fuente: "lucide", lucide: "LifeBuoy" },
  { slug: "cobit", nombre: "COBIT", categoria: "norma", color: "#7C3AED", fuente: "lucide", lucide: "Scale" },
  { slug: "magerit", nombre: "MAGERIT", categoria: "norma", color: "#B45309", fuente: "lucide", lucide: "Gauge", aliases: ["pilar"] },
  { slug: "togaf", nombre: "TOGAF / ArchiMate", categoria: "norma", color: "#B45309", fuente: "lucide", lucide: "Layers", aliases: ["togaf", "archimate"] },
  { slug: "svc-ciberseguridad", nombre: "Ciberseguridad", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Shield", tono: "claro" },
  { slug: "svc-auditoria", nombre: "Auditoría ISO 27002", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "FileSearch", tono: "claro", aliases: ["auditoria"] },
  { slug: "svc-redes", nombre: "Redes e infraestructura", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Network", tono: "claro", aliases: ["redes", "infraestructura"] },
  { slug: "svc-firewall", nombre: "Firewall perimetral", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "BrickWall", tono: "claro", aliases: ["firewall"] },
  { slug: "svc-monitoreo", nombre: "Monitoreo", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Activity", tono: "claro", aliases: ["monitoreo"] },
  { slug: "svc-nube", nombre: "Nube", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Cloud", tono: "claro", aliases: ["cloud", "nube"] },
  { slug: "svc-desarrollo", nombre: "Desarrollo a medida", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Code2", tono: "claro", aliases: ["desarrollo de software"] },
  { slug: "svc-apis", nombre: "APIs e integraciones", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Plug", tono: "claro", aliases: ["api", "apis"] },
  { slug: "svc-automatizacion", nombre: "Automatización", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Workflow", tono: "claro", aliases: ["automatizacion"] },
  { slug: "svc-vulnerabilidades", nombre: "Gestión de vulnerabilidades", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "Bug", tono: "claro", aliases: ["vulnerabilidades", "pentesting"] },
  { slug: "svc-documentacion", nombre: "Documentación técnica", categoria: "servicio", color: "#22D3EE", fuente: "lucide", lucide: "BookOpen", tono: "claro", aliases: ["documentacion"] },
];

/** Minúsculas, sin tildes y con los separadores reducidos a un espacio. */
export function normalizarMarca(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9.+#/]+/g, " ")
    .trim();
}

const compacto = (t: string) => t.replace(/[^a-z0-9]/g, "");

const INDICE: Map<string, Marca> = (() => {
  const m = new Map<string, Marca>();
  for (const marca of MARCAS) {
    for (const clave of [marca.slug, marca.nombre, ...(marca.aliases ?? [])]) {
      const n = normalizarMarca(clave);
      if (!m.has(n)) m.set(n, marca);
      const c = compacto(n);
      if (c && !m.has(c)) m.set(c, marca);
    }
  }
  return m;
})();

/** Claves de 3 letras o más, de la más larga a la más corta, para el prefijo. */
const PREFIJOS = [...INDICE.keys()].filter((k) => k.length >= 3).sort((a, b) => b.length - a.length);

/**
 * Busca la marca de un nombre libre («FortiGate SD-WAN», «Python 3», «ISO 27001»).
 * Primero exacto (normalizado o sin separadores); si no, por prefijo de palabra.
 */
export function marcaPorNombre(nombre: string | null | undefined): Marca | undefined {
  if (!nombre) return undefined;
  const n = normalizarMarca(nombre);
  if (!n) return undefined;
  const exacta = INDICE.get(n) ?? INDICE.get(compacto(n));
  if (exacta) return exacta;
  const clave = PREFIJOS.find((k) => n.startsWith(k + " "));
  return clave ? INDICE.get(clave) : undefined;
}
