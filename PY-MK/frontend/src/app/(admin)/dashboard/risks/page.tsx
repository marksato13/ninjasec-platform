"use client";

import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  HostScore,
  RiskAsset,
  RiskCatalogItem,
  RiskItem,
  createRisk,
  createRiskAsset,
  createRiskThreat,
  createRiskVulnerability,
  getClients,
  getHostScores,
  getRiskAssets,
  getRiskHeatmap,
  getRiskThreats,
  getRiskVulnerabilities,
  getRisks,
  updateRiskFactors,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

const LEVELS = [1, 2, 3, 4, 5];
const ASSET_TYPES = ["hardware", "software", "information", "service", "people", "facility"];

function cellColor(score: number) {
  if (score >= 20) return "#fecaca";
  if (score >= 12) return "#fed7aa";
  if (score >= 6) return "#fef08a";
  return "#bbf7d0";
}

const emptyAssetForm = { client_id: 0, name: "", asset_type: "information", confidentiality: 3, integrity: 3, availability: 3 };
const emptyRiskForm = { client_id: 0, asset_id: 0, title: "", likelihood: 3, impact: 3, threat_ids: [] as number[], vulnerability_ids: [] as number[] };
const emptyCatalogForm = { code: "", name: "", category: "" };

export default function RisksPage() {
  const queryClient = useQueryClient();
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [assetForm, setAssetForm] = useState(emptyAssetForm);
  const [riskForm, setRiskForm] = useState(emptyRiskForm);
  const [threatForm, setThreatForm] = useState(emptyCatalogForm);
  const [vulnForm, setVulnForm] = useState(emptyCatalogForm);

  const activeClientId = clientFilter === "" ? undefined : clientFilter;

  const { data: clients = [] } = useQuery({ queryKey: QK.clients(), queryFn: getClients });
  const { data: assets = [] } = useQuery({ queryKey: QK.riskAssets(activeClientId), queryFn: () => getRiskAssets(activeClientId) });
  const { data: heatmap = [], isLoading: loadingHeatmap } = useQuery({ queryKey: QK.riskHeatmap(activeClientId), queryFn: () => getRiskHeatmap(activeClientId) });
  const { data: hostScores = [] } = useQuery({
    queryKey: QK.hostScores(activeClientId),
    queryFn: () => getHostScores(activeClientId as number),
    enabled: activeClientId !== undefined,
  });
  const { data: threats = [] } = useQuery({ queryKey: QK.riskThreats(), queryFn: getRiskThreats });
  const { data: vulnerabilities = [] } = useQuery({ queryKey: QK.riskVulnerabilities(), queryFn: getRiskVulnerabilities });

  const invalidateRisks = () => {
    queryClient.invalidateQueries({ queryKey: QK.riskHeatmap(activeClientId) });
    queryClient.invalidateQueries({ queryKey: QK.risks(activeClientId) });
  };

  const saveAsset = useMutation({
    mutationFn: () => createRiskAsset(assetForm),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.riskAssets(activeClientId) });
      setAssetForm(emptyAssetForm);
      notifySuccess("Activo registrado");
    },
    onError: (error) => notifyError("No se pudo registrar el activo", error instanceof Error ? error.message : undefined),
  });

  const saveRisk = useMutation({
    mutationFn: () => createRisk(riskForm),
    onSuccess: () => {
      invalidateRisks();
      setRiskForm({ ...emptyRiskForm, client_id: riskForm.client_id });
      notifySuccess("Riesgo registrado");
    },
    onError: (error) => notifyError("No se pudo registrar el riesgo", error instanceof Error ? error.message : undefined),
  });

  const moveFactors = useMutation({
    mutationFn: ({ id, likelihood, impact }: { id: number; likelihood: number; impact: number }) => updateRiskFactors(id, likelihood, impact),
    onSuccess: () => invalidateRisks(),
    onError: (error) => notifyError("No se pudo actualizar", error instanceof Error ? error.message : undefined),
  });

  const saveThreat = useMutation({
    mutationFn: () => createRiskThreat(threatForm),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: QK.riskThreats() }); setThreatForm(emptyCatalogForm); notifySuccess("Amenaza agregada al catálogo"); },
    onError: (error) => notifyError("No se pudo agregar la amenaza", error instanceof Error ? error.message : undefined),
  });

  const saveVulnerability = useMutation({
    mutationFn: () => createRiskVulnerability(vulnForm),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: QK.riskVulnerabilities() }); setVulnForm(emptyCatalogForm); notifySuccess("Vulnerabilidad agregada al catálogo"); },
    onError: (error) => notifyError("No se pudo agregar la vulnerabilidad", error instanceof Error ? error.message : undefined),
  });

  const assetsForRiskClient = useMemo(
    () => assets.filter((asset: RiskAsset) => !riskForm.client_id || asset.client_id === riskForm.client_id),
    [assets, riskForm.client_id],
  );

  const toggleCatalog = (field: "threat_ids" | "vulnerability_ids", id: number) =>
    setRiskForm((old) => ({ ...old, [field]: old[field].includes(id) ? old[field].filter((v) => v !== id) : [...old[field], id] }));

  const submitAsset = (event: FormEvent) => { event.preventDefault(); if (assetForm.client_id && assetForm.name) saveAsset.mutate(); };
  const submitRisk = (event: FormEvent) => { event.preventDefault(); if (riskForm.client_id && riskForm.asset_id && riskForm.title) saveRisk.mutate(); };
  const submitThreat = (event: FormEvent) => { event.preventDefault(); if (threatForm.code && threatForm.name && threatForm.category) saveThreat.mutate(); };
  const submitVulnerability = (event: FormEvent) => { event.preventDefault(); if (vulnForm.code && vulnForm.name && vulnForm.category) saveVulnerability.mutate(); };

  return (
    <section className="page-stack">
      <div className="flex items-center justify-between">
        <h2>Gestión de riesgos</h2>
        <select className="input w-64" value={clientFilter} onChange={(e) => setClientFilter(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Todos los clientes</option>
          {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
        </select>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="panel">
          <h3>Nuevo activo de riesgo</h3>
          <form onSubmit={submitAsset} className="grid gap-3">
            <label>Cliente
              <select className="input" required value={assetForm.client_id} onChange={(e) => setAssetForm({ ...assetForm, client_id: Number(e.target.value) })}>
                <option value={0}>Seleccionar</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
              </select>
            </label>
            <label>Nombre<input className="input" required value={assetForm.name} onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })} /></label>
            <label>Tipo
              <select className="input" value={assetForm.asset_type} onChange={(e) => setAssetForm({ ...assetForm, asset_type: e.target.value })}>
                {ASSET_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-3 gap-2">
              <label>Confid.
                <select className="input" value={assetForm.confidentiality} onChange={(e) => setAssetForm({ ...assetForm, confidentiality: Number(e.target.value) })}>
                  {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
              <label>Integr.
                <select className="input" value={assetForm.integrity} onChange={(e) => setAssetForm({ ...assetForm, integrity: Number(e.target.value) })}>
                  {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
              <label>Disp.
                <select className="input" value={assetForm.availability} onChange={(e) => setAssetForm({ ...assetForm, availability: Number(e.target.value) })}>
                  {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
            </div>
            <button className="button button-primary" disabled={saveAsset.isPending}>Registrar activo</button>
          </form>
        </div>

        <div className="panel">
          <h3>Nuevo riesgo</h3>
          <form onSubmit={submitRisk} className="grid gap-3">
            <label>Cliente
              <select className="input" required value={riskForm.client_id} onChange={(e) => setRiskForm({ ...riskForm, client_id: Number(e.target.value), asset_id: 0 })}>
                <option value={0}>Seleccionar</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
              </select>
            </label>
            <label>Activo
              <select className="input" required value={riskForm.asset_id} onChange={(e) => setRiskForm({ ...riskForm, asset_id: Number(e.target.value) })}>
                <option value={0}>Seleccionar</option>
                {assetsForRiskClient.map((asset: RiskAsset) => <option key={asset.id} value={asset.id}>{asset.name}</option>)}
              </select>
            </label>
            <label>Título<input className="input" required value={riskForm.title} onChange={(e) => setRiskForm({ ...riskForm, title: e.target.value })} /></label>
            <div className="grid grid-cols-2 gap-2">
              <label>Probabilidad
                <select className="input" value={riskForm.likelihood} onChange={(e) => setRiskForm({ ...riskForm, likelihood: Number(e.target.value) })}>
                  {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
              <label>Impacto
                <select className="input" value={riskForm.impact} onChange={(e) => setRiskForm({ ...riskForm, impact: Number(e.target.value) })}>
                  {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
            </div>
            <fieldset className="rounded-lg border border-slate-200 p-2">
              <legend className="px-1 text-sm font-medium">Amenazas del catálogo</legend>
              <div className="max-h-28 overflow-y-auto">
                {threats.map((item: RiskCatalogItem) => (
                  <label key={item.id} className="block text-sm">
                    <input type="checkbox" checked={riskForm.threat_ids.includes(item.id)} onChange={() => toggleCatalog("threat_ids", item.id)} /> {item.code} · {item.name}
                  </label>
                ))}
              </div>
            </fieldset>
            <fieldset className="rounded-lg border border-slate-200 p-2">
              <legend className="px-1 text-sm font-medium">Vulnerabilidades del catálogo</legend>
              <div className="max-h-28 overflow-y-auto">
                {vulnerabilities.map((item: RiskCatalogItem) => (
                  <label key={item.id} className="block text-sm">
                    <input type="checkbox" checked={riskForm.vulnerability_ids.includes(item.id)} onChange={() => toggleCatalog("vulnerability_ids", item.id)} /> {item.code} · {item.name}
                  </label>
                ))}
              </div>
            </fieldset>
            <button className="button button-primary" disabled={saveRisk.isPending}>Registrar riesgo</button>
          </form>
        </div>
      </div>

      <div className="panel overflow-x-auto">
        <h3>Mapa de calor — riesgo inherente</h3>
        {loadingHeatmap ? <p>Cargando…</p> : (
          <div className="grid min-w-[700px] grid-cols-5 gap-2">
            {LEVELS.slice().reverse().map((likelihood) =>
              LEVELS.map((impact) => {
                const cell = heatmap.find((c) => c.likelihood === likelihood && c.impact === impact);
                const risks = cell?.risks ?? [];
                return (
                  <div key={`${likelihood}-${impact}`} className="min-h-32 rounded-lg p-2" style={{ background: cellColor(likelihood * impact) }}>
                    <strong className="text-xs text-slate-800">P{likelihood} × I{impact} = {likelihood * impact}</strong>
                    {risks.map((risk: RiskItem) => (
                      <div key={risk.id} className="mt-2 rounded bg-white/85 p-2 text-xs text-slate-900">
                        <div className="font-semibold">{risk.title}</div>
                        <div className="mt-1 flex gap-1">
                          <select aria-label={`Probabilidad de ${risk.title}`} className="input" value={risk.likelihood}
                            onChange={(e) => moveFactors.mutate({ id: risk.id, likelihood: Number(e.target.value), impact: risk.impact })}>
                            {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                          </select>
                          <select aria-label={`Impacto de ${risk.title}`} className="input" value={risk.impact}
                            onChange={(e) => moveFactors.mutate({ id: risk.id, likelihood: risk.likelihood, impact: Number(e.target.value) })}>
                            {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                );
              }),
            )}
          </div>
        )}
      </div>

      {activeClientId !== undefined && hostScores.length > 0 && (
        <div className="panel overflow-x-auto">
          <h3>Prioridad de hosts (reputación externa + alertas internas)</h3>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: 12 }}>
            Combina AbuseIPDB/VirusTotal/GreyNoise con la frecuencia y severidad de eventos internos (30-P1/30-P2).
          </p>
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "1.3fr 1fr 1fr 1fr 1fr" }}>
              <span>IP</span><span>Alertas internas</span><span>Score interno</span><span>Score externo</span><span>Score compuesto</span>
            </div>
            {hostScores.map((host: HostScore) => (
              <div className="table-row" key={host.ip_address} style={{ gridTemplateColumns: "1.3fr 1fr 1fr 1fr 1fr" }}>
                <span style={{ fontWeight: 600 }}>{host.ip_address}</span>
                <span>{host.internal_alert_count}</span>
                <span>{host.internal_score}</span>
                <span>{host.external_score}</span>
                <span className="badge" style={{ background: cellColor(host.composite_score / 4) }}>{host.composite_score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="panel">
          <h3>Catálogo de amenazas</h3>
          <form onSubmit={submitThreat} className="mb-3 grid grid-cols-3 gap-2">
            <input className="input" placeholder="Código" value={threatForm.code} onChange={(e) => setThreatForm({ ...threatForm, code: e.target.value })} />
            <input className="input" placeholder="Nombre" value={threatForm.name} onChange={(e) => setThreatForm({ ...threatForm, name: e.target.value })} />
            <input className="input" placeholder="Categoría" value={threatForm.category} onChange={(e) => setThreatForm({ ...threatForm, category: e.target.value })} />
            <button className="button button-primary col-span-3" disabled={saveThreat.isPending}>Agregar amenaza</button>
          </form>
          <ul className="max-h-48 overflow-y-auto text-sm">
            {threats.map((item: RiskCatalogItem) => (
              <li key={item.id} className="border-b border-slate-100 py-1">{item.code} · {item.name} {item.is_global && <span className="text-xs text-slate-500">(global)</span>}</li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>Catálogo de vulnerabilidades</h3>
          <form onSubmit={submitVulnerability} className="mb-3 grid grid-cols-3 gap-2">
            <input className="input" placeholder="Código" value={vulnForm.code} onChange={(e) => setVulnForm({ ...vulnForm, code: e.target.value })} />
            <input className="input" placeholder="Nombre" value={vulnForm.name} onChange={(e) => setVulnForm({ ...vulnForm, name: e.target.value })} />
            <input className="input" placeholder="Categoría" value={vulnForm.category} onChange={(e) => setVulnForm({ ...vulnForm, category: e.target.value })} />
            <button className="button button-primary col-span-3" disabled={saveVulnerability.isPending}>Agregar vulnerabilidad</button>
          </form>
          <ul className="max-h-48 overflow-y-auto text-sm">
            {vulnerabilities.map((item: RiskCatalogItem) => (
              <li key={item.id} className="border-b border-slate-100 py-1">{item.code} · {item.name} {item.is_global && <span className="text-xs text-slate-500">(global)</span>}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
