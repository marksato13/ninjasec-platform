/**
 * Datos del sitio público para SEO: dirección canónica y páginas indexables.
 *
 * La URL sale de `NEXT_PUBLIC_SITE_URL` y, si no está, del dominio actual de
 * producción. Cuando haya dominio propio basta con fijar la variable en el build.
 */
import type { Metadata } from "next";

import { capsulaActiva } from "@/lib/capsulas";

export const SITIO_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://ninjasec-pe.duckdns.org").replace(/\/+$/, "");

export const SITIO_NOMBRE = "Ninja Tech";

/** Imagen para compartir en redes: el logo de la marca (720×720). */
export const SITIO_IMAGEN = "/brand/logo-ninja-tech.webp";

export const SITIO_DESCRIPCION =
  "Ciberseguridad y desarrollo de software para pymes en Perú. Dos áreas: Ninja Sec y Ninja Dev.";


/**
 * Rutas públicas que se pueden indexar. `/login` queda fuera a propósito, y
 * `/solucion` solo existe con la cápsula de telemetría encendida.
 */
export function rutasIndexables(): string[] {
  const rutas = ["/", "/servicios", "/proyectos", "/nosotros", "/contacto", "/agenda-demo", "/colabora"];
  if (capsulaActiva("telemetria")) rutas.push("/solucion");
  return rutas;
}

/**
 * Metadatos de una página pública con su dirección canónica.
 *
 * Next no fusiona `openGraph` campo a campo: el de la página reemplaza al del
 * layout. Por eso se repiten aquí la imagen, el nombre y el idioma.
 */
export function metadatosDePagina(ruta: string, titulo: string, descripcion: string): Metadata {
  return {
    title: titulo,
    description: descripcion,
    alternates: { canonical: ruta },
    openGraph: {
      type: "website",
      locale: "es_PE",
      siteName: SITIO_NOMBRE,
      title: `${titulo} · ${SITIO_NOMBRE}`,
      description: descripcion,
      url: ruta,
      images: [{ url: SITIO_IMAGEN, width: 720, height: 720, alt: "Logo de Ninja Tech" }],
    },
  };
}
