"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ArchitectureLayer, ArchitectureModel, getArchitectureModels } from "@/lib/api";
import { QK } from "@/lib/query-keys";

const LAYERS: { value: ArchitectureLayer; label: string }[] = [
  { value: "motivation", label: "Motivación" }, { value: "business", label: "Negocio" },
  { value: "application", label: "Aplicación" }, { value: "technology", label: "Tecnología" },
  { value: "implementation", label: "Implementación" },
];

export default function ArchitecturePage() {
  const [layer, setLayer] = useState<ArchitectureLayer>("motivation");
  const [modelId, setModelId] = useState<number | null>(null);
  const { data: models = [], isLoading } = useQuery<ArchitectureModel[]>({ queryKey: QK.architectureModels(), queryFn: getArchitectureModels });
  const selected = models.find((model) => model.id === modelId) ?? models[0];
  const elements = (selected?.elements ?? []).filter((element) => element.layer === layer);

  return <main className="space-y-6">
    <div><h1 className="text-2xl font-semibold">Arquitectura empresarial</h1><p className="text-sm text-slate-400">Repositorio ArchiMate por capa</p></div>
    <div className="flex flex-wrap gap-3">
      <select aria-label="Modelo" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" value={selected?.id ?? ""} onChange={(event) => setModelId(Number(event.target.value))}>
        {models.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.version} · {model.state}</option>)}
      </select>
      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Capa">
        {LAYERS.map((item) => <button key={item.value} role="radio" aria-checked={layer === item.value} onClick={() => setLayer(item.value)} className={`rounded-full px-4 py-2 text-sm ${layer === item.value ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-300"}`}>{item.label}</button>)}
      </div>
    </div>
    {isLoading ? <p>Cargando…</p> : !selected ? <p>No hay modelos de arquitectura.</p> :
      <div className="overflow-hidden rounded-xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="bg-slate-900 text-slate-400"><tr><th className="p-3">Elemento</th><th className="p-3">Tipo</th><th className="p-3">Origen</th></tr></thead><tbody>{elements.map((element) => <tr key={element.id} className="border-t border-slate-800"><td className="p-3"><div className="font-medium">{element.name}</div><div className="text-slate-400">{element.description}</div></td><td className="p-3">{element.element_type}</td><td className="p-3">{element.source_module ? `${element.source_module} / ${element.source_id ?? "—"}` : "Manual"}</td></tr>)}{elements.length === 0 && <tr><td colSpan={3} className="p-8 text-center text-slate-400">Sin elementos en esta capa.</td></tr>}</tbody></table></div>}
  </main>;
}
