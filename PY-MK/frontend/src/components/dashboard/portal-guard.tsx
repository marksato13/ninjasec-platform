"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";

import { SesionExpiradaListener } from "@/components/auth/sesion-expirada-listener";
import { getMe } from "@/lib/api";
import { clearSession, getStoredToken, isPortalRole, isTokenExpired } from "@/lib/auth";
import { LOGIN_EXPIRED_PATH, SessionExpiredError } from "@/lib/session-expired";

export function PortalGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  // En desarrollo, StrictMode corre el efecto dos veces: la segunda ya no ve el
  // token caducado (lo borró la primera) y cambiaba /login?expired=1 por /login.
  const caducada = useRef(false);
  const [allowed, setAllowed] = useState(false);
  const [message, setMessage] = useState("Validando sesión...");

  useEffect(() => {
    if (caducada.current) return;
    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    // El panel ya lo comprobaba; el portal dejaba pasar al getMe con un token caducado.
    if (isTokenExpired(token)) {
      caducada.current = true;
      clearSession();
      router.replace(LOGIN_EXPIRED_PATH);
      return;
    }

    async function validate() {
      try {
        const me = await getMe();
        if (!isPortalRole(me.role)) {
          router.replace("/dashboard");
          return;
        }
        setAllowed(true);
      } catch (err) {
        // Sesión caducada: el aviso ya lleva a /login?expired=1; no lo pisamos.
        if (err instanceof SessionExpiredError) return;
        clearSession();
        setMessage("Sesión inválida. Redirigiendo...");
        router.replace("/login");
      }
    }

    validate();
  }, [router]);

  return (
    <>
      <SesionExpiradaListener />
      {allowed ? children : <div className="state-panel">{message}</div>}
    </>
  );
}
