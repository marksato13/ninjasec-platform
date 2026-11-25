"use client";

/**
 * Guía Ninja Dev: cómo trabaja el área de desarrollo (plan 34).
 *
 * El texto vive en DOCUMENTOS/NINJA-DEV/*.md y llega aquí como módulo generado
 * (scripts/generar-guia-ninja-dev.mjs). Una sección a la vez, elegida en el
 * índice; la sección activa va en el hash (#flujo-de-trabajo) para poder
 * compartir el enlace.
 */

import { useEffect, useState } from "react";

import { GUIA_NINJA_DEV } from "@/content/ninja-dev/guia.generated";

import { MarkdownSeguro } from "./markdown-seguro";
import styles from "./guia.module.css";

const PORTADA = GUIA_NINJA_DEV[0]?.slug ?? "";

function slugDeHash(): string {
  if (typeof window === "undefined") return PORTADA;
  const h = decodeURIComponent(window.location.hash.replace(/^#/, ""));
  return GUIA_NINJA_DEV.some((s) => s.slug === h) ? h : PORTADA;
}

/** "01-FLUJO-DE-TRABAJO.md" -> "#flujo-de-trabajo" si esa sección existe. */
function resolverEnlace(destino: string): string | null {
  const archivo = destino.split("#")[0].split("/").pop() ?? "";
  const s = GUIA_NINJA_DEV.find((x) => x.archivo.toLowerCase() === archivo.toLowerCase());
  return s ? `#${s.slug}` : null;
}

export function GuiaNinjaDev() {
  const [activa, setActiva] = useState(PORTADA);

  useEffect(() => {
    const sincronizar = () => setActiva(slugDeHash());
    sincronizar();
    window.addEventListener("hashchange", sincronizar);
    return () => window.removeEventListener("hashchange", sincronizar);
  }, []);

  const seccion = GUIA_NINJA_DEV.find((s) => s.slug === activa) ?? GUIA_NINJA_DEV[0];
  const indice = GUIA_NINJA_DEV.findIndex((s) => s.slug === seccion?.slug);
  const siguiente = GUIA_NINJA_DEV[indice + 1];

  if (!seccion) {
    return <p className={styles.vacio}>La guía todavía no tiene secciones.</p>;
  }

  return (
    <div className={styles.guia}>
      <nav className={styles.indice} aria-label="Secciones de la guía">
        <p className={styles.indiceTitulo}>Guía Ninja Dev</p>
        <ol>
          {GUIA_NINJA_DEV.map((s) => (
            <li key={s.slug}>
              <a
                href={`#${s.slug}`}
                aria-current={s.slug === seccion.slug ? "page" : undefined}
                className={styles.indiceEnlace}
              >
                {s.titulo}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <article className={styles.texto} aria-labelledby="guia-titulo">
        <h1 id="guia-titulo">{seccion.titulo}</h1>
        <MarkdownSeguro markdown={seccion.markdown} resolver={resolverEnlace} omitirPrimerTitulo />
        {siguiente ? (
          <a className={styles.siguiente} href={`#${siguiente.slug}`}>
            <span>Siguiente</span>
            {siguiente.titulo}
          </a>
        ) : null}
      </article>
    </div>
  );
}
