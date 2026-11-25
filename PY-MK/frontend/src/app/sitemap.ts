import type { MetadataRoute } from "next";

import { SITIO_URL, rutasIndexables } from "@/lib/sitio";

/** Solo páginas públicas que existen en este build. */
export default function sitemap(): MetadataRoute.Sitemap {
  return rutasIndexables().map((ruta) => ({
    url: `${SITIO_URL}${ruta === "/" ? "" : ruta}`,
    changeFrequency: "monthly",
    priority: ruta === "/" ? 1 : 0.7,
  }));
}
