/**
 * Línea de negocio (Ninja Sec o Ninja Dev) de proyectos, clientes y tickets.
 *
 * La fuente es `areas.business_line` (backend, migración 20261128_03). Antes se
 * adivinaba por el texto del slug y fallaba con áreas como "Redes". Un área sin
 * línea, o un proyecto sin área, cuenta para las dos: nada desaparece por falta
 * de datos.
 */

import type { AreaItem, ProjectItem } from "@/lib/api";
import type { Linea, Modo } from "@/lib/modo";
import { visibleEnModo } from "@/lib/modo";

export type MapaAreas = Map<number, AreaItem>;

export function mapaDeAreas(areas: AreaItem[] | undefined): MapaAreas {
  return new Map((areas ?? []).map((a) => [a.id, a]));
}

export function lineaDeArea(areaId: number | null | undefined, areas: MapaAreas): Linea | null {
  if (!areaId) return null;
  return areas.get(areaId)?.business_line ?? null;
}

export function lineaDeProyecto(p: Pick<ProjectItem, "area_id">, areas: MapaAreas): Linea | null {
  return lineaDeArea(p.area_id, areas);
}

export function proyectoEnModo(p: Pick<ProjectItem, "area_id">, areas: MapaAreas, modo: Modo): boolean {
  return visibleEnModo(lineaDeProyecto(p, areas), modo);
}

/**
 * Un cliente (o un ticket, que cuelga del cliente: los tickets no tienen proyecto)
 * entra en un modo si tiene algún proyecto de esa línea o sin línea. Un cliente
 * sin proyectos aparece en los dos modos: todavía no se sabe qué contrata.
 */
export function clientesEnModo(proyectos: ProjectItem[] | undefined, areas: MapaAreas, modo: Modo): (clientId: number | null | undefined) => boolean {
  if (modo === "todo") return () => true;
  const conProyecto = new Set<number>();
  const enModo = new Set<number>();
  for (const p of proyectos ?? []) {
    if (!p.client_id) continue;
    conProyecto.add(p.client_id);
    if (proyectoEnModo(p, areas, modo)) enModo.add(p.client_id);
  }
  return (clientId) => !clientId || !conProyecto.has(clientId) || enModo.has(clientId);
}
