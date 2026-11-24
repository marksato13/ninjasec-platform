"use client";

import Image from "next/image";
import { Check } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { FaseSeguimiento, VistaSeguimiento } from "@/lib/api";

/**
 * La senda ninja: el recorrido del proyecto como un camino por el que Kuro avanza.
 *
 * Cada fase es una estacion. Las ya recorridas se iluminan, la actual late, y Kuro
 * camina desde la primera hasta donde va el proyecto cada vez que se abre la pantalla.
 *
 * Es decoracion con informacion, no solo decoracion: debajo del dibujo va la MISMA
 * informacion como lista (fase, estado, tareas), que es lo que leen los lectores de
 * pantalla y lo que se ve bien en el celular. El dibujo lleva `aria-hidden`.
 *
 * Con «reducir movimiento» no hay caminata: Kuro aparece ya en su sitio.
 */

// Posiciones de las 5 estaciones en un lienzo de 1000 x 220. Un camino que serpentea,
// no una linea recta: es lo que lo hace parecer un recorrido y no una barra de progreso.
const PUNTOS: [number, number][] = [
  [70, 150],
  [280, 70],
  [500, 150],
  [720, 70],
  [930, 140],
];

const CAMINO = `M ${PUNTOS[0][0]} ${PUNTOS[0][1]} ` +
  `C 150 150, 190 70, ${PUNTOS[1][0]} ${PUNTOS[1][1]} ` +
  `S 420 150, ${PUNTOS[2][0]} ${PUNTOS[2][1]} ` +
  `S 640 70, ${PUNTOS[3][0]} ${PUNTOS[3][1]} ` +
  `S 860 140, ${PUNTOS[4][0]} ${PUNTOS[4][1]}`;

const POSE: Record<string, string> = {
  diagnostico: "pointing",
  planificacion: "pointing",
  implementacion: "working",
  transferencia: "waving",
  acompanamiento: "thumbsup",
};

const ESTILOS = `
.senda-wrap { position: relative; }
.senda-svg { width: 100%; height: auto; display: block; overflow: visible; }
.senda-hecho { stroke-dasharray: 1; stroke-dashoffset: 1; animation: senda-dibujar 1.6s ease-out .2s forwards; }
@keyframes senda-dibujar { to { stroke-dashoffset: 0; } }
.senda-pulso { transform-box: fill-box; transform-origin: center; animation: senda-latir 1.8s ease-in-out infinite; }
@keyframes senda-latir { 0%,100% { transform: scale(1); opacity: .55; } 50% { transform: scale(1.7); opacity: 0; } }
.senda-kuro { position: absolute; width: 14%; max-width: 120px; transform: translate(-50%, -88%);
  transition: left 1.7s cubic-bezier(.45,.05,.2,1), top 1.7s cubic-bezier(.45,.05,.2,1); pointer-events: none;
  filter: drop-shadow(0 6px 10px rgba(0,0,0,.45)); }
.senda-kuro--flota { animation: senda-flotar 2.6s ease-in-out infinite; }
@keyframes senda-flotar { 0%,100% { margin-top: 0; } 50% { margin-top: -6px; } }
.senda-solo { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.senda-fases { list-style: none; margin: 14px 0 0; padding: 0; display: grid; gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
.senda-fase { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: var(--panel); }
.senda-fase[data-estado="current"] { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent); }
.senda-fase[data-estado="done"] { border-color: color-mix(in srgb, var(--success) 55%, var(--line)); }
.senda-fase[data-estado="todo"] { opacity: .72; }
@media (prefers-reduced-motion: reduce) {
  .senda-hecho { animation: none; stroke-dashoffset: 0; }
  .senda-pulso, .senda-kuro--flota { animation: none; }
  .senda-kuro { transition: none; }
}
`;

/** Fraccion del camino hasta la estacion `i`, suponiendo tramos iguales. Es el respaldo hasta medir el camino real. */
function fraccionLineal(i: number): number {
  return i / (PUNTOS.length - 1);
}

/** Mide el camino de verdad: en que fraccion de su longitud esta cada estacion. */
function medirEstaciones(camino: SVGPathElement): number[] {
  const total = camino.getTotalLength();
  const PASOS = 600;
  let desde = 0;
  return PUNTOS.map(([px, py]) => {
    // Las estaciones van en orden a lo largo del camino: se busca hacia delante, y asi
    // un camino que se cruza consigo mismo no confunde una estacion con otra.
    let mejor = desde, distancia = Infinity;
    for (let k = Math.floor((desde / total) * PASOS); k <= PASOS; k++) {
      const l = (k / PASOS) * total;
      const pt = camino.getPointAtLength(l);
      const d = (pt.x - px) ** 2 + (pt.y - py) ** 2;
      if (d < distancia) { distancia = d; mejor = l; }
    }
    desde = mejor;
    return mejor / total;
  });
}

const RECORRIDO_PX = 1; // pathLength normalizado: 1 = el camino entero

export function SendaNinja({ vista }: { vista: VistaSeguimiento }) {
  const fases = vista.phases;
  const completado = fases.every((f) => f.state === "done");
  const iActual = Math.max(0, fases.findIndex((f) => f.state === "current"));
  const destino = completado ? PUNTOS.length - 1 : iActual;

  // Kuro empieza en la primera estacion y camina hasta la actual al montar.
  const [posicion, setPosicion] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setPosicion(destino), 450);
    return () => clearTimeout(t);
  }, [destino]);

  const [x, y] = PUNTOS[Math.min(posicion, PUNTOS.length - 1)];
  const poseClave = completado ? "celebrating" : POSE[fases[destino]?.key ?? "diagnostico"];

  // Donde esta cada estacion a lo largo del camino. Hasta medirlo, se supone lineal.
  const caminoRef = useRef<SVGPathElement>(null);
  const [fracciones, setFracciones] = useState<number[]>(() => PUNTOS.map((_, i) => fraccionLineal(i)));
  useEffect(() => {
    if (caminoRef.current) setFracciones(medirEstaciones(caminoRef.current));
  }, []);
  const recorrido = completado ? 1 : fracciones[destino] ?? 0;

  return (
    <div className="senda-wrap">
      <style>{ESTILOS}</style>

      <svg className="senda-svg" viewBox="0 0 1000 220" aria-hidden focusable="false">
        <defs>
          <linearGradient id="senda-grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="var(--security, #22D3EE)" />
            <stop offset="1" stopColor="var(--primary, #3B82F6)" />
          </linearGradient>
        </defs>

        {/* El camino completo, apagado */}
        <path ref={caminoRef} d={CAMINO} fill="none" stroke="var(--line, #2a3a55)" strokeWidth="6" strokeLinecap="round" strokeDasharray="2 14" />

        {/* Lo ya recorrido, que se dibuja al entrar */}
        <path
          className="senda-hecho"
          d={CAMINO}
          pathLength={RECORRIDO_PX}
          fill="none"
          stroke="url(#senda-grad)"
          strokeWidth="7"
          strokeLinecap="round"
          style={{ strokeDasharray: `${completado ? 1 : recorrido} 1` }}
        />

        {PUNTOS.map(([px, py], i) => {
          const f = fases[i];
          const hecho = f?.state === "done";
          const actual = f?.state === "current";
          return (
            <g key={i} transform={`translate(${px} ${py})`}>
              {actual && <circle className="senda-pulso" r="22" fill="var(--primary, #3B82F6)" />}
              <circle
                r={actual ? 17 : 14}
                fill={hecho ? "var(--success, #10B981)" : actual ? "var(--primary, #3B82F6)" : "var(--panel, #0f1c2e)"}
                stroke={hecho || actual ? "none" : "var(--line, #2a3a55)"}
                strokeWidth="3"
              />
              <text
                textAnchor="middle"
                dy="5"
                fontSize="14"
                fontWeight="700"
                fill={hecho || actual ? "#fff" : "var(--muted, #7d90b0)"}
              >
                {hecho ? "✓" : i + 1}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Kuro, colocado en porcentajes del lienzo para que escale con el */}
      <Image
        className={`senda-kuro ${posicion === destino ? "senda-kuro--flota" : ""}`}
        src={`/mascot/kuro-${poseClave}.png`}
        alt=""
        aria-hidden
        width={160}
        height={160}
        style={{ left: `${(x / 1000) * 100}%`, top: `${(y / 220) * 100}%` }}
        priority
      />

      {/* La misma informacion, como lista: es lo que se lee con lector de pantalla y en el celular */}
      <ol className="senda-fases" aria-label="Fases del proyecto">
        {fases.map((f, i) => (
          <li
            key={f.key}
            className="senda-fase"
            data-estado={f.state}
            aria-current={f.state === "current" ? "step" : undefined}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                aria-hidden
                style={{
                  width: 22, height: 22, borderRadius: 999, display: "grid", placeItems: "center", fontSize: 12, fontWeight: 700,
                  background: f.state === "done" ? "var(--success)" : f.state === "current" ? "var(--primary)" : "transparent",
                  border: f.state === "todo" ? "1.5px solid var(--line)" : "none",
                  color: f.state === "todo" ? "var(--muted)" : "#fff",
                }}
              >
                {f.state === "done" ? <Check size={13} /> : i + 1}
              </span>
              <strong style={{ fontSize: "0.92rem" }}>{f.label}</strong>
            </div>
            <p className="muted-small" style={{ margin: "6px 0 0" }}>{f.description}</p>
            <p className="muted-small" style={{ margin: "6px 0 0" }}>
              <span className="senda-solo">Estado: </span>
              {f.state === "done" ? "Completada" : f.state === "current" ? "En curso" : "Pendiente"}
              {f.tasks_total > 0 && ` · ${f.tasks_done}/${f.tasks_total} tareas`}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}
