"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";

import {
  createDocType,
  DocTypeItem,
  getDocTypes,
  getProjectDocs,
  getProjects,
  ProjectDocItem,
  ProjectItem,
  updateDocType,
  toggleProjectDoc,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { Modal } from "@/components/ui/modal";
import { getDocScopeLabel, getDocVisibilityLabel } from "@/lib/role-utils";

const scopeOptions = ["public", "private", "both"];

export default function ApprovalsPage() {
  const [docTypes, setDocTypes] = useState<DocTypeItem[]>([]);
  const [docs, setDocs] = useState<ProjectDocItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [error, setError] = useState("");

  const [docTypeName, setDocTypeName] = useState("");
  const [docTypeScope, setDocTypeScope] = useState("both");
  const [docTypeSaving, setDocTypeSaving] = useState(false);
  const [docTypeOpen, setDocTypeOpen] = useState(false);

  const [docProjectFilter, setDocProjectFilter] = useState("");

  const queryClient = useQueryClient();
  const { data, isLoading, error: queryError } = useQuery({
    queryKey: ["approvals"],
    queryFn: async () => {
      const [docTypesData, docsData, projectsData] = await Promise.all([
        getDocTypes(),
        getProjectDocs(),
        getProjects(),
      ]);
      return { docTypesData, docsData, projectsData };
    },
  });

  useEffect(() => {
    if (!data) return;
    setDocTypes(data.docTypesData);
    setDocs(data.docsData);
    setProjects(data.projectsData);
  }, [data]);

  useEffect(() => {
    if (queryError) {
      setError(queryError instanceof Error ? queryError.message : "No se pudo cargar aprobaciones");
    }
  }, [queryError]);

  const filteredDocs = useMemo(() => {
    if (!docProjectFilter) return docs;
    return docs.filter((doc) => doc.project_id === Number(docProjectFilter));
  }, [docs, docProjectFilter]);

  const projectMap = useMemo(() => {
    const map = new Map<number, string>();
    projects.forEach((project) => map.set(project.id, project.name));
    return map;
  }, [projects]);

  async function handleDocTypeSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!docTypeName) {
      notifyError("Ingresa un nombre para el tipo");
      return;
    }
    setDocTypeSaving(true);
    setError("");
    try {
      const created = await createDocType({ name: docTypeName, scope: docTypeScope, is_active: true });
      setDocTypes((current) => [...current, created]);
      setDocTypeName("");
      setDocTypeScope("both");
      setDocTypeOpen(false);
      notifySuccess("Tipo creado", "El tipo de documento fue agregado.");
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo crear el tipo";
      setError(message);
      notifyError("No se pudo crear el tipo", message);
    } finally {
      setDocTypeSaving(false);
    }
  }

  async function handleToggleDocType(item: DocTypeItem) {
    try {
      const updated = await updateDocType(item.id, { is_active: !item.is_active });
      setDocTypes((current) => current.map((docType) => (docType.id === updated.id ? updated : docType)));
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar el tipo");
    }
  }

  async function handleToggleDoc(doc: ProjectDocItem) {
    try {
      const updated = await toggleProjectDoc(doc.id, !doc.enabled);
      setDocs((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar el documento");
    }
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h2>Aprobaciones y catálogos</h2>
        </div>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {isLoading ? <div className="empty-state">Cargando datos...</div> : null}

      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Skills y certificaciones</p>
            <h3>La validación se mudó a Formación</h3>
            <p className="muted-small" style={{ margin: 0 }}>
              Ahí ves el certificado adjunto, el enlace del emisor y la matriz del equipo.
            </p>
          </div>
          <Link className="button button-primary button-sm" href="/dashboard/formacion?tab=validar">
            <GraduationCap size={14} aria-hidden="true" /> Ir a validar
          </Link>
        </div>
      </article>

      <div className="split-grid">
        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Catalogo</p>
              <h3>Tipos de documentos</h3>
            </div>
            <div className="panel-actions">
              <button className="button button-primary" type="button" onClick={() => setDocTypeOpen(true)}>
                Nuevo tipo
              </button>
            </div>
          </div>
          {docTypes.length === 0 ? (
            <div className="empty-state">No hay tipos disponibles.</div>
          ) : (
            <div className="table-like">
              <div className="table-row table-head table-row-wide">
                <span>Tipo</span>
                <span>Scope</span>
                <span>Estado</span>
                <span>Acciones</span>
              </div>
              {docTypes.map((item) => (
                <div className="table-row table-row-wide" key={item.id}>
                  <span>{item.name}</span>
                  <span>{getDocScopeLabel(item.scope)}</span>
                  <span className={`badge badge-${item.is_active ? "approved" : "rejected"}`}>
                    {item.is_active ? "Activo" : "Inactivo"}
                  </span>
                  <span className="table-actions">
                    <button className="button button-ghost" type="button" onClick={() => handleToggleDocType(item)}>
                      {item.is_active ? "Desactivar" : "Activar"}
                    </button>
                  </span>
                </div>
              ))}
            </div>
          )}
          <Modal isOpen={docTypeOpen} title="Nuevo tipo de documento" onClose={() => setDocTypeOpen(false)}>
            <form className="entity-form" onSubmit={handleDocTypeSubmit}>
              <input placeholder="Nuevo tipo" value={docTypeName} onChange={(event) => setDocTypeName(event.target.value)} />
              <select value={docTypeScope} onChange={(event) => setDocTypeScope(event.target.value)}>
                {scopeOptions.map((option) => (
                  <option key={option} value={option}>
                    {getDocScopeLabel(option)}
                  </option>
                ))}
              </select>
              <button className="button button-primary" type="submit" disabled={docTypeSaving}>
                {docTypeSaving ? "Guardando..." : "Crear tipo"}
              </button>
            </form>
          </Modal>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Documentos</p>
              <h3>Control de visibilidad</h3>
            </div>
            <div className="panel-actions">
              <select value={docProjectFilter} onChange={(event) => setDocProjectFilter(event.target.value)}>
                <option value="">Todos los proyectos</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              <span className="muted-small">{filteredDocs.length} documento{filteredDocs.length !== 1 ? "s" : ""}</span>
            </div>
          </div>
          {filteredDocs.length === 0 ? (
            <div className="empty-state">No hay documentos registrados.</div>
          ) : (
            <div className="table-like">
              <div className="table-row table-head table-row-5">
                <span>Titulo</span>
                <span>Proyecto</span>
                <span>Visibilidad</span>
                <span>Estado</span>
                <span>Acciones</span>
              </div>
              {filteredDocs.map((doc) => (
                <div className="table-row table-row-5" key={doc.id}>
                  <span>{doc.title}</span>
                  <span>{projectMap.get(doc.project_id) || `#${doc.project_id}`}</span>
                  <span>{getDocVisibilityLabel(doc.visibility)}</span>
                  <span className={`badge badge-${doc.enabled ? "approved" : "rejected"}`}>
                    {doc.enabled ? "Habilitado" : "Deshabilitado"}
                  </span>
                  <span className="table-actions">
                    <button className="button button-ghost" type="button" onClick={() => handleToggleDoc(doc)}>
                      {doc.enabled ? "Deshabilitar" : "Habilitar"}
                    </button>
                  </span>
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
