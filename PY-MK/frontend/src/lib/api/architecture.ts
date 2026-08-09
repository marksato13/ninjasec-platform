import { request } from "./client";

export type ArchitectureLayer = "motivation" | "business" | "application" | "technology" | "implementation";
export type ArchitectureElement = { id: number; model_id: number; layer: ArchitectureLayer; element_type: string; name: string; description?: string | null; source_module?: string | null; source_id?: string | null; properties_json?: Record<string, unknown> | null };
export type ArchitectureRelationship = { id: number; model_id: number; source_element_id: number; target_element_id: number; relationship_type: string; label?: string | null };
export type ArchitectureModel = { id: number; client_id: number; organization_id: number; name: string; version: string; state: string; adm_phase?: string | null; status: string; elements: ArchitectureElement[]; relationships: ArchitectureRelationship[] };

export async function getArchitectureModels(): Promise<ArchitectureModel[]> { return request("/architecture/models"); }
export async function createArchitectureModel(payload: { client_id: number; name: string; version?: string; state: string }): Promise<ArchitectureModel> { return request("/architecture/models", { method: "POST", body: JSON.stringify(payload) }); }
export async function createArchitectureElement(modelId: number, payload: Omit<ArchitectureElement, "id" | "model_id">): Promise<ArchitectureElement> { return request(`/architecture/models/${modelId}/elements`, { method: "POST", body: JSON.stringify(payload) }); }
export async function createArchitectureRelationship(modelId: number, payload: Omit<ArchitectureRelationship, "id" | "model_id">): Promise<ArchitectureRelationship> { return request(`/architecture/models/${modelId}/relationships`, { method: "POST", body: JSON.stringify(payload) }); }
