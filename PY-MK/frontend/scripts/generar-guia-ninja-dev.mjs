#!/usr/bin/env node
/**
 * Convierte DOCUMENTOS/NINJA-DEV/*.md en src/content/ninja-dev/guia.generated.ts.
 *
 * Por qué un archivo generado y versionado, y no importar los .md en el build:
 * - no hay que tocar next.config.ts (loaders) ni el Dockerfile;
 * - la imagen de producción (standalone) no necesita leer disco en ejecución;
 * - el diff del PR muestra exactamente qué texto cambia en la plataforma.
 *
 * Uso, desde PY-MK/frontend:
 *   node scripts/generar-guia-ninja-dev.mjs              # lee ../../DOCUMENTOS/NINJA-DEV
 *   node scripts/generar-guia-ninja-dev.mjs <carpeta>    # otra carpeta
 */
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const origen = resolve(process.argv[2] ?? join(aqui, "..", "..", "..", "DOCUMENTOS", "NINJA-DEV"));
const destino = join(aqui, "..", "src", "content", "ninja-dev", "guia.generated.ts");

const archivos = readdirSync(origen)
  .filter((f) => /^\d\d-.+\.md$/.test(f))
  .sort();

if (archivos.length === 0) {
  console.error(`No hay archivos NN-*.md en ${origen}`);
  process.exit(1);
}

const secciones = archivos.map((archivo) => {
  const texto = readFileSync(join(origen, archivo), "utf8").replace(/\r\n/g, "\n").trim();
  const titulo = (texto.match(/^#\s+(.+)$/m)?.[1] ?? archivo).trim();
  const slug = archivo.replace(/^\d\d-/, "").replace(/\.md$/, "").toLowerCase();
  return { archivo, slug, titulo, markdown: texto };
});

const cabecera = `// ARCHIVO GENERADO por scripts/generar-guia-ninja-dev.mjs. No editar a mano:
// edita DOCUMENTOS/NINJA-DEV/*.md y vuelve a generar.
// Origen: ${archivos.length} archivos de DOCUMENTOS/NINJA-DEV.

export type SeccionGuia = { archivo: string; slug: string; titulo: string; markdown: string };

export const GUIA_NINJA_DEV: SeccionGuia[] = `;

mkdirSync(dirname(destino), { recursive: true });
writeFileSync(destino, `${cabecera}${JSON.stringify(secciones, null, 2)};\n`, "utf8");
console.log(`Generado ${destino} con ${secciones.length} secciones.`);
