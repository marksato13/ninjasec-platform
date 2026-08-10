import { request } from "./client";

export type CatalogDeviceItem = {
  id: number;
  slug: string;
  brand: string;
  model: string;
  category: string;
  subcategory: string | null;
  osi_layer: string | null;
  segment: string | null;
  port_count: number | null;
  port_speed: string | null;
  poe: boolean;
  poe_budget_w: number | null;
  stackable: boolean;
  rack_mountable: boolean;
  managed: boolean;
  switching_capacity_gbps: number | null;
  throughput_mbps: number | null;
  power_consumption_w: number | null;
  lifecycle_status: string;
  eos_date: string | null;
  eol_date: string | null;
  price_range_usd: string | null;
  use_cases: string | null;
  tags: string | null;
  datasheet_url: string | null;
};

export type CatalogDeviceLink = {
  id: number;
  catalog_device_id: number;
  link_type: string;
  url: string;
  archive_url: string | null;
  last_checked_at: string | null;
};

export type CatalogDeviceSummary = {
  catalog_device_id: number;
  content: string;
  source_note: string | null;
  updated_by_user_id: number | null;
  updated_at: string | null;
};

export type CatalogDeviceDetail = CatalogDeviceItem & {
  links: CatalogDeviceLink[];
  summary: CatalogDeviceSummary | null;
  instance_count: number;
};

export type CatalogDeviceFilters = {
  brand?: string;
  category?: string;
  osi_layer?: string;
  segment?: string;
  lifecycle_status?: string;
  poe?: boolean;
  stackable?: boolean;
  rack_mountable?: boolean;
  managed?: boolean;
  q?: string;
};

function buildQuery(filters: CatalogDeviceFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const getCatalogDevices = (filters: CatalogDeviceFilters = {}) =>
  request<CatalogDeviceItem[]>(`/catalog/devices/${buildQuery(filters)}`);

export const getCatalogDevice = (deviceId: number) =>
  request<CatalogDeviceDetail>(`/catalog/devices/${deviceId}`);

export const addCatalogDeviceLink = (
  deviceId: number,
  payload: { link_type: string; url: string; archive_url?: string | null }
) =>
  request<CatalogDeviceLink>(`/catalog/devices/${deviceId}/links`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const deleteCatalogDeviceLink = (deviceId: number, linkId: number) =>
  request<void>(`/catalog/devices/${deviceId}/links/${linkId}`, { method: "DELETE" });

export const upsertCatalogDeviceSummary = (
  deviceId: number,
  payload: { content: string; source_note?: string | null }
) =>
  request<CatalogDeviceSummary>(`/catalog/devices/${deviceId}/summary`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
