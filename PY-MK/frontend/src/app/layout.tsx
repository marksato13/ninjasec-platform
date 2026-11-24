import type { Metadata } from "next";
import "./globals.css";
import "sweetalert2/dist/sweetalert2.min.css";

import { AppProviders } from "@/components/providers/app-providers";
import { ThemeProvider } from "@/components/theme/theme-provider";

export const metadata: Metadata = {
  title: "Ninja Tech",
  description: "Ciberseguridad y desarrollo de software para pymes.",
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
