"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { CatalogDeviceFilters, CatalogDeviceItem, getCatalogDevices } from "@/lib/api";
import { QK } from "@/lib/query-keys";

const CATEGORIES = ["router", "switch", "firewall", "access_point", "modem", "server", "nas", "ups"];
const LIFECYCLE_OPTIONS = ["active", "eos", "eol"];

const LIFECYCLE_LABEL: Record<string, string> = {
  active: "Activo",
  eos: "Fin de venta",
  eol: "Fin de vida",
};

const LIFECYCLE_COLOR: Record<string, string> = {
  active: "var(--success)",
  eos: "var(--warning)",
  eol: "var(--danger)",
};

const CATEGORY_LABEL: Record<string, string> = {
  router: "Router",
  switch: "Switch",
  firewall: "Firewall",
  access_point: "Access point",
  modem: "Módem",
  server: "Servidor",
  nas: "NAS",
  ups: "UPS",
};

export default function CatalogDevicesPage() {
  const [filters, setFilters] = useState<CatalogDeviceFilters>({});
  const [search, setSearch] = useState("");

  const activeFilters: CatalogDeviceFilters = { ...filters, q: search || undefined };

  const { data: devices = [], isLoading } = useQuery<CatalogDeviceItem[]>({
    queryKey: QK.catalogDevices(activeFilters),
    queryFn: () => getCatalogDevices(activeFilters),
  });

  const brands = Array.from(new Set(devices.map((d) => d.brand))).sort();

  function updateFilter<K extends keyof CatalogDeviceFilters>(key: K, value: CatalogDeviceFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value || undefined }));
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Catálogo</p>
          <h2>Equipos de red</h2>
        </div>
        <span className="muted-small">{devices.length} modelo{devices.length !== 1 ? "s" : ""}</span>
      </div>

      <article className="panel filters-panel">
        <div className="filters-grid">
          <input
            type="text"
            placeholder="Buscar por marca, modelo o etiqueta..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={filters.category ?? ""} onChange={(e) => updateFilter("category", e.target.value)}>
            <option value="">Todas las categorías</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c] ?? c}</option>)}
          </select>
          <select value={filters.lifecycle_status ?? ""} onChange={(e) => updateFilter("lifecycle_status", e.target.value)}>
            <option value="">Cualquier ciclo de vida</option>
            {LIFECYCLE_OPTIONS.map((s) => <option key={s} value={s}>{LIFECYCLE_LABEL[s]}</option>)}
          </select>
        </div>
        <div className="filters-grid" style={{ marginTop: 12 }}>
          <select value={filters.brand ?? ""} onChange={(e) => updateFilter("brand", e.target.value)}>
            <option value="">Todas las marcas</option>
            {brands.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
          <label className="checkbox-row">
            <input type="checkbox" checked={filters.poe === true} onChange={(e) => updateFilter("poe", e.target.checked ? true : undefined)} />
            Solo con PoE
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={filters.managed === true} onChange={(e) => updateFilter("managed", e.target.checked ? true : undefined)} />
            Solo gestionables
          </label>
        </div>
      </article>

      {isLoading ? (
        <div className="empty-state">Cargando catálogo...</div>
      ) : devices.length === 0 ? (
        <div className="empty-state">Sin modelos que coincidan con los filtros.</div>
      ) : (
        <div className="card-grid">
          {devices.map((device) => (
            <Link key={device.id} href={`/dashboard/catalog-devices/${device.id}`} className="card" style={{ textDecoration: "none", borderLeft: `3px solid ${LIFECYCLE_COLOR[device.lifecycle_status] ?? "var(--line)"}` }}>
              <div className="card-header">
                <div className="card-title">
                  <strong>{device.brand} {device.model}</strong>
                  <span className="card-subtitle">{CATEGORY_LABEL[device.category] ?? device.category}</span>
                </div>
                <div className="card-badges">
                  <span className="badge" style={{ color: LIFECYCLE_COLOR[device.lifecycle_status], background: `${LIFECYCLE_COLOR[device.lifecycle_status]}1A` }}>
                    {LIFECYCLE_LABEL[device.lifecycle_status] ?? device.lifecycle_status}
                  </span>
                </div>
              </div>
              <div className="card-meta">
                {device.port_count ? <div><span className="card-label">Puertos</span><span>{device.port_count} · {device.port_speed}</span></div> : null}
                {device.poe ? <div><span className="card-label">PoE</span><span>{device.poe_budget_w ? `${device.poe_budget_w}W` : "Sí"}</span></div> : null}
                {device.price_range_usd ? <div><span className="card-label">Precio ref.</span><span>USD {device.price_range_usd}</span></div> : null}
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
