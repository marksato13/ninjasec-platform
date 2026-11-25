import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8024";

// Auditoria de seguridad 2026-11-25 (B4). La sesion vive en localStorage: si algun dia
// entra un XSS, esta politica le impide cargar scripts de otro dominio, enviar datos a
// otro dominio o meter la web en un iframe ajeno.
//
// Lo unico externo que carga la web es Google Sign-In. 'unsafe-inline' en scripts hace
// falta porque Next inyecta scripts en linea sin nonce; quitarlo exige nonces por
// peticion (paginas dinamicas), y eso es otro cambio.
// Solo en produccion: en desarrollo, la recarga en caliente de Next necesita 'unsafe-eval'.
const GOOGLE = "https://accounts.google.com";
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' ${GOOGLE}`,
  `style-src 'self' 'unsafe-inline' ${GOOGLE}`,
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  `connect-src 'self' ${GOOGLE}`,
  // El portal muestra en un iframe los PDF entregados al cliente, alojados fuera
  // (github_url). frame-src decide que podemos incrustar, no quien nos incrusta.
  `frame-src 'self' https: ${GOOGLE}`,
  "frame-ancestors 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join("; ");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  skipTrailingSlashRedirect: true,
  // No anunciar el framework en cada respuesta (X-Powered-By: Next.js).
  poweredByHeader: false,
  async headers() {
    if (process.env.NODE_ENV !== "production") return [];
    return [{ source: "/:path*", headers: [{ key: "Content-Security-Policy", value: CSP }] }];
  },
  // Auditoria de modulos 2026-11-25: paginas retiradas o mudadas. Redirigen en el
  // servidor, antes del guardia del portal (que no deja montar la pagina al equipo).
  async redirects() {
    return [
      { source: "/dashboard/approvals", destination: "/dashboard/formacion?tab=validar", permanent: false },
      { source: "/portal/support", destination: "/portal/tickets", permanent: false },
      { source: "/portal/tasks", destination: "/dashboard/mis-tareas", permanent: false },
      { source: "/portal/resources", destination: "/dashboard/projects", permanent: false },
      { source: "/portal/applications/:path*", destination: "/dashboard", permanent: false },
      // Paginas huerfanas retiradas (sin entrada en ningun menu).
      { source: "/portal/company", destination: "/portal", permanent: false },
      { source: "/portal/reports", destination: "/portal/documents", permanent: false },
      { source: "/portal/reviews", destination: "/portal/documents", permanent: false },
      { source: "/dashboard/architecture", destination: "/dashboard", permanent: false },
    ];
  },
  async rewrites() {
    return [
      // Catch-all con trailing slash explícito (debe ir antes del genérico)
      {
        source: "/api/v1/:path*/",
        destination: `${BACKEND_URL}/api/v1/:path*/`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
