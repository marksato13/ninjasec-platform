"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LOGIN_EXPIRED_PATH, SESSION_EXPIRED_EVENT } from "@/lib/session-expired";

/**
 * Atiende el aviso de sesión caducada que emite el cliente API y lleva al login
 * con el router de Next, sin recargar la página. No pinta nada.
 */
export function SesionExpiradaListener() {
  const router = useRouter();

  useEffect(() => {
    function alCaducar(evento: Event) {
      evento.preventDefault();
      router.replace(LOGIN_EXPIRED_PATH);
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, alCaducar);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, alCaducar);
  }, [router]);

  return null;
}
