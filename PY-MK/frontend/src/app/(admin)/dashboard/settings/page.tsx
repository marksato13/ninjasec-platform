"use client";

import { Pencil, Plus, Power } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  AreaItem,
  DocTypeItem,
  ProjectTypeItem,
  createArea,
  createDocType,
  createProjectType,
  getAreaUsage,
  getAreas,
  getDocTypes,
  getProjectTypeUsage,
  getProjectTypes,
  updateArea,
  updateProjectType,
} from "@/lib/api";
import { confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { getDocScopeLabel } from "@/lib/role-utils";

type Tab = "project-types" | "areas" | "doc-types";
type CatalogTab = "project-types" | "areas";

const docTypeSchema = z.object({
  name:  z.string().min(2, "Mínimo 2 caracteres").max(100),
  scope: z.enum(["public", "private", "both"]),
});
type DocTypeFormValues = z.infer<typeof docTypeSchema>;

const catalogSchema = z.object({
  name: z.string().min(2, "Mínimo 2 caracteres").max(120),
});
type CatalogFormValues = z.infer<typeof catalogSchema>;

// areas y tipos de proyecto comparten forma (id, name, slug, is_active) y
// las mismas operaciones — se despachan por pestaña en vez de duplicar UI.
const CATALOG_API = {
  "areas": { create: createArea, update: updateArea, usage: getAreaUsage },
  "project-types": { create: createProjectType, update: updateProjectType, usage: getProjectTypeUsage },
} as const;

export default function DashboardSettingsPage() {
  const user         = getStoredUser();
  const isSuperAdmin = user?.role === "super_admin";
  const isAdmin      = user?.role === "admin" || isSuperAdmin;
  const queryClient  = useQueryClient();

  const [tab,        setTab]        = useState<Tab>("project-types");
  const [showCreate, setShowCreate] = useState(false);
  const [editingId,  setEditingId]  = useState<number | null>(null);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<DocTypeFormValues>({
    resolver: zodResolver(docTypeSchema),
    defaultValues: { name: "", scope: "public" },
  });

  const catalogForm = useForm<CatalogFormValues>({
    resolver: zodResolver(catalogSchema),
    defaultValues: { name: "" },
  });
  const editForm = useForm<CatalogFormValues>({
    resolver: zodResolver(catalogSchema),
    defaultValues: { name: "" },
  });

  const { data: projectTypes = [], isLoading: ptLoading } = useQuery<ProjectTypeItem[]>({
    queryKey: ["project-types"],
    queryFn:  () => getProjectTypes(),
  });

  const { data: areas = [], isLoading: arLoading } = useQuery<AreaItem[]>({
    queryKey: ["areas"],
    queryFn:  () => getAreas(),
  });

  const { data: docTypes = [], isLoading: dtLoading } = useQuery<DocTypeItem[]>({
    queryKey: ["doc-types"],
    queryFn:  () => getDocTypes(),
  });

  const createDocTypeMutation = useMutation({
    mutationFn: (v: DocTypeFormValues) => createDocType({ name: v.name, scope: v.scope }),
    onSuccess: () => {
      notifySuccess("Tipo de documento creado");
      reset();
      setShowCreate(false);
      queryClient.invalidateQueries({ queryKey: ["doc-types"] });
    },
    onError: (err) => notifyError("Error", err instanceof Error ? err.message : undefined),
  });

  const createCatalogMutation = useMutation({
    mutationFn: (v: CatalogFormValues) => CATALOG_API[tab as CatalogTab].create({ name: v.name }),
    onSuccess: () => {
      notifySuccess(tab === "areas" ? "Área creada" : "Tipo de proyecto creado");
      catalogForm.reset();
      setShowCreate(false);
      queryClient.invalidateQueries({ queryKey: [tab] });
    },
    onError: (err) => notifyError("Error", err instanceof Error ? err.message : undefined),
  });

  const renameCatalogMutation = useMutation({
    mutationFn: ({ catalogTab, id, name }: { catalogTab: CatalogTab; id: number; name: string }) =>
      CATALOG_API[catalogTab].update(id, { name }),
    onSuccess: () => {
      notifySuccess("Nombre actualizado");
      setEditingId(null);
      editForm.reset();
      queryClient.invalidateQueries({ queryKey: [tab] });
    },
    onError: (err) => notifyError("Error", err instanceof Error ? err.message : undefined),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ catalogTab, id, isActive, confirmDeactivation }: { catalogTab: CatalogTab; id: number; isActive: boolean; confirmDeactivation?: boolean }) =>
      CATALOG_API[catalogTab].update(id, { is_active: isActive, confirm_deactivation: confirmDeactivation ?? false }),
    onSuccess: (_data, variables) => {
      notifySuccess(variables.isActive ? "Registro activado" : "Registro desactivado");
      queryClient.invalidateQueries({ queryKey: [tab] });
    },
    onError: (err) => notifyError("Error", err instanceof Error ? err.message : undefined),
  });

  async function handleDeactivate(catalogTab: CatalogTab, id: number, name: string) {
    const { in_use_by: inUseBy } = await CATALOG_API[catalogTab].usage(id).catch(() => ({ in_use_by: 0 }));
    const confirmed = await confirmDelete({
      title: `¿Desactivar "${name}"?`,
      text: inUseBy > 0
        ? `${inUseBy} registro(s) lo usan actualmente. El histórico sigue siendo válido, pero dejará de estar disponible para elegir en registros nuevos.`
        : "No está en uso. Dejará de estar disponible para elegir en registros nuevos.",
      confirmText: "Sí, desactivar",
    });
    if (!confirmed) return;
    toggleActiveMutation.mutate({ catalogTab, id, isActive: false, confirmDeactivation: inUseBy > 0 });
  }

  const TAB_LABELS: Record<Tab, string> = {
    "project-types": "Tipos de proyecto",
    "areas":         "Áreas",
    "doc-types":     "Tipos de documento",
  };

  const isLoading = ptLoading || arLoading || dtLoading;

  if (!isAdmin) {
    return (
      <section className="page-stack">
        <div className="empty-state">No tienes permisos para acceder a esta sección.</div>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Sistema</p>
          <h2>Configuración</h2>
        </div>
        {isSuperAdmin && <span className="badge badge-active">Super Admin</span>}
      </div>

      <div className="tab-list">
        {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "tab-active" : ""}`}
            type="button"
            onClick={() => { setTab(t); setShowCreate(false); reset(); }}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Catálogo</p>
            <h3>{TAB_LABELS[tab]}</h3>
          </div>
          {isAdmin && (
            <button
              className="button button-primary button-sm"
              type="button"
              onClick={() => { setShowCreate((s) => !s); setEditingId(null); }}
            >
              <Plus size={14} /> Nuevo
            </button>
          )}
        </div>

        {showCreate && (tab === "areas" || tab === "project-types") && (
          <form
            className="entity-form"
            onSubmit={catalogForm.handleSubmit((v) => createCatalogMutation.mutate(v))}
            style={{ borderTop: "1px solid var(--line)", paddingTop: 14, marginBottom: 14 }}
          >
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, alignItems: "start" }}>
              <div>
                <input
                  type="text"
                  placeholder={tab === "areas" ? "Nombre del área" : "Nombre del tipo de proyecto"}
                  {...catalogForm.register("name")}
                />
                {catalogForm.formState.errors.name && (
                  <p className="form-error">{catalogForm.formState.errors.name.message}</p>
                )}
              </div>
              <button
                className="button button-success button-sm"
                type="submit"
                disabled={createCatalogMutation.isPending}
              >
                Guardar
              </button>
            </div>
          </form>
        )}

        {showCreate && tab === "doc-types" && (
          <form
            className="entity-form"
            onSubmit={handleSubmit((v) => createDocTypeMutation.mutate(v))}
            style={{ borderTop: "1px solid var(--line)", paddingTop: 14, marginBottom: 14 }}
          >
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10, alignItems: "start" }}>
              <div>
                <input type="text" placeholder="Nombre del tipo de documento" {...register("name")} />
                {errors.name && <p className="form-error">{errors.name.message}</p>}
              </div>
              <select {...register("scope")} style={{ height: 42 }}>
                <option value="public">Público</option>
                <option value="private">Privado</option>
                <option value="both">Ambos</option>
              </select>
              <button className="button button-success button-sm" type="submit" disabled={isSubmitting}>
                Guardar
              </button>
            </div>
          </form>
        )}

        {isLoading ? (
          <div className="empty-state">Cargando…</div>
        ) : (
          <div className="table-like">
            {tab === "project-types" && (
              <>
                <div className="table-row table-head" style={{ gridTemplateColumns: "1fr auto auto" }}>
                  <span>Nombre</span><span>Estado</span><span></span>
                </div>
                {projectTypes.map((item) => (
                  <CatalogRow
                    key={item.id}
                    item={item}
                    catalogTab="project-types"
                    isAdmin={isAdmin}
                    editingId={editingId}
                    setEditingId={setEditingId}
                    editForm={editForm}
                    onRename={(id, name) => renameCatalogMutation.mutate({ catalogTab: "project-types", id, name })}
                    onToggleActive={(id) =>
                      item.is_active
                        ? handleDeactivate("project-types", id, item.name)
                        : toggleActiveMutation.mutate({ catalogTab: "project-types", id, isActive: true })
                    }
                  />
                ))}
                {projectTypes.length === 0 && <div className="empty-state">Sin registros.</div>}
              </>
            )}

            {tab === "areas" && (
              <>
                <div className="table-row table-head" style={{ gridTemplateColumns: "1fr auto auto" }}>
                  <span>Área</span><span>Estado</span><span></span>
                </div>
                {areas.map((item) => (
                  <CatalogRow
                    key={item.id}
                    item={item}
                    catalogTab="areas"
                    isAdmin={isAdmin}
                    editingId={editingId}
                    setEditingId={setEditingId}
                    editForm={editForm}
                    onRename={(id, name) => renameCatalogMutation.mutate({ catalogTab: "areas", id, name })}
                    onToggleActive={(id) =>
                      item.is_active
                        ? handleDeactivate("areas", id, item.name)
                        : toggleActiveMutation.mutate({ catalogTab: "areas", id, isActive: true })
                    }
                  />
                ))}
                {areas.length === 0 && <div className="empty-state">Sin registros.</div>}
              </>
            )}

            {tab === "doc-types" && (
              <>
                <div className="table-row table-head" style={{ gridTemplateColumns: "1fr auto auto" }}>
                  <span>Nombre</span><span>Alcance</span><span>Estado</span>
                </div>
                {docTypes.map((item) => (
                  <div className="table-row" key={item.id} style={{ gridTemplateColumns: "1fr auto auto" }}>
                    <span>{item.name}</span>
                    <span className="muted-small">{getDocScopeLabel(item.scope)}</span>
                    <span className={`badge ${item.is_active ? "badge-active" : "badge-archived"}`}>
                      {item.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </div>
                ))}
                {docTypes.length === 0 && <div className="empty-state">Sin registros.</div>}
              </>
            )}
          </div>
        )}
      </article>

      {isSuperAdmin && (
        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Navegación</p><h3>Menús por rol</h3></div>
            <Link className="button button-primary button-sm" href="/dashboard/settings/menus">Editar menús</Link>
          </div>
          <p style={{ color: "var(--muted)", margin: 0, fontSize: "0.88rem" }}>
            Decide qué opciones ve cada rol en el sitio web, en el panel del equipo y en el portal.
          </p>
        </article>
      )}

      {isSuperAdmin && (
        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Seguridad</p><h3>Variables de entorno</h3></div>
          </div>
          <p style={{ color: "var(--muted)", margin: "0 0 14px", fontSize: "0.88rem" }}>
            Los parámetros críticos se configuran en el archivo{" "}
            <code style={{ background: "var(--row)", padding: "2px 6px", borderRadius: 4 }}>.env</code>{" "}
            del backend y se inyectan vía Docker Compose.
          </p>
          <div className="table-like">
            {[
              { key: "APP_ENV",     value: "production / development" },
              { key: "API_PREFIX",  value: "/api/v1" },
              { key: "PORTS",       value: "8024 backend · 3018 frontend · 5433 postgres" },
            ].map((item) => (
              <div className="table-row" key={item.key} style={{ gridTemplateColumns: "1fr 2fr" }}>
                <code style={{ fontSize: "0.82rem", color: "var(--primary)" }}>{item.key}</code>
                <span className="muted-small">{item.value}</span>
              </div>
            ))}
          </div>
        </article>
      )}
    </section>
  );
}

function CatalogRow({
  item,
  catalogTab,
  isAdmin,
  editingId,
  setEditingId,
  editForm,
  onRename,
  onToggleActive,
}: {
  item: AreaItem | ProjectTypeItem;
  catalogTab: CatalogTab;
  isAdmin: boolean;
  editingId: number | null;
  setEditingId: (id: number | null) => void;
  editForm: ReturnType<typeof useForm<CatalogFormValues>>;
  onRename: (id: number, name: string) => void;
  onToggleActive: (id: number) => void;
}) {
  const isEditing = editingId === item.id;

  if (isEditing) {
    return (
      <form
        className="table-row"
        style={{ gridTemplateColumns: "1fr auto auto", alignItems: "center" }}
        onSubmit={editForm.handleSubmit((v) => onRename(item.id, v.name))}
      >
        <div>
          <input type="text" autoFocus {...editForm.register("name")} />
          {editForm.formState.errors.name && (
            <p className="form-error">{editForm.formState.errors.name.message}</p>
          )}
        </div>
        <span className={`badge ${item.is_active ? "badge-active" : "badge-archived"}`}>
          {item.is_active ? "Activo" : "Inactivo"}
        </span>
        <div style={{ display: "flex", gap: 6 }}>
          <button className="button button-success button-sm" type="submit">Guardar</button>
          <button
            className="button button-ghost button-sm"
            type="button"
            onClick={() => setEditingId(null)}
          >
            Cancelar
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="table-row" style={{ gridTemplateColumns: "1fr auto auto", alignItems: "center" }}>
      <span>{item.name}</span>
      <span className={`badge ${item.is_active ? "badge-active" : "badge-archived"}`}>
        {item.is_active ? "Activo" : "Inactivo"}
      </span>
      {isAdmin ? (
        <div style={{ display: "flex", gap: 6 }}>
          <button
            className="button button-ghost button-sm"
            type="button"
            title="Editar nombre"
            onClick={() => { setEditingId(item.id); editForm.reset({ name: item.name }); }}
          >
            <Pencil size={14} />
          </button>
          <button
            className={`button button-sm ${item.is_active ? "button-ghost" : "button-success"}`}
            type="button"
            title={item.is_active ? "Desactivar" : "Activar"}
            onClick={() => onToggleActive(item.id)}
          >
            <Power size={14} />
          </button>
        </div>
      ) : (
        <span />
      )}
    </div>
  );
}
