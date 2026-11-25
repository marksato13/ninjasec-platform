"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MessageCircleQuestion, FileText, FolderKanban, Package, Server, Ticket } from "lucide-react";

import {
  AuthUser,
  getDevices,
  getMe,
  getProjectDocs,
  getProjects,
  getSupportTickets,
  ProjectItem,
  SupportTicketItem,
} from "@/lib/api";
import { clearSession, getStoredToken, isPortalRole, isTokenExpired } from "@/lib/auth";
import { ProyectoResumen } from "@/components/portal/proyecto-resumen";
import { hace } from "@/components/portal/etiquetas";
import s from "@/components/portal/portal.module.css";

/**
 * Inicio del portal. Responde, en este orden, lo que el cliente viene a saber:
 * en que estan sus proyectos, que necesitamos de el, y donde esta lo demas.
 *
 * No muestra un «estado de seguridad»: no tenemos un dato que lo respalde, y un «OK»
 * sin base es peor que no decir nada.
 */

const CERRADOS = new Set(["closed", "resolved", "completed", "cancelled", "canceled"]);

function saludo(): string {
  const h = Number(new Date().toLocaleString("en-US", { hour: "numeric", hour12: false, timeZone: "America/Lima" }));
  if (h < 12) return "Buenos días";
  if (h < 19) return "Buenas tardes";
  return "Buenas noches";
}

function hoy(): string {
  return new Date().toLocaleDateString("es-PE", { weekday: "long", day: "numeric", month: "long", timeZone: "America/Lima" });
}

export function PortalShell() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [proyectos, setProyectos] = useState<ProjectItem[] | null>(null);
  const [tickets, setTickets] = useState<SupportTicketItem[]>([]);
  const [equipos, setEquipos] = useState<number | null>(null);
  const [documentos, setDocumentos] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      window.location.href = "/login";
      return;
    }
    if (isTokenExpired(token)) {
      clearSession();
      window.location.href = "/login?expired=1";
      return;
    }

    async function cargar() {
      try {
        const me = await getMe();
        if (!isPortalRole(me.role)) {
          window.location.href = "/dashboard";
          return;
        }
        setUser(me);

        const [proyRes, ticketsRes, equiposRes, docsRes] = await Promise.allSettled([
          getProjects(),
          getSupportTickets({}),
          getDevices({}),
          getProjectDocs(),
        ]);
        setProyectos(proyRes.status === "fulfilled" ? proyRes.value : []);
        if (ticketsRes.status === "fulfilled") setTickets(ticketsRes.value);
        if (equiposRes.status === "fulfilled") setEquipos(equiposRes.value.filter((d) => d.status === "active").length);
        if (docsRes.status === "fulfilled") setDocumentos(docsRes.value.length);
      } catch (err) {
        clearSession();
        setError(err instanceof Error ? err.message : "No se pudo cargar el portal");
      } finally {
        setLoading(false);
      }
    }

    cargar();
  }, []);

  if (loading) return <div className="state-panel">Cargando tu portal…</div>;
  if (error) return <div className="state-panel state-error">{error}</div>;

  const nombre = (user?.name || user?.full_name || "").split(" ")[0];
  const activos = (proyectos ?? []).filter((p) => !CERRADOS.has(p.status.toLowerCase()));
  const esperandoTe = tickets.filter((t) => t.status === "pending");
  const abiertos = tickets.filter((t) => !CERRADOS.has(t.status));

  return (
    <section className="page-stack">
      <header className={s.saludo}>
        <h2>{saludo()}{nombre ? `, ${nombre}` : ""}</h2>
        <p>{hoy()}</p>
      </header>

      <div className={s.columnas}>
        <section className={s.bloque} aria-labelledby="tus-proyectos">
          <div className={s.bloqueTitulo}>
            <h3 id="tus-proyectos">Tus proyectos</h3>
            {(proyectos?.length ?? 0) > activos.length ? <Link href="/portal/projects">Ver todos</Link> : null}
          </div>
          {activos.length === 0 ? (
            <div className={s.vacio}>
              <strong>No tienes proyectos en curso.</strong>
              <span>Cuando aceptes una propuesta, aquí verás en qué fase va el trabajo y qué sigue.</span>
              <Link className="button button-primary button-sm" href="/portal/services">
                Ver servicios
              </Link>
            </div>
          ) : (
            activos.map((p) => <ProyectoResumen key={p.id} proyecto={p} />)
          )}
        </section>

        <aside className={s.bloque}>
          <section className={s.bloque} aria-labelledby="pendiente">
            <div className={s.bloqueTitulo}>
              <h3 id="pendiente">Pendiente de tu lado</h3>
            </div>
            {esperandoTe.length === 0 ? (
              <p className={s.alDia}>Nada por ahora. Te avisaremos aquí cuando necesitemos una respuesta o una aprobación tuya.</p>
            ) : (
              <ul className={s.pendientes}>
                {esperandoTe.map((t) => (
                  <li key={t.id}>
                    <Link className={s.pendiente} href="/portal/tickets">
                      <MessageCircleQuestion size={18} aria-hidden="true" style={{ color: "var(--warning)", flex: "none" }} />
                      <span>
                        Responder el ticket #{t.id}: {t.title}
                        <small>Esperando tu respuesta, {hace(t.updated_at)}</small>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className={s.bloque} aria-labelledby="accesos">
            <div className={s.bloqueTitulo}>
              <h3 id="accesos">Tu cuenta</h3>
            </div>
            <div className={s.accesos}>
              <Link className={s.acceso} href="/portal/projects">
                <FolderKanban size={16} aria-hidden="true" /> Proyectos <strong>{proyectos?.length ?? "—"}</strong>
              </Link>
              <Link className={s.acceso} href="/portal/tickets">
                <Ticket size={16} aria-hidden="true" /> Tickets abiertos <strong>{abiertos.length}</strong>
              </Link>
              <Link className={s.acceso} href="/portal/documents">
                <FileText size={16} aria-hidden="true" /> Documentos <strong>{documentos ?? "—"}</strong>
              </Link>
              <Link className={s.acceso} href="/portal/inventory">
                <Server size={16} aria-hidden="true" /> Equipos <strong>{equipos ?? "—"}</strong>
              </Link>
              <Link className={s.acceso} href="/portal/services" style={{ gridColumn: "1 / -1" }}>
                <Package size={16} aria-hidden="true" /> Solicitar un servicio
              </Link>
            </div>
          </section>
        </aside>
      </div>
    </section>
  );
}
