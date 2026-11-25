import { FileBarChart2 } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/theme/theme-toggle";
import { getInitials } from "@/lib/role-utils";
import { NotificationCenter } from "./alerts-widget";
import { SelectorModo } from "./selector-modo";

type TopbarProps = {
  user: { name: string; role: string; email: string } | null;
  onMenuClick?: () => void;
};

const topbarTitles: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":                    { title: "Dashboard",             subtitle: "Indicadores y seguimiento operativo" },
  "/dashboard/ninja-dev":          { title: "Guía Ninja Dev",        subtitle: "Cómo trabaja el área de desarrollo" },
  "/dashboard/clients":            { title: "Clientes",              subtitle: "Empresas, sedes y servicios" },
  "/dashboard/integrations":       { title: "Integraciones",         subtitle: "Conectores, licencias y salud" },
  "/dashboard/devices":            { title: "Dispositivos",          subtitle: "Activos monitoreados por consola" },
  "/dashboard/security-reviews":   { title: "Revisiones",            subtitle: "Checklist, hallazgos y cierres" },
  "/dashboard/support-tickets":    { title: "Tickets",               subtitle: "SLA, asignaciones y resolución" },
  "/dashboard/reports":            { title: "Reportes",              subtitle: "Exportes y consolidados" },
  "/dashboard/leads":              { title: "Leads",                 subtitle: "Captación y seguimiento comercial" },
  "/dashboard/work-windows":       { title: "Ventanas de trabajo",   subtitle: "Cambios autorizados por el cliente" },
  "/dashboard/services":           { title: "Servicios",             subtitle: "Catálogo de servicios activos" },
  "/dashboard/projects":           { title: "Proyectos",             subtitle: "Pipeline y estado de proyectos" },
  "/dashboard/users":              { title: "Usuarios",              subtitle: "Cuentas y roles del sistema" },
  "/dashboard/collaborators":      { title: "Colaboradores",         subtitle: "Perfiles y disponibilidad" },
  "/dashboard/applications":       { title: "Postulaciones",         subtitle: "Proceso de selección" },
  "/dashboard/approvals":          { title: "Aprobaciones",          subtitle: "Skills y certificaciones pendientes" },
  "/dashboard/audit":              { title: "Auditoría",             subtitle: "Trazabilidad de acciones" },
  "/dashboard/risks":              { title: "Riesgos",               subtitle: "Activos, amenazas y tratamiento" },
  "/dashboard/vulnerabilities":    { title: "Vulnerabilidades",      subtitle: "CVE priorizadas por EPSS" },
  "/dashboard/sgsi":               { title: "Guía SGSI",             subtitle: "Documentación paso a paso" },
  "/dashboard/netdoctor":          { title: "NetDoctor",             subtitle: "Diagnóstico guiado de red" },
  "/dashboard/catalog-devices":    { title: "Catálogo de equipos",   subtitle: "Modelos, precios y ciclo de vida" },
  "/dashboard/hardening":          { title: "Hardening",             subtitle: "Evaluación de configuración" },
  "/dashboard/soc-report":         { title: "Informe SOC",           subtitle: "Resumen para el cliente" },
  "/dashboard/formacion":          { title: "Formación",             subtitle: "Rutas hacia una certificación" },
  "/dashboard/settings":           { title: "Configuración",         subtitle: "Ajustes del sistema" },
};

// La ruta mas larga que coincide gana: antes "/dashboard" atrapaba "/dashboard/risks"
// y toda pagina sin entrada propia se titulaba "Dashboard".
function resolveTitle(pathname: string) {
  if (topbarTitles[pathname]) return topbarTitles[pathname];
  const match = Object.entries(topbarTitles)
    .filter(([path]) => path !== "/dashboard" && pathname.startsWith(`${path}/`))
    .sort((a, b) => b[0].length - a[0].length)[0];
  return match?.[1] ?? { title: "Panel", subtitle: "Operación de Ninja Tech" };
}

export function Topbar({ user, onMenuClick }: TopbarProps) {
  const pathname = usePathname();
  const copy = resolveTitle(pathname);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="sidebar-toggle topbar-menu"
          type="button"
          aria-label="Colapsar menu"
          onClick={onMenuClick}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="topbar__title">
          <h2>{copy.title}</h2>
          <span className="topbar__subtitle">{copy.subtitle}</span>
        </div>
      </div>

      <div className="topbar-actions">
        {user && (user.role === "super_admin" || user.role === "admin") ? <SelectorModo /> : null}
        <NotificationCenter />
        <ThemeToggle />
        {user && (
          <div className="user-chip">
            <span
              className="profile-avatar"
              style={{ background: `hsl(${(user.name?.charCodeAt(0) ?? 200) % 360}, 50%, 40%)` }}
            >
              {getInitials(user.name || user.email)}
            </span>
            <span className="profile-label">{user.name}</span>
          </div>
        )}
        <Link className="button button-secondary" href="/dashboard/reports" style={{ gap: 6 }}>
          <FileBarChart2 size={14} />
          Reportes
        </Link>
      </div>
    </header>
  );
}
