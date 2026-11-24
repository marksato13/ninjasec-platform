"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  CambioMenu,
  ConfigMenus,
  OpcionMenu,
  Superficie,
  getConfigMenus,
  saveConfigMenus,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";

const SUPERFICIES: { id: Superficie; titulo: string; ayuda: string }[] = [
  { id: "public", titulo: "Sitio web", ayuda: "La barra que ve cualquier visitante, sin iniciar sesión." },
  { id: "staff", titulo: "Panel del equipo", ayuda: "El menú lateral de /dashboard." },
  { id: "portal", titulo: "Portal", ayuda: "El menú lateral de /portal, para clientes y colaboradores." },
];

const AUDIENCIA: Record<string, string> = {
  visitor: "Visitante",
  super_admin: "Super admin",
  admin: "Admin",
  collaborator: "Colaborador",
  client: "Cliente",
};

const clave = (s: Superficie, c: string, a: string) => `${s}|${c}|${a}`;

export default function MenusPage() {
  const user = getStoredUser();
  const esSuperAdmin = user?.role === "super_admin";
  const qc = useQueryClient();
  const [superficie, setSuperficie] = useState<Superficie>("staff");
  // Solo lo que el usuario ha tocado respecto a lo guardado: clave -> visible.
  const [cambios, setCambios] = useState<Record<string, boolean>>({});

  const { data, isLoading, error } = useQuery({
    queryKey: QK.navConfig(),
    queryFn: getConfigMenus,
    enabled: esSuperAdmin,
  });

  const guardar = useMutation({
    mutationFn: (lote: CambioMenu[]) => saveConfigMenus(lote),
    onSuccess: (nueva: ConfigMenus) => {
      qc.setQueryData(QK.navConfig(), nueva);
      // Los menus que se pintan leen de aqui: que se enteren ya.
      qc.invalidateQueries({ queryKey: QK.navMe() });
      setCambios({});
      notifySuccess("Menús guardados", "Los cambios se ven al recargar cada pantalla.");
    },
    onError: (e: unknown) =>
      notifyError("No se pudo guardar", e instanceof Error ? e.message : undefined),
  });

  const actual = data?.superficies[superficie];

  function efectivo(o: OpcionMenu, aud: string): boolean {
    const k = clave(superficie, o.clave, aud);
    return k in cambios ? cambios[k] : o.visible[aud];
  }

  function alternar(o: OpcionMenu, aud: string) {
    const k = clave(superficie, o.clave, aud);
    const nuevo = !efectivo(o, aud);
    setCambios((previo) => {
      const siguiente = { ...previo };
      // Si vuelve a lo guardado, deja de ser un cambio.
      if (nuevo === o.visible[aud]) delete siguiente[k];
      else siguiente[k] = nuevo;
      return siguiente;
    });
  }

  const lote: CambioMenu[] = useMemo(
    () =>
      Object.entries(cambios).map(([k, visible]) => {
        const [s, c, a] = k.split("|");
        return { superficie: s as Superficie, clave: c, audiencia: a, visible };
      }),
    [cambios],
  );

  // Agrupa por `grupo` conservando el orden en que vienen.
  const grupos = useMemo(() => {
    const salida: { nombre: string; opciones: OpcionMenu[] }[] = [];
    for (const o of actual?.opciones ?? []) {
      const ultimo = salida[salida.length - 1];
      if (ultimo && ultimo.nombre === o.grupo) ultimo.opciones.push(o);
      else salida.push({ nombre: o.grupo, opciones: [o] });
    }
    return salida;
  }, [actual]);

  if (!esSuperAdmin) {
    return (
      <section className="page-stack">
        <div className="state-panel">Solo el super admin puede editar los menús.</div>
      </section>
    );
  }

  const columnas = `minmax(220px, 2fr) repeat(${actual?.audiencias.length ?? 1}, minmax(90px, 1fr))`;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Configuración</p>
          <h2>Menús por rol</h2>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className="button button-ghost button-sm"
            disabled={lote.length === 0 || guardar.isPending}
            onClick={() => setCambios({})}
          >
            Descartar
          </button>
          <button
            type="button"
            className="button button-primary button-sm"
            disabled={lote.length === 0 || guardar.isPending}
            onClick={() => guardar.mutate(lote)}
          >
            {guardar.isPending ? "Guardando…" : `Guardar${lote.length ? ` (${lote.length})` : ""}`}
          </button>
        </div>
      </div>

      <article className="panel">
        <p className="muted-small" style={{ margin: 0 }}>
          Aquí decides <strong>qué se muestra</strong> a cada rol, no qué se permite. Una pantalla
          sigue protegida por el backend aunque se oculte su enlace. Por eso solo puedes marcar una
          opción para los roles que el sistema ya deja usarla: mostrar un enlace que termina en un
          error no ayuda a nadie. Lo que aparece con «—» no está disponible para ese rol.
        </p>
      </article>

      <div className="tab-list" role="tablist">
        {SUPERFICIES.map((s) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={superficie === s.id}
            className={`button button-sm ${superficie === s.id ? "button-primary" : "button-ghost"}`}
            onClick={() => setSuperficie(s.id)}
          >
            {s.titulo}
          </button>
        ))}
      </div>
      <p className="muted-small" style={{ margin: 0 }}>
        {SUPERFICIES.find((s) => s.id === superficie)?.ayuda}
      </p>

      {isLoading && <div className="state-panel">Cargando…</div>}
      {error && <div className="form-error">No se pudo cargar la configuración.</div>}

      {actual && (
        <article className="panel">
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: columnas }}>
              <span>Opción</span>
              {actual.audiencias.map((a) => (
                <span key={a} style={{ textAlign: "center" }}>{AUDIENCIA[a] ?? a}</span>
              ))}
            </div>

            {grupos.map((g) => (
              <div key={g.nombre}>
                <div
                  className="table-row"
                  style={{ gridTemplateColumns: "1fr", background: "var(--row)", fontWeight: 600 }}
                >
                  <span className="muted-small">{g.nombre}</span>
                </div>
                {g.opciones.map((o) => {
                  const apagada = o.capsula !== null && !o.capsula_encendida;
                  return (
                    <div
                      className="table-row"
                      key={o.clave}
                      style={{ gridTemplateColumns: columnas, opacity: apagada ? 0.55 : 1 }}
                    >
                      <span>
                        {o.etiqueta}{" "}
                        <code className="muted-small">{o.clave}</code>
                        {apagada && (
                          <span
                            className="badge badge-pending"
                            style={{ marginLeft: 8 }}
                            title={`La cápsula «${o.capsula}» está apagada: no se muestra a nadie.`}
                          >
                            cápsula apagada
                          </span>
                        )}
                      </span>
                      {actual.audiencias.map((a) => {
                        if (!o.permitidas.includes(a)) {
                          return (
                            <span key={a} style={{ textAlign: "center" }} className="muted-small">—</span>
                          );
                        }
                        const fija = o.obligatoria_para.includes(a);
                        return (
                          <span key={a} style={{ textAlign: "center" }}>
                            <input
                              type="checkbox"
                              checked={efectivo(o, a)}
                              disabled={fija || guardar.isPending}
                              title={fija ? "No se puede ocultar: dejaría a alguien sin forma de entrar." : undefined}
                              aria-label={`${o.etiqueta} para ${AUDIENCIA[a] ?? a}`}
                              onChange={() => alternar(o, a)}
                            />
                          </span>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </article>
      )}
    </section>
  );
}
