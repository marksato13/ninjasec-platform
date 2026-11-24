"use client";

import {
  Activity,
  CheckCircle2,
  ExternalLink,
  Eye,
  EyeOff,
  Flag,
  MessageSquare,
  Network,
  Radio,
  Server,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  Avance,
  EquipoProyecto,
  FaseClave,
  VistaSeguimiento,
  cambiarFase,
  fijarEquipos,
  getSeguimiento,
  publicarAvance,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

import { SendaNinja } from "./senda-ninja";

/**
 * La vista de seguimiento de un proyecto.
 *
 * `modo = "cliente"` es lo que ve quien contrato. `modo = "equipo"` es lo mismo MAS el
 * centro de mando para alimentarla. El servidor ya decide que puede ver cada quien: esta
 * vista no filtra nada por su cuenta, solo pinta. El interruptor «ver como el cliente»
 * del equipo sirve para comprobar lo que se esta publicando antes de que lo lea nadie.
 */

const POLL_MS = 15_000;

const ESTILOS = `
.seg-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); }
.seg-vivo { width: 10px; height: 10px; border-radius: 999px; background: var(--success, #10b981); position: relative; flex: none; }
.seg-vivo::after { content: ""; position: absolute; inset: -5px; border-radius: 999px; border: 2px solid var(--success, #10b981);
  animation: seg-onda 1.8s ease-out infinite; }
@keyframes seg-onda { from { transform: scale(.5); opacity: .9; } to { transform: scale(1.6); opacity: 0; } }
.seg-entra { animation: seg-sube .5s ease-out both; }
@keyframes seg-sube { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.seg-linea { position: relative; padding-left: 26px; }
.seg-linea::before { content: ""; position: absolute; left: 8px; top: 6px; bottom: 6px; width: 2px; background: var(--line); }
.seg-nodo { position: absolute; left: 0; top: 2px; width: 18px; height: 18px; border-radius: 999px; display: grid; place-items: center;
  background: var(--panel); border: 2px solid var(--primary); color: var(--primary); }
.seg-avatar { width: 34px; height: 34px; border-radius: 999px; display: grid; place-items: center; font-weight: 700; font-size: 13px; color: #fff; flex: none; }
.seg-solo { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
@media (prefers-reduced-motion: reduce) { .seg-vivo::after, .seg-entra { animation: none; } }
`;

const COLORES = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6"];
const colorDe = (nombre: string) => COLORES[[...nombre].reduce((a, c) => a + c.charCodeAt(0), 0) % COLORES.length];
const iniciales = (n: string) => n.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("") || "?";

function hace(iso: string | null, ahora: number): string {
  if (!iso) return "sin actividad todavía";
  const s = Math.max(0, Math.round((ahora - new Date(iso + (iso.endsWith("Z") ? "" : "Z")).getTime()) / 1000));
  if (s < 60) return "hace unos segundos";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return `hace ${Math.floor(s / 86400)} d`;
}

const ICONO_EQUIPO = (tipo: string | null) => {
  const t = (tipo ?? "").toLowerCase();
  if (t.includes("fire") || t.includes("fw")) return ShieldCheck;
  if (t.includes("switch") || t.includes("router") || t.includes("ap")) return Network;
  return Server;
};

const ESTADO_EQUIPO: Record<string, { texto: string; clase: string }> = {
  online: { texto: "En línea", clase: "badge-active" },
  offline: { texto: "Sin conexión", clase: "badge-pending" },
  unknown: { texto: "Sin datos", clase: "badge-draft" },
};

function Anillo({ valor }: { valor: number }) {
  const r = 38, c = 2 * Math.PI * r;
  return (
    <svg width="96" height="96" viewBox="0 0 96 96" role="img" aria-label={`${valor}% de las tareas terminadas`}>
      <circle cx="48" cy="48" r={r} fill="none" stroke="var(--line)" strokeWidth="9" />
      <circle
        cx="48" cy="48" r={r} fill="none" stroke="var(--primary)" strokeWidth="9" strokeLinecap="round"
        strokeDasharray={`${(valor / 100) * c} ${c}`} transform="rotate(-90 48 48)"
        style={{ transition: "stroke-dasharray 1s ease-out" }}
      />
      <text x="48" y="54" textAnchor="middle" fontSize="20" fontWeight="800" fill="var(--text)">{valor}%</text>
    </svg>
  );
}

function IconoAvance({ a }: { a: Avance }) {
  if (a.kind === "phase_change") return <Flag size={11} />;
  if (a.kind === "task_done") return <CheckCircle2 size={11} />;
  if (a.kind === "milestone") return <Flag size={11} />;
  return <MessageSquare size={11} />;
}

/* ───────────────────────── centro de mando (solo equipo) ───────────────────────── */

function CentroDeMando({ vista, alCambiar }: { vista: VistaSeguimiento; alCambiar: (v: VistaSeguimiento) => void }) {
  const [fase, setFase] = useState<FaseClave>(vista.phase);
  const [nota, setNota] = useState("");
  const [titulo, setTitulo] = useState("");
  const [cuerpo, setCuerpo] = useState("");
  const [enlace, setEnlace] = useState("");
  const [hito, setHito] = useState(false);
  const [visible, setVisible] = useState(true);
  const [equipos, setEquipos] = useState<number[]>((vista.candidate_devices ?? []).filter((c) => c.linked).map((c) => c.id));

  const fallo = (t: string) => (e: unknown) => notifyError(t, e instanceof Error ? e.message : undefined);

  const mFase = useMutation({
    mutationFn: () => cambiarFase(vista.id, fase, nota),
    onSuccess: (v) => { alCambiar(v); setNota(""); notifySuccess("Fase actualizada", "El cliente ya lo ve en su recorrido."); },
    onError: fallo("No se pudo cambiar la fase"),
  });
  const mAvance = useMutation({
    mutationFn: () => publicarAvance(vista.id, {
      title: titulo, body: cuerpo || null, kind: hito ? "milestone" : "update",
      link_url: enlace || null, visible_to_client: visible,
    }),
    onSuccess: (v) => {
      alCambiar(v); setTitulo(""); setCuerpo(""); setEnlace(""); setHito(false);
      notifySuccess(visible ? "Avance publicado" : "Nota guardada", visible ? "El cliente ya lo ve." : "Solo la ve el equipo.");
    },
    onError: fallo("No se pudo publicar"),
  });
  const mEquipos = useMutation({
    mutationFn: () => fijarEquipos(vista.id, equipos),
    onSuccess: (v) => { alCambiar(v); notifySuccess("Equipos actualizados"); },
    onError: fallo("No se pudieron guardar los equipos"),
  });

  const rotulo = vista.phases.find((f) => f.key === fase)?.label ?? fase;

  return (
    <article className="panel seg-entra" aria-label="Centro de mando">
      <div className="panel-head">
        <div><p className="eyebrow">Solo el equipo</p><h3>Centro de mando</h3></div>
      </div>
      <div className="seg-grid">
        {/* Fase */}
        <section>
          <h4 style={{ margin: "0 0 6px" }}>¿Dónde está el proyecto?</h4>
          <label className="muted-small" htmlFor="seg-fase">Fase</label>
          <select id="seg-fase" value={fase} onChange={(e) => setFase(e.target.value as FaseClave)} style={{ width: "100%" }}>
            {vista.phases.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
          </select>
          <label className="muted-small" htmlFor="seg-nota" style={{ display: "block", marginTop: 8 }}>
            Mensaje para el cliente (opcional)
          </label>
          <textarea id="seg-nota" rows={2} value={nota} maxLength={1000} onChange={(e) => setNota(e.target.value)}
            placeholder="Qué cambia y qué sigue" style={{ width: "100%" }} />
          <button type="button" className="button button-primary button-sm" style={{ marginTop: 8 }}
            disabled={mFase.isPending || fase === vista.phase} onClick={() => mFase.mutate()}>
            {fase === vista.phase ? "Ya está en esta fase" : `Pasar a ${rotulo}`}
          </button>
        </section>

        {/* Avance */}
        <section>
          <h4 style={{ margin: "0 0 6px" }}>Publicar un avance</h4>
          <label className="muted-small" htmlFor="seg-titulo">Título</label>
          <input id="seg-titulo" value={titulo} maxLength={160} onChange={(e) => setTitulo(e.target.value)} style={{ width: "100%" }}
            placeholder={vista.line === "dev" ? "Primera entrega lista para probar" : "Segmentación de red terminada"} />
          <label className="muted-small" htmlFor="seg-cuerpo" style={{ display: "block", marginTop: 8 }}>Detalle</label>
          <textarea id="seg-cuerpo" rows={2} value={cuerpo} maxLength={4000} onChange={(e) => setCuerpo(e.target.value)} style={{ width: "100%" }} />
          <label className="muted-small" htmlFor="seg-enlace" style={{ display: "block", marginTop: 8 }}>
            {vista.line === "dev" ? "Enlace a la demo o al entorno de pruebas" : "Enlace (opcional)"}
          </label>
          <input id="seg-enlace" type="url" value={enlace} onChange={(e) => setEnlace(e.target.value)}
            placeholder="https://" style={{ width: "100%" }} />
          <div style={{ display: "grid", gap: 4, margin: "8px 0" }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input type="checkbox" checked={hito} onChange={(e) => setHito(e.target.checked)} /> Es un hito
            </label>
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input type="checkbox" checked={visible} onChange={(e) => setVisible(e.target.checked)} /> Visible para el cliente
            </label>
            {!visible && <span className="muted-small">Será una nota interna: solo el equipo la verá.</span>}
          </div>
          <button type="button" className="button button-primary button-sm"
            disabled={mAvance.isPending || titulo.trim().length < 3} onClick={() => mAvance.mutate()}>
            {visible ? "Publicar" : "Guardar nota interna"}
          </button>
        </section>

        {/* Equipos */}
        {vista.candidate_devices !== null && (
          <section>
            <h4 style={{ margin: "0 0 6px" }}>Equipos del proyecto</h4>
            {vista.candidate_devices.length === 0 ? (
              <p className="muted-small" style={{ margin: 0 }}>
                Este cliente no tiene equipos registrados. Se dan de alta en «Dispositivos».
              </p>
            ) : (
              <>
                <div style={{ display: "grid", gap: 4 }}>
                  {vista.candidate_devices.map((c) => (
                    <label key={c.id} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <input type="checkbox" checked={equipos.includes(c.id)}
                        onChange={(e) => setEquipos((p) => e.target.checked ? [...p, c.id] : p.filter((x) => x !== c.id))} />
                      {c.hostname} <span className="muted-small">{c.vendor ?? c.type ?? ""}</span>
                    </label>
                  ))}
                </div>
                <button type="button" className="button button-ghost button-sm" style={{ marginTop: 8 }}
                  disabled={mEquipos.isPending} onClick={() => mEquipos.mutate()}>Guardar equipos</button>
                <p className="muted-small" style={{ margin: "6px 0 0" }}>El cliente verá el equipo, nunca su IP.</p>
              </>
            )}
          </section>
        )}
      </div>
    </article>
  );
}

/* ───────────────────────────────── la vista ───────────────────────────────── */

export function SeguimientoVista({ proyectoId, modo }: { proyectoId: number; modo: "cliente" | "equipo" }) {
  const qc = useQueryClient();
  const [ahora, setAhora] = useState(() => Date.now());
  const [comoCliente, setComoCliente] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const q = useQuery({
    queryKey: QK.tracking(proyectoId),
    queryFn: () => getSeguimiento(proyectoId),
    refetchInterval: POLL_MS,
  });

  if (q.isLoading) return <div className="state-panel">Preparando el recorrido…</div>;
  if (q.error || !q.data) {
    return (
      <div className="state-panel" role="alert">
        No pudimos cargar este proyecto. Puede que ya no exista o que no tengas acceso.
      </div>
    );
  }

  const v = q.data;
  const esEquipo = modo === "equipo" && v.can_manage && !comoCliente;
  const avances = comoCliente ? v.updates.filter((a) => a.visible_to_client) : v.updates;
  const alCambiar = (nueva: VistaSeguimiento) => qc.setQueryData(QK.tracking(proyectoId), nueva);

  return (
    <section className="page-stack">
      <style>{ESTILOS}</style>

      {/* Cabecera */}
      <article className="panel seg-entra">
        <div style={{ display: "flex", gap: 20, alignItems: "center", flexWrap: "wrap", justifyContent: "space-between" }}>
          <div style={{ minWidth: 240, flex: 1 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span className="badge badge-active">{v.line === "dev" ? "Desarrollo" : "Infraestructura"}</span>
              {v.paused && <span className="badge badge-pending">En pausa</span>}
              {v.status === "completed" && <span className="badge badge-archived">Completado</span>}
            </div>
            <h2 style={{ margin: "8px 0 4px" }}>{v.name}</h2>
            {v.description && <p className="muted-small" style={{ margin: 0 }}>{v.description}</p>}
            <p className="muted-small" style={{ margin: "8px 0 0", display: "flex", gap: 8, alignItems: "center" }}>
              <span className="seg-vivo" aria-hidden />
              <Radio size={13} aria-hidden /> En vivo · última actividad {hace(v.last_activity_at, ahora)}
            </p>
          </div>
          <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
            <Anillo valor={v.progress_percent} />
            <div>
              <strong style={{ fontSize: "1.3rem" }}>{v.tasks_done}/{v.tasks_total}</strong>
              <p className="muted-small" style={{ margin: 0 }}>tareas terminadas</p>
              {(v.start_date || v.end_date) && (
                <p className="muted-small" style={{ margin: "4px 0 0" }}>
                  {v.start_date ?? "—"} → {v.end_date ?? "por definir"}
                </p>
              )}
            </div>
          </div>
        </div>

        {modo === "equipo" && v.can_manage && (
          <div style={{ marginTop: 12 }}>
            <button type="button" className="button button-ghost button-sm" aria-pressed={comoCliente}
              onClick={() => setComoCliente((x) => !x)}>
              {comoCliente ? <EyeOff size={14} /> : <Eye size={14} />}{" "}
              {comoCliente ? "Volver al centro de mando" : "Ver como lo ve el cliente"}
            </button>
          </div>
        )}
      </article>

      {/* La senda */}
      <article className="panel seg-entra" style={{ animationDelay: ".08s" }}>
        <div className="panel-head"><div><p className="eyebrow">El recorrido</p><h3>Así va tu proyecto</h3></div></div>
        <SendaNinja vista={v} />
      </article>

      {/* Ahora, siguiente, equipo, equipos */}
      <div className="seg-grid">
        <article className="panel seg-entra" style={{ animationDelay: ".14s" }}>
          <div className="panel-head"><div><p className="eyebrow">Ahora mismo</p><h3 style={{ display: "flex", gap: 8, alignItems: "center" }}><Activity size={17} aria-hidden /> En marcha</h3></div></div>
          {v.now.length === 0 ? (
            <p className="muted-small" style={{ margin: 0 }}>
              En este momento no hay una tarea abierta. {v.next_up.length ? "Lo siguiente está abajo." : "El equipo está preparando el siguiente paso."}
            </p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
              {v.now.map((n) => (
                <li key={n.task_id} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span className="seg-avatar" style={{ background: colorDe(n.person) }} aria-hidden>{iniciales(n.person)}</span>
                  <span><strong>{n.title}</strong><br /><span className="muted-small">{n.person} está trabajando en esto</span></span>
                </li>
              ))}
            </ul>
          )}
          {v.next_up.length > 0 && (
            <>
              <h4 style={{ margin: "14px 0 6px" }}>Lo que sigue</h4>
              <ol style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 4 }}>
                {v.next_up.map((t) => <li key={t}>{t}</li>)}
              </ol>
            </>
          )}
        </article>

        <article className="panel seg-entra" style={{ animationDelay: ".2s" }}>
          <div className="panel-head"><div><p className="eyebrow">Quiénes trabajan</p><h3 style={{ display: "flex", gap: 8, alignItems: "center" }}><Users size={17} aria-hidden /> Tu equipo</h3></div></div>
          {v.team.length === 0 ? (
            <p className="muted-small" style={{ margin: 0 }}>Todavía no hay personas asignadas.</p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
              {v.team.map((p) => (
                <li key={p.name} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span className="seg-avatar" style={{ background: colorDe(p.name) }} aria-hidden>{iniciales(p.name)}</span>
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <strong>{p.name}</strong>
                    <br /><span className="muted-small">{p.role ?? "Equipo"} · {p.done_tasks} hechas, {p.open_tasks} abiertas</span>
                    {p.working_now && (
                      <span className="badge badge-active" style={{ display: "inline-block", marginTop: 4 }}>Trabajando ahora</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>

        {v.devices.length > 0 && (
          <article className="panel seg-entra" style={{ animationDelay: ".26s" }}>
            <div className="panel-head"><div><p className="eyebrow">Sobre qué trabajamos</p><h3 style={{ display: "flex", gap: 8, alignItems: "center" }}><Server size={17} aria-hidden /> Equipos</h3></div></div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
              {v.devices.map((d: EquipoProyecto) => {
                const Icono = ICONO_EQUIPO(d.type);
                const est = ESTADO_EQUIPO[d.status] ?? ESTADO_EQUIPO.unknown;
                return (
                  <li key={d.id} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                    <Icono size={20} aria-hidden style={{ color: "var(--primary)", flex: "none" }} />
                    <span style={{ flex: 1 }}><strong>{d.hostname}</strong><br />
                      <span className="muted-small">{[d.vendor, d.model, d.type].filter(Boolean).join(" · ") || "Equipo"}</span></span>
                    <span className={`badge ${est.clase}`}>{est.texto}</span>
                  </li>
                );
              })}
            </ul>
          </article>
        )}
      </div>

      {esEquipo && <CentroDeMando key={`${v.phase}-${v.candidate_devices?.length ?? 0}`} vista={v} alCambiar={alCambiar} />}

      {/* Bitácora */}
      <article className="panel seg-entra" style={{ animationDelay: ".3s" }}>
        <div className="panel-head"><div><p className="eyebrow">Bitácora</p><h3>Lo que ha pasado</h3></div></div>
        {avances.length === 0 ? (
          <p className="muted-small" style={{ margin: 0 }}>Aquí irá apareciendo cada avance de tu proyecto.</p>
        ) : (
          <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 16 }}>
            {avances.map((a, i) => (
              <li key={a.id} className="seg-linea seg-entra" style={{ animationDelay: `${Math.min(i, 8) * 0.04}s` }}>
                <span className="seg-nodo" aria-hidden><IconoAvance a={a} /></span>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "baseline" }}>
                  <strong>{a.title}</strong>
                  {a.kind === "milestone" && <span className="badge badge-active">Hito</span>}
                  {!a.visible_to_client && <span className="badge badge-pending">Interna</span>}
                </div>
                {a.body && <p style={{ margin: "4px 0 0" }}>{a.body}</p>}
                {a.link_url && (
                  <p style={{ margin: "6px 0 0" }}>
                    <a href={a.link_url} target="_blank" rel="noopener noreferrer" className="button button-secondary button-sm">
                      <ExternalLink size={13} aria-hidden /> Abrir
                    </a>
                  </p>
                )}
                <p className="muted-small" style={{ margin: "4px 0 0" }}>
                  {hace(a.created_at, ahora)}{a.author ? ` · ${a.author}` : ""}
                </p>
              </li>
            ))}
          </ol>
        )}
      </article>
    </section>
  );
}
