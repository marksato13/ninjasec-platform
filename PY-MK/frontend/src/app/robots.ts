import type { MetadataRoute } from "next";

import { SITIO_URL } from "@/lib/sitio";

/** Los buscadores ven el sitio público; nunca el panel, el portal ni la API. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/dashboard", "/portal", "/login", "/api/"],
    },
    sitemap: `${SITIO_URL}/sitemap.xml`,
    host: SITIO_URL,
  };
}
