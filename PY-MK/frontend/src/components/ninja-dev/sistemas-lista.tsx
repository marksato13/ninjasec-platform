"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AppWindow, Plus } from "lucide-react";

import {
  createClientSystem,
  getClients,
  getClientSystems,
  getProjects,
  type DashboardClient,
  type EstadoSistema,
  type ProjectItem,
  type SistemaIn,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";
import { ENTORNO, ESTADO_SISTEMA, PLAN_SOPORTE, fechaCorta, mensajeError } from "./etiquetas";
import { FormSistema } from "./form-sistema";
import s from "./ninja-dev.module.css";

type Props = {
  /** Fija la lista a un cliente (pestaña Sistemas de la ficha del cliente). */
  clientId?: number;
};

/** 35-P-01: sistemas que Ninja Dev entregó o mantiene, con sus entornos y avisos. */
export function SistemasLista({ clientId }: Props) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filtroCliente, setFiltroCliente] = useState("");
  const [filtroEstado, setFiltroEstado] = useState<EstadoSistema | "">("");
  const [altaOpen, setAltaOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const cliente = clientId ?? (filtroCliente ? Number(filtroCliente) : undefined);

  const { data, isLoading, error } = useQuery({
    queryKey: QK.clientSystems(cliente),
    queryFn: () => getClientSystems(cliente),
  });
  const { data: clients = [] } = useQuery<DashboardClient[]>({ queryKey: QK.clients(), queryFn: getClients });
  const { data: projects = [] } = useQuery<ProjectItem[]>({
    queryKey: QK.projects(),
    queryFn: getProjects,
    enabled: !!data?.can_manage,
  });

  const nombreCliente = useMemo(() => {
    const m: Record<number, string> = {};
    clients.forEach((c) => { m[c.id] = c.company_name; });
    return m;
  }, [clients]);

  const sistemas = (data?.systems ?? []).filter((x) => !filtroEstado || x.status === filtroEstado);
  const conAviso = sistemas.filter(
    (x) => x.warranty_expiring || x.environments.some((e) => e.expiring_soon),
  ).length;

  async function crear(payload: SistemaIn) {
    setSaving(true);
    try {
      const nuevo = await createClientSystem(payload);
      queryClient.invalidateQueries({ queryKey: QK.clientSystemsAll() });
      notifySuccess("Sistema registrado", "Añádele sus entornos desde la ficha.");
      setAltaOpen(false);
      router.push(`/dashboard/sistemas/${nuevo.id}`);
    } catch (err) {
      notifyError("No se pudo registrar el sistema", mensajeError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Ninja Dev</p>
          <h3>Sistemas del cliente</h3>
        </div>
        <div className={s.barra}>
          {conAviso > 0 && <span className="badge badge-pending">{conAviso} con vencimiento cercano</span>}
          {!clientId && (
            <select value={filtroCliente} onChange={(e) => setFiltroCliente(e.target.value)} aria-label="Filtrar por cliente">
              <option value="">Todos los clientes</option>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.company_name}</option>)}
            </select>
          )}
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value as EstadoSistema | "")}
            aria-label="Filtrar por estado"
          >
            <option value="">Todos los estados</option>
            {(Object.keys(ESTADO_SISTEMA) as EstadoSistema[]).map((k) => (
              <option key={k} value={k}>{ESTADO_SISTEMA[k].label}</option>
            ))}
          </select>
          {data?.can_manage && (
            <button className="button button-primary" type="button" onClick={() => setAltaOpen(true)} style={{ gap: 6 }}>
              <Plus size={14} /> Registrar sistema
            </button>
          )}
        </div>
      </div>

      {data && !data.can_manage && (
        <p className="muted-small" style={{ marginTop: 0 }}>
          Ves los sistemas de los proyectos en los que participas. Los registra y edita un administrador.
        </p>
      )}

      {isLoading ? (
        <div className="empty-state">Cargando…</div>
      ) : error ? (
        <div className="empty-state">No se pudieron cargar los sistemas: {mensajeError(error)}</div>
      ) : sistemas.length === 0 ? (
        <div className="empty-state">
          <AppWindow size={20} style={{ opacity: 0.6 }} />
          <p style={{ margin: "6px 0 0" }}>
            {data?.can_manage
              ? "Aún no hay sistemas registrados. Registra el primero cuando un proyecto Ninja Dev salga a producción."
              : "No hay sistemas en tus proyectos."}
          </p>
        </div>
      ) : (
        <div className={`table-like ${s.lista}`}>
          <div className={`table-row table-head ${s.fila} ${s.sistemas} ${s.sinClic} ${s.cabecera}`}>
            <span>Sistema</span>
            <span>Cliente</span>
            <span>Estado</span>
            <span>Entornos</span>
            <span>Garantía</span>
          </div>
          {sistemas.map((x) => {
            const avisoEntorno = x.environments.some((e) => e.expiring_soon);
            return (
              <Link key={x.id} href={`/dashboard/sistemas/${x.id}`} className={`table-row ${s.fila} ${s.sistemas}`}>
                <span>
                  <div className={s.nombre}>{x.name}</div>
                  <div className="muted-small">{x.stack || "—"} · {PLAN_SOPORTE[x.support_plan]}</div>
                </span>
                <span className={s.celda}>{x.client_name ?? nombreCliente[x.client_id] ?? `#${x.client_id}`}</span>
                <span>
                  <span className={`badge ${ESTADO_SISTEMA[x.status]?.cls ?? "badge-draft"}`}>
                    {ESTADO_SISTEMA[x.status]?.label ?? x.status}
                  </span>
                </span>
                <span className={s.etiquetas}>
                  {x.environments.length === 0 && <span className="muted-small">Sin entornos</span>}
                  {x.environments.map((e) => (
                    <span key={e.id} className={`badge ${ENTORNO[e.kind].cls}`}>{ENTORNO[e.kind].label}</span>
                  ))}
                  {avisoEntorno && <span className={s.aviso}>Dominio o certificado por vencer</span>}
                </span>
                <span className={x.warranty_expiring ? s.aviso : s.celda}>{fechaCorta(x.warranty_until)}</span>
              </Link>
            );
          })}
        </div>
      )}

      <Modal isOpen={altaOpen} title="Registrar sistema" onClose={() => setAltaOpen(false)}>
        <FormSistema clientId={clientId} clients={clients} projects={projects} saving={saving} onSubmit={crear} />
      </Modal>
    </article>
  );
}
