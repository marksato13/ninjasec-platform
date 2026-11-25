/**
 * Portafolio público: los proyectos que Ninja Tech puede enseñar.
 *
 * ## Regla de honestidad
 *
 * Cada entrada declara `evidencia`, y la portada la muestra tal cual:
 *
 *   producto      lo construimos y está en línea (se puede ver y se prueba)
 *   laboratorio   implementado y medido en un laboratorio propio, NO en un cliente
 *   caso          entregado a un cliente real
 *   preparacion   se ofrece, pero todavía no hay nada que enseñar
 *
 * «laboratorio» y «caso» no se mezclan nunca: decir que algo del laboratorio está
 * «en producción de clientes» es justo lo que se cae con una sola pregunta.
 *
 * `publicar: false` deja la entrada escrita pero fuera de la web. Un caso de cliente
 * no se publica sin su permiso por escrito, y ese permiso no existe todavía.
 */

export type Linea = "dev" | "infra";
export type Evidencia = "producto" | "laboratorio" | "caso" | "preparacion";
export type Capa = "usuario" | "borde" | "aplicacion" | "datos" | "operacion" | "red" | "externo";

export type NodoDiagrama = {
  id: string;
  etiqueta: string;
  detalle?: string;
  capa: Capa;
  x: number;
  y: number;
};
export type AristaDiagrama = { de: string; a: string; etiqueta?: string; animada?: boolean };

export type ProyectoPublico = {
  id: string;
  linea: Linea;
  titulo: string;
  evidencia: Evidencia;
  resumen: string;
  detalle: string[];
  tecnologias: string[];
  /** Lo que se sabe que NO hace o que falta. Se muestra: es parte de la honestidad. */
  limites?: string;
  diagrama?: { titulo: string; nodos: NodoDiagrama[]; aristas: AristaDiagrama[] };
  publicar: boolean;
};

export const EVIDENCIA_ETIQUETA: Record<Evidencia, { texto: string; ayuda: string }> = {
  producto: { texto: "En línea", ayuda: "Construido por Ninja Tech y funcionando: puedes verlo." },
  laboratorio: {
    texto: "Laboratorio propio",
    ayuda: "Implementado y medido en nuestro laboratorio, no en un cliente.",
  },
  caso: { texto: "Caso de cliente", ayuda: "Entregado a un cliente real." },
  preparacion: { texto: "En preparación", ayuda: "Lo ofrecemos, pero todavía no hay trabajo propio que enseñar." },
};

export const PROYECTOS: ProyectoPublico[] = [
  // ------------------------------------------------------------------ DEV
  {
    id: "plataforma-ninjasec",
    linea: "dev",
    titulo: "Plataforma de gestión de Ninja Tech",
    evidencia: "producto",
    resumen:
      "El sistema con el que Ninja Tech gestiona clientes, proyectos y colaboradores. Es el mismo que estás usando: está en línea ahora.",
    detalle: [
      "Cuatro roles (super admin, admin, colaborador y cliente), cada uno con su propio menú, que el super admin puede editar.",
      "Aislamiento por organización: los datos de un cliente no se ven desde otro, y pedir un recurso ajeno devuelve 404.",
      "Flujo completo: interés → cliente → proyecto → equipo y tareas → entrega, y planes de estudio para el equipo.",
    ],
    tecnologias: ["FastAPI", "Next.js", "PostgreSQL", "Docker", "Caddy"],
    limites:
      "Los conectores a equipos de red todavía son simulados, por eso esa parte del producto está apagada.",
    diagrama: {
      titulo: "Arquitectura",
      nodos: [
        { id: "nav", etiqueta: "Navegador", detalle: "Visitante, cliente, equipo", capa: "usuario", x: 0, y: 120 },
        { id: "caddy", etiqueta: "Caddy", detalle: "HTTPS automático", capa: "borde", x: 230, y: 120 },
        { id: "web", etiqueta: "Next.js", detalle: "Sitio, panel y portal", capa: "aplicacion", x: 470, y: 30 },
        { id: "api", etiqueta: "FastAPI", detalle: "Reglas, roles y auditoría", capa: "aplicacion", x: 470, y: 210 },
        { id: "db", etiqueta: "PostgreSQL", detalle: "Datos por organización", capa: "datos", x: 720, y: 210 },
        { id: "resp", etiqueta: "Respaldos", detalle: "Verificados al crearse", capa: "operacion", x: 720, y: 330 },
      ],
      aristas: [
        { de: "nav", a: "caddy", etiqueta: "HTTPS" },
        { de: "caddy", a: "web" },
        { de: "caddy", a: "api", etiqueta: "/api" },
        { de: "web", a: "api", animada: true },
        { de: "api", a: "db" },
        { de: "db", a: "resp" },
      ],
    },
    publicar: true,
  },
  {
    id: "despliegue-continuo",
    linea: "dev",
    titulo: "Despliegue continuo con reversión automática",
    evidencia: "producto",
    resumen:
      "Lo que entra en la rama principal se publica solo, y si la versión nueva no arranca, la máquina vuelve sola a la anterior.",
    detalle: [
      "Cinco verificaciones obligatorias antes de aceptar un cambio: pruebas, compilación, secretos, análisis estático y dependencias.",
      "La máquina revisa la rama cada 5 minutos, reconstruye y comprueba que cada servicio esté sano.",
      "Si algo falla, restaura la versión anterior sin que nadie intervenga.",
    ],
    tecnologias: ["GitHub Actions", "Docker Compose", "systemd", "Gitleaks", "Semgrep", "Trivy"],
    limites: "Comprueba que los contenedores estén sanos, no que cada pantalla funcione a fondo.",
    diagrama: {
      titulo: "Del cambio a la web",
      nodos: [
        { id: "pr", etiqueta: "Pull Request", detalle: "Una rama por cambio", capa: "usuario", x: 0, y: 100 },
        { id: "ci", etiqueta: "Verificaciones", detalle: "5 obligatorias", capa: "operacion", x: 220, y: 100 },
        { id: "main", etiqueta: "main", detalle: "Solo entra lo verde", capa: "borde", x: 440, y: 100 },
        { id: "vm", etiqueta: "Servidor", detalle: "Mira main cada 5 min", capa: "aplicacion", x: 660, y: 100 },
        { id: "ok", etiqueta: "En línea", detalle: "Todo sano", capa: "datos", x: 900, y: 20 },
        { id: "rev", etiqueta: "Versión anterior", detalle: "Reversión automática", capa: "externo", x: 900, y: 190 },
      ],
      aristas: [
        { de: "pr", a: "ci" },
        { de: "ci", a: "main", etiqueta: "si pasa" },
        { de: "main", a: "vm", animada: true },
        { de: "vm", a: "ok", etiqueta: "sano" },
        { de: "vm", a: "rev", etiqueta: "falla" },
      ],
    },
    publicar: true,
  },
  // ---------------------------------------------------------------- INFRA
  {
    id: "lab-alta-disponibilidad",
    linea: "infra",
    titulo: "Red con alta disponibilidad y doble proveedor",
    evidencia: "laboratorio",
    resumen:
      "Una red segmentada en 15 VLANs, con dos firewalls en alta disponibilidad y dos proveedores de internet, para que una caída no pare la operación.",
    detalle: [
      "Dos firewalls pfSense en par (CARP): si uno cae, el otro toma el control.",
      "Dos proveedores de internet con conmutación automática.",
      "Segmentación por zonas: la red de visitas no llega a los servidores.",
    ],
    tecnologias: ["pfSense", "CARP", "VLAN", "Doble WAN"],
    limites:
      "Implementado y medido en nuestro laboratorio, con evidencia documentada. No está en producción de un cliente.",
    diagrama: {
      titulo: "Topología del laboratorio",
      nodos: [
        { id: "isp1", etiqueta: "Proveedor A", capa: "externo", x: 60, y: 0 },
        { id: "isp2", etiqueta: "Proveedor B", capa: "externo", x: 340, y: 0 },
        { id: "fw1", etiqueta: "Firewall 1", detalle: "Principal", capa: "borde", x: 60, y: 130 },
        { id: "fw2", etiqueta: "Firewall 2", detalle: "Respaldo (CARP)", capa: "borde", x: 340, y: 130 },
        { id: "core", etiqueta: "Switch central", detalle: "Troncales VLAN", capa: "red", x: 200, y: 260 },
        { id: "v1", etiqueta: "Servidores", capa: "datos", x: 0, y: 390 },
        { id: "v2", etiqueta: "Oficina", capa: "aplicacion", x: 200, y: 390 },
        { id: "v3", etiqueta: "Visitas (aisladas)", capa: "usuario", x: 400, y: 390 },
      ],
      aristas: [
        { de: "isp1", a: "fw1" },
        { de: "isp2", a: "fw2" },
        { de: "fw1", a: "fw2", etiqueta: "CARP", animada: true },
        { de: "fw1", a: "core" },
        { de: "fw2", a: "core" },
        { de: "core", a: "v1", etiqueta: "VLAN" },
        { de: "core", a: "v2", etiqueta: "VLAN" },
        { de: "core", a: "v3", etiqueta: "VLAN" },
      ],
    },
    publicar: true,
  },
  {
    // Entregado a un cliente real. NO se publica sin su permiso por escrito.
    id: "migracion-firewall",
    linea: "infra",
    titulo: "Migración de firewall de MikroTik a FortiGate",
    evidencia: "caso",
    resumen:
      "Migración de un firewall perimetral con portal cautivo y script de aprovisionamiento, en ventana nocturna y con vuelta atrás probada.",
    detalle: [
      "Se trabajó en ventana nocturna con la vuelta atrás probada antes de empezar.",
      "Se entregó documento de migración y diagrama.",
    ],
    tecnologias: ["FortiGate", "MikroTik", "Portal cautivo"],
    publicar: false,
  },
  {
    id: "aws",
    linea: "infra",
    titulo: "Infraestructura en AWS",
    evidencia: "preparacion",
    resumen:
      "Diseño y despliegue de infraestructura en la nube y conexión por VPN con la red de la oficina.",
    detalle: [
      "Es un servicio que ofrecemos, y estamos armando un laboratorio propio para respaldarlo con evidencia.",
      "Cuando exista, aparecerá aquí con su diagrama y sus mediciones, y no antes.",
    ],
    tecnologias: ["AWS", "VPN", "Redes privadas"],
    publicar: true,
  },
];

export const proyectosVisibles = (linea?: Linea) =>
  PROYECTOS.filter((p) => p.publicar && (!linea || p.linea === linea));
