"use client";

import { useMemo, useState } from "react";
import { SearchX } from "lucide-react";

import { CATEGORIAS_MARCA, MARCAS, normalizarMarca } from "@/lib/marcas";
import { EmptyState } from "@/components/ui/empty-state";
import { MarcaIcono } from "@/components/ui/marca-icono";

import s from "./formacion.module.css";

/**
 * Tecnologías que dominamos: el mapa de marcas, normas y servicios con que
 * trabaja el equipo, por categoría. Sirve para declarar skills con el mismo
 * nombre y para que un comercial vea de un vistazo qué cubre NinjaSec.
 */
export function Tecnologias() {
  const [q, setQ] = useState("");
  const filtro = normalizarMarca(q);

  const grupos = useMemo(
    () =>
      CATEGORIAS_MARCA.map((c) => ({
        ...c,
        marcas: MARCAS.filter(
          (m) =>
            m.categoria === c.id &&
            (!filtro ||
              normalizarMarca(m.nombre).includes(filtro) ||
              (m.aliases ?? []).some((a) => normalizarMarca(a).includes(filtro))),
        ),
      })).filter((g) => g.marcas.length > 0),
    [filtro],
  );

  return (
    <div className="page-stack">
      <div className={s.toolbar}>
        <p className={s.intro}>
          Lo que el equipo usa en proyectos y laboratorios. Al declarar una skill, usa el mismo nombre y su logo aparecerá
          en tu perfil y en la matriz del equipo.
        </p>
        <input
          type="search"
          className={`input ${s.buscar}`}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar: FortiGate, ISO 27001…"
          aria-label="Buscar tecnología"
        />
      </div>

      {grupos.length === 0 ? (
        <EmptyState icon={SearchX} title="Nada con ese nombre" description="Prueba con la marca o con el protocolo." />
      ) : null}

      {grupos.map((g) => (
        <section key={g.id} className={`panel ${s.grupo}`} aria-labelledby={`tec-${g.id}`}>
          <h3 id={`tec-${g.id}`} className={s.grupoTitulo}>
            {g.titulo} <small>{g.marcas.length}</small>
          </h3>
          <ul className={s.logos}>
            {g.marcas.map((m) => (
              <li key={m.slug} className={s.logo}>
                <MarcaIcono nombre={m.nombre} marca={m} size={24} />
                <span>{m.nombre}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <p className={s.creditos}>
        Logos de Simple Icons (CC0) y Devicon (MIT); normas y servicios con iconos de Lucide. Cada marca pertenece a su
        dueño y aparece solo para indicar con qué tecnología trabajamos.
      </p>
    </div>
  );
}
