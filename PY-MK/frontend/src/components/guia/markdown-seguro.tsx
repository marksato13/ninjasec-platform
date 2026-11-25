/**
 * Renderizador de Markdown mínimo y seguro para las guías internas.
 *
 * Solo cubre lo que usan las guías (títulos, párrafos, listas, tablas, citas,
 * bloques de código, **negrita**, `código` y [enlaces](...)). No usa
 * dangerouslySetInnerHTML: cada nodo es un elemento React, así que el HTML que
 * venga en el texto se muestra como texto y nunca se ejecuta.
 *
 * Enlaces: http(s) abre en otra pestaña; "NN-ALGO.md" salta a esa sección de la
 * guía (lo resuelve `resolverEnlaceInterno`); cualquier otro esquema
 * (javascript:, data:...) se pinta como texto plano.
 */

import type { ReactNode } from "react";

type Bloque =
  | { t: "titulo"; nivel: number; texto: string }
  | { t: "parrafo"; texto: string }
  | { t: "lista"; ordenada: boolean; items: string[] }
  | { t: "tabla"; cabecera: string[]; filas: string[][] }
  | { t: "cita"; texto: string }
  | { t: "codigo"; texto: string };

function celdas(linea: string): string[] {
  return linea.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

function esSeparadorDeTabla(linea: string): boolean {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/.test(linea);
}

export function analizar(md: string): Bloque[] {
  const lineas = md.replace(/\r\n/g, "\n").split("\n");
  const bloques: Bloque[] = [];
  let i = 0;
  while (i < lineas.length) {
    const l = lineas[i];
    if (!l.trim()) { i++; continue; }

    if (l.startsWith("```")) {
      const cuerpo: string[] = [];
      i++;
      while (i < lineas.length && !lineas[i].startsWith("```")) cuerpo.push(lineas[i++]);
      i++;
      bloques.push({ t: "codigo", texto: cuerpo.join("\n") });
      continue;
    }

    const h = /^(#{1,6})\s+(.*)$/.exec(l);
    if (h) { bloques.push({ t: "titulo", nivel: h[1].length, texto: h[2].trim() }); i++; continue; }

    if (l.trim().startsWith("|") && i + 1 < lineas.length && esSeparadorDeTabla(lineas[i + 1])) {
      const cabecera = celdas(l);
      i += 2;
      const filas: string[][] = [];
      while (i < lineas.length && lineas[i].trim().startsWith("|")) filas.push(celdas(lineas[i++]));
      bloques.push({ t: "tabla", cabecera, filas });
      continue;
    }

    if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
      const ordenada = /^\s*\d+\./.test(l);
      const items: string[] = [];
      while (i < lineas.length && /^\s*([-*]|\d+\.)\s+/.test(lineas[i])) {
        let item = lineas[i].replace(/^\s*([-*]|\d+\.)\s+/, "");
        i++;
        // Continuación del mismo punto (línea sangrada sin viñeta)
        while (i < lineas.length && /^\s{2,}\S/.test(lineas[i]) && !/^\s*([-*]|\d+\.)\s+/.test(lineas[i])) {
          item += ` ${lineas[i].trim()}`;
          i++;
        }
        items.push(item);
      }
      bloques.push({ t: "lista", ordenada, items });
      continue;
    }

    if (l.startsWith(">")) {
      const cuerpo: string[] = [];
      while (i < lineas.length && lineas[i].startsWith(">")) cuerpo.push(lineas[i++].replace(/^>\s?/, ""));
      bloques.push({ t: "cita", texto: cuerpo.join(" ") });
      continue;
    }

    const cuerpo: string[] = [];
    while (
      i < lineas.length &&
      lineas[i].trim() &&
      !/^(#{1,6}\s|```|>|\s*([-*]|\d+\.)\s+)/.test(lineas[i]) &&
      !(lineas[i].trim().startsWith("|") && i + 1 < lineas.length && esSeparadorDeTabla(lineas[i + 1]))
    ) cuerpo.push(lineas[i++].trim());
    bloques.push({ t: "parrafo", texto: cuerpo.join(" ") });
  }
  return bloques;
}

export type ResolverEnlace = (destino: string) => string | null;

function enLinea(texto: string, resolver: ResolverEnlace, prefijo: string): ReactNode[] {
  const nodos: ReactNode[] = [];
  const patron = /(\*\*([^*]+)\*\*)|(`([^`]+)`)|(\[([^\]]+)\]\(([^)\s]+)\))/g;
  let ultimo = 0;
  let m: RegExpExecArray | null;
  let n = 0;
  while ((m = patron.exec(texto))) {
    if (m.index > ultimo) nodos.push(texto.slice(ultimo, m.index));
    const clave = `${prefijo}-${n++}`;
    if (m[2] !== undefined) {
      nodos.push(<strong key={clave}>{enLinea(m[2], resolver, clave)}</strong>);
    } else if (m[4] !== undefined) {
      nodos.push(<code key={clave}>{m[4]}</code>);
    } else {
      const etiqueta = m[6];
      const destino = m[7];
      if (/^https?:\/\//i.test(destino)) {
        nodos.push(
          <a key={clave} href={destino} target="_blank" rel="noopener noreferrer">
            {etiqueta}
          </a>,
        );
      } else {
        const interno = resolver(destino);
        nodos.push(interno ? <a key={clave} href={interno}>{etiqueta}</a> : <span key={clave}>{etiqueta}</span>);
      }
    }
    ultimo = m.index + m[0].length;
  }
  if (ultimo < texto.length) nodos.push(texto.slice(ultimo));
  return nodos;
}

export function MarkdownSeguro({
  markdown,
  resolver = () => null,
  className,
  omitirPrimerTitulo = false,
}: {
  markdown: string;
  resolver?: ResolverEnlace;
  className?: string;
  omitirPrimerTitulo?: boolean;
}) {
  let bloques = analizar(markdown);
  if (omitirPrimerTitulo && bloques[0]?.t === "titulo") bloques = bloques.slice(1);

  return (
    <div className={className}>
      {bloques.map((b, i) => {
        const k = `b${i}`;
        switch (b.t) {
          case "titulo": {
            // h1 lo pone la página; dentro del texto los niveles empiezan en h2.
            const nivel = Math.min(Math.max(b.nivel, 2), 4);
            const Tag = `h${nivel}` as "h2" | "h3" | "h4";
            return <Tag key={k}>{enLinea(b.texto, resolver, k)}</Tag>;
          }
          case "parrafo":
            return <p key={k}>{enLinea(b.texto, resolver, k)}</p>;
          case "cita":
            return <blockquote key={k}>{enLinea(b.texto, resolver, k)}</blockquote>;
          case "codigo":
            return <pre key={k}><code>{b.texto}</code></pre>;
          case "lista": {
            const Tag = b.ordenada ? "ol" : "ul";
            return (
              <Tag key={k}>
                {b.items.map((it, j) => <li key={`${k}-${j}`}>{enLinea(it, resolver, `${k}-${j}`)}</li>)}
              </Tag>
            );
          }
          case "tabla":
            return (
              <div key={k} className="guia-tabla" role="region" aria-label="Tabla" tabIndex={0}>
                <table>
                  <thead>
                    <tr>{b.cabecera.map((c, j) => <th key={j} scope="col">{enLinea(c, resolver, `${k}-h${j}`)}</th>)}</tr>
                  </thead>
                  <tbody>
                    {b.filas.map((f, j) => (
                      <tr key={j}>{f.map((c, x) => <td key={x}>{enLinea(c, resolver, `${k}-${j}-${x}`)}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
        }
      })}
    </div>
  );
}
