import type { CSSProperties } from "react";
import {
  Activity,
  BookOpen,
  Boxes,
  BrickWall,
  Bug,
  ClipboardCheck,
  ClipboardList,
  Cloud,
  Code2,
  Database,
  FileSearch,
  Gauge,
  GitBranch,
  Globe,
  KeyRound,
  Landmark,
  Layers,
  LifeBuoy,
  ListChecks,
  ListOrdered,
  Lock,
  Network,
  Plug,
  Radar,
  Route,
  Router,
  Scale,
  Shapes,
  Sheet,
  Shield,
  ShieldCheck,
  Users,
  Waypoints,
  Workflow,
  type LucideIcon,
} from "lucide-react";

import { marcaPorNombre, type LucideMarca, type Marca } from "@/lib/marcas";

import s from "./marca-icono.module.css";

const LUCIDE: Record<LucideMarca, LucideIcon> = {
  Activity, BookOpen, Boxes, BrickWall, Bug, ClipboardCheck, ClipboardList, Cloud, Code2, Database,
  FileSearch, Gauge, GitBranch, Globe, KeyRound, Landmark, Layers, LifeBuoy, ListChecks, ListOrdered,
  Lock, Network, Plug, Radar, Route, Router, Scale, Shapes, Sheet, Shield, ShieldCheck, Users,
  Waypoints, Workflow,
};

function iniciales(nombre: string): string {
  const palabras = nombre.replace(/[^\p{L}\p{N} ]/gu, " ").split(/\s+/).filter(Boolean);
  if (palabras.length === 0) return "?";
  if (palabras.length === 1) return palabras[0].slice(0, 2).toUpperCase();
  return (palabras[0][0] + palabras[1][0]).toUpperCase();
}

type Props = {
  /** Nombre libre (una skill, una herramienta); se resuelve con `marcaPorNombre`. */
  nombre: string;
  /** Si ya se tiene la marca, se evita buscarla otra vez. */
  marca?: Marca;
  /** Lado en píxeles. */
  size?: number;
  /** Sin marca conocida: true muestra iniciales; false no pinta nada. */
  iniciales?: boolean;
  className?: string;
};

/**
 * Logo de una marca o tecnología, legible en temas claros y oscuros.
 *
 * - SVG de una tinta (Simple Icons): máscara CSS pintada con el color de marca.
 *   Las marcas casi negras usan el color del texto en temas oscuros, y las muy
 *   claras se oscurecen en el tema claro.
 * - SVG a color (Devicon): `<img>` tal cual; con `placa`, sobre fondo claro.
 * - Normas y servicios: icono de lucide en el color de marca.
 * - Sin icono: las iniciales del nombre.
 */
export function MarcaIcono({ nombre, marca, size = 18, iniciales: conIniciales = true, className }: Props) {
  const m = marca ?? marcaPorNombre(nombre);
  const etiqueta = m?.nombre ?? nombre;
  const estilo = { "--marca": m?.color ?? "var(--primary)", width: size, height: size } as CSSProperties;
  const tono = m?.tono === "oscuro" ? s.oscuro : m?.tono === "claro" ? s.claro : "";
  const clase = (...c: (string | undefined | false)[]) => [s.icono, tono, ...c, className].filter(Boolean).join(" ");

  if (m?.fuente === "simple-icons" && m.icono) {
    return (
      <span
        role="img"
        aria-label={etiqueta}
        className={clase(s.mono)}
        style={{ ...estilo, maskImage: `url(${m.icono})`, WebkitMaskImage: `url(${m.icono})` }}
      />
    );
  }
  if (m?.fuente === "devicon" && m.icono) {
    return (
      <span className={clase(s.color, m.placa && s.placa)} style={estilo}>
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG estático y local; next/image no aporta nada */}
        <img src={m.icono} alt={etiqueta} width={size} height={size} loading="lazy" decoding="async" />
      </span>
    );
  }
  if (m?.fuente === "lucide" && m.lucide) {
    const Icono = LUCIDE[m.lucide];
    return (
      <span role="img" aria-label={etiqueta} className={clase(s.lucide)} style={estilo}>
        <Icono size={size} strokeWidth={2} aria-hidden="true" />
      </span>
    );
  }
  if (!conIniciales) return null;
  return (
    <span
      role="img"
      aria-label={etiqueta}
      className={clase(s.iniciales)}
      style={{ ...estilo, fontSize: Math.max(8, Math.round(size * 0.42)) }}
    >
      {iniciales(etiqueta)}
    </span>
  );
}

/** Nombre con su logo delante; el texto sigue siendo el nombre original. */
export function ConMarca({ nombre, size = 16 }: { nombre: string; size?: number }) {
  return (
    <span className={s.conMarca}>
      <MarcaIcono nombre={nombre} size={size} iniciales={false} />
      <span>{nombre}</span>
    </span>
  );
}
