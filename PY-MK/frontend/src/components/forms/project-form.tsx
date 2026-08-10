"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  createProject,
  createProjectTask,
  DashboardClient,
  getClients,
  getMe,
  getProducts,
  getProjectTypes,
  getServices,
  ProductItem,
  ProjectItem,
  ProjectTypeItem,
  ServiceItem,
} from "@/lib/api";
import { notifyError, notifySuccess, notifyWarning } from "@/lib/alerts";
import { projectFormSchema, type ProjectFormValues } from "@/lib/validation";
import { PROJECT_TEMPLATES, type ProjectTemplate } from "@/lib/project-templates";

type ProjectFormProps = {
  onCreated: (project: ProjectItem) => void;
};

const statusOptions = [
  { value: "planning", label: "Planificación" },
  { value: "active", label: "Activo" },
  { value: "paused", label: "Pausado" },
  { value: "completed", label: "Completado" },
];

export function ProjectForm({ onCreated }: ProjectFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: "",
      clientId: "",
      projectTypeId: "",
      serviceId: "",
      productId: "",
      description: "",
      status: "planning",
      startDate: "",
      endDate: "",
    },
  });

  const [organizationId, setOrganizationId] = useState<number | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [clients, setClients] = useState<DashboardClient[]>([]);
  const [projectTypes, setProjectTypes] = useState<ProjectTypeItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);
  const firstError = useMemo(() => Object.values(errors)[0]?.message, [errors]);

  useEffect(() => {
    Promise.all([getMe(), getClients(), getProjectTypes(), getServices(), getProducts()])
      .then(([me, clientsData, typesData, servicesData, productsData]) => {
        setOrganizationId(me.organization_id ?? null);
        setCurrentUserId(me.id);
        setClients(clientsData);
        setProjectTypes(typesData);
        setServices(servicesData.filter((item) => item.active));
        setProducts(productsData.filter((item) => item.is_active));
      })
      .catch(() => setOrganizationId(null));
  }, []);

  function applyTemplate(template: ProjectTemplate | null) {
    setSelectedTemplate(template);
    if (template) {
      setValue("name", template.name);
      setValue("description", template.description);
    }
  }

  async function onSubmit(values: ProjectFormValues) {
    if (!organizationId) {
      notifyError("No se pudo resolver la organizacion");
      return;
    }

    const parsedClientId = Number(values.clientId);
    const parsedProjectTypeId = Number(values.projectTypeId);
    const parsedServiceId = values.serviceId ? Number(values.serviceId) : null;
    const parsedProductId = values.productId ? Number(values.productId) : null;

    try {
      const created = await createProject({
        organization_id: organizationId,
        client_id: parsedClientId,
        project_type_id: parsedProjectTypeId,
        service_id: parsedServiceId,
        product_id: parsedProductId,
        name: values.name,
        description: values.description?.trim() || undefined,
        status: values.status,
        start_date: values.startDate || null,
        end_date: values.endDate || null,
      });
      onCreated(created);

      if (selectedTemplate && currentUserId) {
        const results = await Promise.allSettled(
          selectedTemplate.checklist.map((title) =>
            createProjectTask({ project_id: created.id, assigned_user_id: currentUserId, title })
          )
        );
        const failed = results.filter((r) => r.status === "rejected").length;
        if (failed > 0) {
          notifyWarning(
            "Proyecto creado con checklist incompleto",
            `${failed} de ${selectedTemplate.checklist.length} tareas de la plantilla no se pudieron crear.`
          );
        }
      }

      reset();
      setSelectedTemplate(null);
      notifySuccess("Proyecto creado", "El proyecto fue agregado al pipeline.");
    } catch (err) {
      notifyError("No se pudo crear el proyecto", err instanceof Error ? err.message : undefined);
    }
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit(onSubmit)}>
      <div>
        <p className="card-label" style={{ marginBottom: 8 }}>Plantilla (opcional)</p>
        <div className="template-picker">
          <button
            type="button"
            className={`template-picker__option ${!selectedTemplate ? "template-picker__option--active" : ""}`}
            onClick={() => applyTemplate(null)}
          >
            <strong>En blanco</strong>
            <span className="muted-small">Sin checklist inicial</span>
          </button>
          {PROJECT_TEMPLATES.map((template) => (
            <button
              type="button"
              key={template.id}
              className={`template-picker__option ${selectedTemplate?.id === template.id ? "template-picker__option--active" : ""}`}
              onClick={() => applyTemplate(template)}
            >
              <strong>{template.name}</strong>
              <span className="muted-small">{template.checklist.length} tareas iniciales</span>
            </button>
          ))}
        </div>
        {selectedTemplate ? (
          <ul className="template-picker__checklist">
            {selectedTemplate.checklist.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : null}
      </div>

      <input placeholder="Nombre" {...register("name")} required />
      <select {...register("clientId")} required>
        <option value="">Selecciona un cliente</option>
        {clients.map((client) => (
          <option key={client.id} value={client.id}>
            {client.company_name}
          </option>
        ))}
      </select>
      <select {...register("projectTypeId")} required>
        <option value="">Selecciona tipo de proyecto</option>
        {projectTypes.map((type) => (
          <option key={type.id} value={type.id}>
            {type.name}
          </option>
        ))}
      </select>
      <select {...register("serviceId")}>
        <option value="">Selecciona un servicio (opcional)</option>
        {services.map((service) => (
          <option key={service.id} value={service.id}>
            {service.title}
          </option>
        ))}
      </select>
      <select {...register("productId")}>
        <option value="">Selecciona un producto (opcional)</option>
        {products.map((product) => (
          <option key={product.id} value={product.id}>
            {product.name}
          </option>
        ))}
      </select>
      <textarea placeholder="Descripcion" {...register("description")} rows={4} />
      <select {...register("status")}>
        {statusOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <div className="table-row table-row-wide">
        <input type="date" {...register("startDate")} />
        <input type="date" {...register("endDate")} />
      </div>
      {firstError ? <p className="form-error">{firstError}</p> : null}
      <button className="button button-primary" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Guardando..." : "Crear proyecto"}
      </button>
    </form>
  );
}
