"use client";

import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CalendarClock,
  Boxes,
  BriefcaseBusiness,
  Building2,
  Code2,
  ChevronDown,
  ChevronUp,
  FileBarChart2,
  FolderKanban,
  GraduationCap,
  Layers,
  ListChecks,
  Lock,
  LogOut,
  Plug,
  ScrollText,
  Server,
  Settings,
  ShieldCheck,
  ShieldAlert,
  Stethoscope,
  Gauge,
  Target,
  Ticket,
  UserCheck,
  Users,
  X,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { clearSession, getStoredUser } from "@/lib/auth";
import { formatRoleLabel, getInitials } from "@/lib/role-utils";
import { getMisMenus, getPendingApprovalsCount } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { rutaDisponible } from "@/lib/capsulas";
import { type Linea, useModo, visibleEnModo } from "@/lib/modo";

type NavItem = {
  label: string;
  href: string;
  icon: React.ReactNode;
  adminOnly?: boolean; // si true, no visible para collaborator
  // Linea de negocio de la opcion (plan 34). Sin linea = comun a los dos modos.
  line?: Linea;
};
type NavGroup = {
  id: string;
  label: string;
  staffAllowed: boolean; // true = super_admin + admin + collaborator
  items: NavItem[];
};

const IC = (Icon: React.ElementType) => <Icon size={16} strokeWidth={1.75} />;

// Orden del flujo de la empresa (ninjasec-empresa/OPERACIONES/flujos/01-ORDEN-DEL-SERVICIO.md):
// primero entra el cliente (Comercial), luego se trabaja (Operacion), con las
// herramientas tecnicas de Ninja Sec a mano, y al final el equipo y el control.
// Las opciones de la capsula de telemetria siguen aqui: el menu del servidor las
// oculta mientras este apagada.
const navGroups: NavGroup[] = [
  {
    id: "home",
    label: "Inicio",
    staffAllowed: true,
    items: [
      { label: "Dashboard", href: "/dashboard", icon: IC(BarChart3), adminOnly: true },
    ],
  },
  {
    id: "commercial",
    label: "Comercial",
    staffAllowed: true,
    items: [
      { label: "Leads",     href: "/dashboard/leads",    icon: IC(Target),    adminOnly: true },
      { label: "Servicios", href: "/dashboard/services", icon: IC(Layers),    adminOnly: true },
      { label: "Clientes",  href: "/dashboard/clients",  icon: IC(Building2) },
    ],
  },
  {
    id: "operations",
    label: "Operación",
    staffAllowed: true,
    items: [
      { label: "Proyectos",           href: "/dashboard/projects",         icon: IC(FolderKanban) },
      { label: "Mis tareas",          href: "/dashboard/mis-tareas",       icon: IC(ListChecks) },
      { label: "Ventanas de trabajo", href: "/dashboard/work-windows",     icon: IC(CalendarClock) },
      { label: "Tickets",             href: "/dashboard/support-tickets",  icon: IC(Ticket) },
      { label: "Revisiones",          href: "/dashboard/security-reviews", icon: IC(ShieldCheck) },
    ],
  },
  {
    id: "sec-tools",
    label: "Herramientas Ninja Sec",
    staffAllowed: true,
    items: [
      { label: "Riesgos",             href: "/dashboard/risks",           icon: IC(AlertTriangle), line: "sec" },
      { label: "Vulnerabilidades",    href: "/dashboard/vulnerabilities", icon: IC(ShieldAlert), line: "sec" },
      { label: "Dispositivos",        href: "/dashboard/devices",         icon: IC(Server), line: "sec" },
      { label: "Catálogo de equipos", href: "/dashboard/catalog-devices", icon: IC(Boxes), line: "sec" },
      { label: "NetDoctor",           href: "/dashboard/netdoctor",       icon: IC(Stethoscope), line: "sec" },
      { label: "Guía SGSI",           href: "/dashboard/sgsi",            icon: IC(BookOpen), line: "sec" },
      { label: "Integraciones",       href: "/dashboard/integrations",    icon: IC(Plug), line: "sec" },
      { label: "Hardening",           href: "/dashboard/hardening",       icon: IC(Lock), line: "sec" },
      { label: "Informe SOC",         href: "/dashboard/soc-report",      icon: IC(Gauge), line: "sec" },
    ],
  },
  {
    // Ninja Dev: la guia del area. El estimador, el registro de despliegues y los
    // documentos desde plantilla llegaran aqui como modulos (plan 34).
    id: "dev-tools",
    label: "Herramientas Ninja Dev",
    staffAllowed: true,
    items: [
      { label: "Guía Ninja Dev", href: "/dashboard/ninja-dev", icon: IC(Code2), line: "dev" },
    ],
  },
  {
    // La formacion es de todo el equipo; Usuarios y Postulaciones, solo de admins.
    id: "team",
    label: "Equipo",
    staffAllowed: true,
    items: [
      { label: "Colaboradores", href: "/dashboard/collaborators", icon: IC(UserCheck) },
      { label: "Formación",     href: "/dashboard/formacion",     icon: IC(GraduationCap) },
      { label: "Usuarios",      href: "/dashboard/users",         icon: IC(Users),             adminOnly: true },
      { label: "Postulaciones", href: "/dashboard/applications",  icon: IC(BriefcaseBusiness), adminOnly: true },
    ],
  },
  {
    id: "control",
    label: "Control",
    staffAllowed: false,
    items: [
      { label: "Reportes",      href: "/dashboard/reports",   icon: IC(FileBarChart2) },
      { label: "Auditoría",     href: "/dashboard/audit",     icon: IC(ScrollText) },
      { label: "Configuración", href: "/dashboard/settings",  icon: IC(Settings) },
    ],
  },
];

type SidebarProps = {
  isOpen?: boolean;
  isCollapsed?: boolean;
  onClose?: () => void;
};

export function Sidebar({ isOpen = false, isCollapsed = false, onClose }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const user = getStoredUser();
  const role = user?.role ?? "";

  const isAdmin = role === "super_admin" || role === "admin";
  const isCollaborator = role === "collaborator";
  const isSuperAdmin = role === "super_admin";
  // El modo filtra solo para quien puede elegirlo; el resto ve su menu completo.
  const modoElegido = useModo();
  const modo = isAdmin ? modoElegido : "todo";
  const { data: pendingApprovals } = useQuery({
    queryKey: QK.pendingApprovals(),
    queryFn: getPendingApprovalsCount,
    enabled: isSuperAdmin,
  });

  // Lo que se muestra lo decide el servidor (menus editables por rol). Mientras
  // no llega, o si falla, se usa la regla que estaba escrita aqui: el menu
  // nunca se queda vacio por un fallo de red.
  const { data: misMenus } = useQuery({
    queryKey: QK.navMe(),
    queryFn: getMisMenus,
    staleTime: 60_000,
  });
  const visiblesDelServidor = misMenus?.staff ?? null;

  const visibleGroups = visiblesDelServidor
    ? navGroups
    : navGroups.filter((g) => isAdmin || (isCollaborator && g.staffAllowed));

  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() =>
    navGroups.reduce((acc, g) => { acc[g.id] = true; return acc; }, {} as Record<string, boolean>),
  );

  function toggleGroup(id: string) {
    setExpandedGroups((s) => ({ ...s, [id]: !s[id] }));
  }

  function handleLogout() {
    clearSession();
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className={`sidebar ${isOpen ? "sidebar--open" : ""} ${isCollapsed ? "sidebar--collapsed" : ""}`}>

      {/* Brand */}
      <div className="brand-block sidebar-header">
        <div className="logo-space logo-space--marca">
          <Image src="/brand/icono-cabeza.webp" alt="Ninja Tech" width={36} height={36} priority />
        </div>
        {!isCollapsed && (
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "var(--text)" }}>Ninja Tech</p>
            <span className="pill" style={{ fontSize: "0.65rem", padding: "2px 7px" }}>
              {formatRoleLabel(role)}
            </span>
          </div>
        )}
        <button
          className="sidebar-close button button-ghost button-icon"
          type="button"
          aria-label="Cerrar menu"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {visibleGroups.map((group) => {
          const isExpanded = isCollapsed ? true : expandedGroups[group.id];

          // Filtrar items: collaborator no ve los adminOnly, admin no ve Auditoria (solo super_admin)
          const items = group.items.filter((item) => {
            if (visiblesDelServidor) {
              if (!visiblesDelServidor.includes(item.href)) return false;
            } else {
              if (isCollaborator && item.adminOnly) return false;
              if (item.href === "/dashboard/audit" && !isSuperAdmin) return false;
            }
            // Pantallas de una capsula apagada: no se pintan. La pagina
            // ademas devuelve notFound(), porque esconder el menu no basta.
            if (!rutaDisponible(item.href)) return false;
            // Modo Ninja Sec / Ninja Dev: preferencia de vista, no permiso.
            if (!visibleEnModo(item.line, modo)) return false;
            return true;
          });

          if (items.length === 0) return null;

          return (
            <div className="sidebar-group" key={group.id}>
              {!isCollapsed && (
                <button
                  className="sidebar-group-header"
                  type="button"
                  onClick={() => toggleGroup(group.id)}
                  aria-expanded={isExpanded}
                >
                  <span className="sidebar-group-title">{group.label}</span>
                  <span className="sidebar-group-toggle">
                    {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </span>
                </button>
              )}
              {isExpanded && (
                <div className="sidebar-group-items">
                  {items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`nav-item ${pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href)) ? "nav-item-active" : ""}`}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <span className="nav-item-icon-wrap">{item.icon}</span>
                      {!isCollapsed && <strong>{item.label}</strong>}
                      {item.href === "/dashboard/formacion" && (pendingApprovals?.pending ?? 0) > 0 && (
                        <span className="badge badge-pending" aria-label={`${pendingApprovals?.pending} certificaciones por validar`}>
                          {pendingApprovals?.pending}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      {!isCollapsed && user && (
        <div className="sidebar-footer">
          <div
            className="profile-avatar"
            style={{
              background: `hsl(${(user.name?.charCodeAt(0) ?? 200) % 360}, 55%, 42%)`,
              flexShrink: 0,
            }}
          >
            {getInitials(user.name)}
          </div>
          <div className="sidebar-footer-info">
            <p className="sidebar-footer-name">{user.name}</p>
            <p className="sidebar-footer-role">{formatRoleLabel(role)}</p>
          </div>
          <button
            className="sidebar-footer-btn"
            type="button"
            onClick={handleLogout}
            title="Cerrar sesion"
            aria-label="Cerrar sesion"
          >
            <LogOut size={14} />
          </button>
        </div>
      )}
      {isCollapsed && (
        <div style={{ padding: "12px 10px", borderTop: "1px solid var(--line)", marginTop: "auto" }}>
          <button
            className="sidebar-footer-btn"
            style={{ width: "100%" }}
            type="button"
            onClick={handleLogout}
            title="Cerrar sesion"
          >
            <LogOut size={14} />
          </button>
        </div>
      )}
    </aside>
  );
}
