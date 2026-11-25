import type { Metadata } from "next";
import "./globals.css";
import "sweetalert2/dist/sweetalert2.min.css";

import { AppProviders } from "@/components/providers/app-providers";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { SITIO_DESCRIPCION, SITIO_IMAGEN, SITIO_NOMBRE, SITIO_URL } from "@/lib/sitio";

export const metadata: Metadata = {
  metadataBase: new URL(SITIO_URL),
  title: {
    default: `${SITIO_NOMBRE} · Ciberseguridad y desarrollo para pymes`,
    template: `%s · ${SITIO_NOMBRE}`,
  },
  description: SITIO_DESCRIPCION,
  applicationName: SITIO_NOMBRE,
  openGraph: {
    type: "website",
    locale: "es_PE",
    siteName: SITIO_NOMBRE,
    images: [{ url: SITIO_IMAGEN, width: 720, height: 720, alt: "Logo de Ninja Tech" }],
  },
  twitter: { card: "summary", images: [SITIO_IMAGEN] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <ThemeProvider />
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
