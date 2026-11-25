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
  updateRiskFactors,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { ChipPicker } from "@/components/ui/chip-picker";
import { ScalePicker } from "@/components/ui/scale-picker";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { levelTone, riskTone, SEVERITY_LABEL } from "@/components/ui/severity";

const LEVELS = [1, 2, 3, 4, 5];

// El valor que viaja al backend se queda en ingles; solo cambia lo que se lee.
const ASSET_TYPES: { value: string; label: string }[] = [
  { value: "information", label: "Información" },
  { value: "hardware", label: "Hardware" },
  { value: "software", label: "Software" },
  { value: "service", label: "Servicio" },
  { value: "people", label: "Personas" },
  { value: "facility", label: "Instalaciones" },
];

const emptyAssetForm = { client_id: 0, name: "", asset_type: "information", confidentiality: 3, integrity: 3, availability: 3 };
const emptyRiskForm = { client_id: 0, asset_id: 0, title: "", likelihood: 3, impact: 3, threat_ids: [] as number[], vulnerability_ids: [] as number[] };
const emptyCatalogForm = { code: "", name: "", category: "" };

function errorText(error: unknown) {
  return error instanceof Error ? error.message : undefined;
}

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
      setAssetForm({ ...emptyAssetForm, client_id: assetForm.client_id });
      notifySuccess("Activo registrado");
    },
    onError: (error) => notifyError("No se pudo registrar el activo", errorText(error)),
  });

  const saveRisk = useMutation({
    mutationFn: () => createRisk(riskForm),
    onSuccess: () => {
      invalidateRisks();
      setRiskForm({ ...emptyRiskForm, client_id: riskForm.client_id });
      notifySuccess("Riesgo registrado");
    },
    onError: (error) => notifyError("No se pudo registrar el riesgo", errorText(error)),
  });

  const moveFactors = useMutation({
    mutationFn: ({ id, likelihood, impact }: { id: number; likelihood: number; impact: number }) => updateRiskFactors(id, likelihood, impact),
    onSuccess: () => invalidateRisks(),
    onError: (error) => notifyError("No se pudo mover el riesgo", errorText(error)),
  });

  const saveThreat = useMutation({
    mutationFn: () => createRiskThreat(threatForm),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: QK.riskThreats() }); setThreatForm(emptyCatalogForm); notifySuccess("Amenaza agregada al catálogo"); },
    onError: (error) => notifyError("No se pudo agregar la amenaza", errorText(error)),
  });

  const saveVulnerability = useMutation({
    mutationFn: () => createRiskVulnerability(vulnForm),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: QK.riskVulnerabilities() }); setVulnForm(emptyCatalogForm); notifySuccess("Vulnerabilidad agregada al catálogo"); },
    onError: (error) => notifyError("No se pudo agregar la vulnerabilidad", errorText(error)),
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

  const assetValue = Math.max(assetForm.confidentiality, assetForm.integrity, assetForm.availability);
  const inherent = riskForm.likelihood * riskForm.impact;
  const totalRisks = heatmap.reduce((sum, cell) => sum + (cell.risks?.length ?? 0), 0);

  const toChip = (item: RiskCatalogItem) => ({ id: item.id, code: item.code, name: item.name, group: item.category });

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ninja Sec</p>
          <h2>Gestión de riesgos</h2>
        </div>
        <label className="form-field form-field--inline">
          <span className="form-label">Ver riesgos de</span>
          <select className="input" value={clientFilter} onChange={(e) => setClientFilter(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Todos los clientes</option>
            {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
          </select>
        </label>
      </div>

      <div className="risk-forms">
        <form className="panel form-card" onSubmit={submitAsset}>
          <header className="form-card__head">
            <h3>Registrar un activo</h3>
            <p>Lo que hay que proteger. Su valor es la mayor de sus tres notas.</p>
          </header>

          <div className="form-grid form-grid--2">
            <label className="form-field">
              <span className="form-label">Cliente</span>
              <select className="input" required value={assetForm.client_id} onChange={(e) => setAssetForm({ ...assetForm, client_id: Number(e.target.value) })}>
                <option value={0} disabled>Elige un cliente</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
              </select>
            </label>
            <label className="form-field">
              <span className="form-label">Tipo de activo</span>
              <select className="input" value={assetForm.asset_type} onChange={(e) => setAssetForm({ ...assetForm, asset_type: e.target.value })}>
                {ASSET_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </label>
          </div>
          <label className="form-field">
            <span className="form-label">Nombre</span>
            <input className="input" required placeholder="Ej.: Base de datos de facturación" value={assetForm.name} onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })} />
          </label>

          <div className="form-grid form-grid--3">
            <ScalePicker label="Confidencialidad" value={assetForm.confidentiality} onChange={(v) => setAssetForm({ ...assetForm, confidentiality: v })} />
            <ScalePicker label="Integridad" value={assetForm.integrity} onChange={(v) => setAssetForm({ ...assetForm, integrity: v })} />
            <ScalePicker label="Disponibilidad" value={assetForm.availability} onChange={(v) => setAssetForm({ ...assetForm, availability: v })} />
          </div>

          <footer className="form-card__foot">
            <p className="form-result" aria-live="polite">
              Valor del activo <strong>{assetValue}</strong> <SeverityBadge tone={levelTone(assetValue)} />
            </p>
            <button className="button button-primary" disabled={!assetForm.client_id || !assetForm.name} aria-busy={saveAsset.isPending}>
              Registrar activo
            </button>
          </footer>
        </form>

        <form className="panel form-card" onSubmit={submitRisk}>
          <header className="form-card__head">
            <h3>Registrar un riesgo</h3>
            <p>Qué le puede pasar a un activo, qué tan probable es y cuánto dolería.</p>
          </header>

          <div className="form-grid form-grid--2">
            <label className="form-field">
              <span className="form-label">Cliente</span>
              <select className="input" required value={riskForm.client_id} onChange={(e) => setRiskForm({ ...riskForm, client_id: Number(e.target.value), asset_id: 0 })}>
                <option value={0} disabled>Elige un cliente</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
              </select>
            </label>
            <label className="form-field">
              <span className="form-label">Activo</span>
              <select className="input" required disabled={!riskForm.client_id} value={riskForm.asset_id} onChange={(e) => setRiskForm({ ...riskForm, asset_id: Number(e.target.value) })}>
                <option value={0} disabled>{riskForm.client_id ? (assetsForRiskClient.length ? "Elige un activo" : "Este cliente no tiene activos") : "Primero elige un cliente"}</option>
                {assetsForRiskClient.map((asset: RiskAsset) => <option key={asset.id} value={asset.id}>{asset.name}</option>)}
              </select>
            </label>
          </div>
          <label className="form-field">
            <span className="form-label">Título</span>
            <input className="input" required placeholder="Ej.: Pérdida de datos por ransomware" value={riskForm.title} onChange={(e) => setRiskForm({ ...riskForm, title: e.target.value })} />
          </label>

          <div className="form-grid form-grid--2">
            <ScalePicker label="Probabilidad" ends={["Rara", "Casi segura"]} value={riskForm.likelihood} onChange={(v) => setRiskForm({ ...riskForm, likelihood: v })} />
            <ScalePicker label="Impacto" ends={["Leve", "Grave"]} value={riskForm.impact} onChange={(v) => setRiskForm({ ...riskForm, impact: v })} />
          </div>

          <ChipPicker label="Amenazas" options={threats.map(toChip)} selected={riskForm.threat_ids} onToggle={(id) => toggleCatalog("threat_ids", id)} emptyText="Ninguna amenaza coincide." />
          <ChipPicker label="Vulnerabilidades" options={vulnerabilities.map(toChip)} selected={riskForm.vulnerability_ids} onToggle={(id) => toggleCatalog("vulnerability_ids", id)} emptyText="Ninguna vulnerabilidad coincide." />

          <footer className="form-card__foot">
            <p className="form-result" aria-live="polite">
              Riesgo inherente <strong>{riskForm.likelihood} × {riskForm.impact} = {inherent}</strong> <SeverityBadge tone={riskTone(inherent)} />
            </p>
            <button className="button button-primary" disabled={!riskForm.client_id || !riskForm.asset_id || !riskForm.title} aria-busy={saveRisk.isPending}>
              Registrar riesgo
            </button>
          </footer>
        </form>
      </div>

      <article className="panel">
        <header className="form-card__head">
          <h3>Mapa de calor del riesgo inherente</h3>
          <p>{totalRisks === 0 ? "Aún no hay riesgos registrados para esta vista." : `${totalRisks} riesgo${totalRisks === 1 ? "" : "s"}. Cambia probabilidad o impacto desde cada tarjeta para moverlo.`}</p>
        </header>
        {loadingHeatmap ? <p className="muted-small">Cargando el mapa…</p> : (
          <div className="heatmap" role="table" aria-label="Riesgos por probabilidad e impacto">
            <span className="heatmap__axis heatmap__axis--y" aria-hidden="true">Probabilidad</span>
            <div className="heatmap__grid" role="rowgroup">
              {LEVELS.slice().reverse().map((likelihood) => (
                <div className="heatmap__row" role="row" key={likelihood}>
                  <span className="heatmap__tick" role="rowheader">{likelihood}</span>
                  {LEVELS.map((impact) => {
                    const cell = heatmap.find((c) => c.likelihood === likelihood && c.impact === impact);
                    const risks = cell?.risks ?? [];
                    const score = likelihood * impact;
                    const tone = riskTone(score);
                    return (
                      <div key={impact} role="cell" className={`heatmap__cell sev-${tone}${risks.length ? " has-risks" : ""}`} aria-label={`Probabilidad ${likelihood}, impacto ${impact}: ${SEVERITY_LABEL[tone]}, ${risks.length} riesgos`}>
                        <span className="heatmap__score">{score}</span>
                        {risks.map((risk: RiskItem) => (
                          <div key={risk.id} className="heatmap__risk">
                            <span className="heatmap__risk-title">{risk.title}</span>
                            <div className="heatmap__risk-factors">
                              <select aria-label={`Probabilidad de ${risk.title}`} className="input input--xs" value={risk.likelihood}
                                onChange={(e) => moveFactors.mutate({ id: risk.id, likelihood: Number(e.target.value), impact: risk.impact })}>
                                {LEVELS.map((v) => <option key={v} value={v}>P{v}</option>)}
                              </select>
                              <select aria-label={`Impacto de ${risk.title}`} className="input input--xs" value={risk.impact}
                                onChange={(e) => moveFactors.mutate({ id: risk.id, likelihood: risk.likelihood, impact: Number(e.target.value) })}>
                                {LEVELS.map((v) => <option key={v} value={v}>I{v}</option>)}
                              </select>
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              ))}
              <div className="heatmap__row heatmap__row--ticks" aria-hidden="true">
                <span className="heatmap__tick" />
                {LEVELS.map((impact) => <span key={impact} className="heatmap__tick">{impact}</span>)}
              </div>
            </div>
            <span className="heatmap__axis heatmap__axis--x" aria-hidden="true">Impacto</span>
          </div>
        )}
      </article>

      {activeClientId !== undefined && hostScores.length > 0 && (
        <article className="panel" style={{ overflowX: "auto" }}>
          <header className="form-card__head">
            <h3>Prioridad de hosts</h3>
            <p>Combina la reputación externa (AbuseIPDB, VirusTotal, GreyNoise) con la frecuencia y severidad de las alertas internas.</p>
          </header>
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "1.3fr 1fr 1fr 1fr 1fr" }}>
              <span>IP</span><span>Alertas internas</span><span>Puntaje interno</span><span>Puntaje externo</span><span>Puntaje combinado</span>
            </div>
            {hostScores.map((host: HostScore) => (
              <div className="table-row" key={host.ip_address} style={{ gridTemplateColumns: "1.3fr 1fr 1fr 1fr 1fr" }}>
                <span style={{ fontWeight: 600 }}>{host.ip_address}</span>
                <span>{host.internal_alert_count}</span>
                <span>{host.internal_score}</span>
                <span>{host.external_score}</span>
                <span><SeverityBadge tone={riskTone(host.composite_score / 4)}>{host.composite_score}</SeverityBadge></span>
              </div>
            ))}
          </div>
        </article>
      )}

      <div className="risk-forms">
        {([
          { title: "Catálogo de amenazas", items: threats, form: threatForm, setForm: setThreatForm, submit: submitThreat, pending: saveThreat.isPending, cta: "Agregar amenaza", codeHint: "T-DEL-06" },
          { title: "Catálogo de vulnerabilidades", items: vulnerabilities, form: vulnForm, setForm: setVulnForm, submit: submitVulnerability, pending: saveVulnerability.isPending, cta: "Agregar vulnerabilidad", codeHint: "V-TEC-04" },
        ] as const).map((c) => (
          <article className="panel form-card" key={c.title}>
            <header className="form-card__head">
              <h3>{c.title}</h3>
              <p>{c.items.length} en el catálogo. Los globales vienen con la plataforma.</p>
            </header>
            <form onSubmit={c.submit} className="form-grid form-grid--catalog">
              <label className="form-field">
                <span className="form-label">Código</span>
                <input className="input" placeholder={c.codeHint} value={c.form.code} onChange={(e) => c.setForm({ ...c.form, code: e.target.value })} />
              </label>
              <label className="form-field">
                <span className="form-label">Nombre</span>
                <input className="input" value={c.form.name} onChange={(e) => c.setForm({ ...c.form, name: e.target.value })} />
              </label>
              <label className="form-field">
                <span className="form-label">Categoría</span>
                <input className="input" value={c.form.category} onChange={(e) => c.setForm({ ...c.form, category: e.target.value })} />
              </label>
              <button className="button button-secondary" disabled={!c.form.code || !c.form.name || !c.form.category} aria-busy={c.pending}>{c.cta}</button>
            </form>
            <ul className="catalog-list">
              {c.items.map((item: RiskCatalogItem) => (
                <li key={item.id}>
                  <span className="chip__code">{item.code}</span>
                  <span>{item.name}</span>
                  {item.is_global ? <span className="catalog-list__tag">Global</span> : null}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
