import { SITIO_DESCRIPCION, SITIO_IMAGEN, SITIO_NOMBRE, SITIO_URL } from "@/lib/sitio";

/**
 * Datos estructurados de la organización para buscadores. Solo lo que es
 * cierto hoy: sin teléfono, dirección ni redes sociales que aún no existen.
 */
const ORGANIZACION = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: SITIO_NOMBRE,
  url: SITIO_URL,
  logo: `${SITIO_URL}${SITIO_IMAGEN}`,
  description: SITIO_DESCRIPCION,
  areaServed: "PE",
};

export default function PublicLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <script
        type="application/ld+json"
        // Contenido fijo del propio código, no entrada de usuario.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(ORGANIZACION).replace(/</g, "\\u003c") }}
      />
      {children}
    </>
  );
}
