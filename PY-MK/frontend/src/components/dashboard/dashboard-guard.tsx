"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";

import { SesionExpiradaListener } from "@/components/auth/sesion-expirada-listener";
import { getMe } from "@/lib/api";
import { clearSession, getStoredToken, isTokenExpired } from "@/lib/auth";
import { LOGIN_EXPIRED_PATH, SessionExpiredError } from "@/lib/session-expired";

const DASHBOARD_ROLES = ["super_admin", "admin", "collaborator"];

export function DashboardGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  // En desarrollo, StrictMode corre el efecto dos veces: la segunda ya no ve el
  // token caducado (lo borró la primera) y cambiaba /login?expired=1 por /login.
  const caducada = useRef(false);
  const [allowed, setAllowed] = useState(false);
  const [message, setMessage] = useState("Validando sesion...");

  useEffect(() => {
    if (caducada.current) return;
    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    if (isTokenExpired(token)) {
      caducada.current = true;
      clearSession();
      router.replace(LOGIN_EXPIRED_PATH);
      return;
    }

    async function validate() {
      try {
        const me = await getMe();
        if (me.role === "client") {
          router.replace("/portal");
          return;
        }
        if (!DASHBOARD_ROLES.includes(me.role)) {
          clearSession();
          router.replace("/login");
          return;
        }
        setAllowed(true);
      } catch (err) {
        // Sesión caducada: el aviso ya lleva a /login?expired=1; no lo pisamos.
        if (err instanceof SessionExpiredError) return;
        clearSession();
        setMessage("Sesion invalida. Redirigiendo...");
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
