"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { getGoogleLoginConfig, loginWithGoogle } from "@/lib/api";
import { persistSession } from "@/lib/auth";

const GSI_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

type GoogleCredentialResponse = { credential: string };

// Superficie minima de la API de Google Identity Services que usamos --
// no hay paquete de tipos oficial instalado, y no hace falta traer uno
// entero para 3 metodos.
type GoogleIdentityServices = {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
      }) => void;
      renderButton: (
        parent: HTMLElement,
        options: { theme: "outline" | "filled_black"; size: "large"; width: number; text: string }
      ) => void;
    };
  };
};

declare global {
  interface Window {
    google?: GoogleIdentityServices;
  }
}

let scriptLoadPromise: Promise<void> | null = null;

function loadGoogleScript(): Promise<void> {
  if (scriptLoadPromise) return scriptLoadPromise;
  scriptLoadPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("No se pudo cargar Google Identity Services")));
      return;
    }
    const script = document.createElement("script");
    script.src = GSI_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("No se pudo cargar Google Identity Services"));
    document.head.appendChild(script);
  });
  return scriptLoadPromise;
}

function currentTheme(): "outline" | "filled_black" {
  if (typeof document === "undefined") return "filled_black";
  return document.documentElement.dataset.theme === "light" ? "outline" : "filled_black";
}

type GoogleSignInButtonProps = {
  onError: (message: string) => void;
};

export function GoogleSignInButton({ onError }: GoogleSignInButtonProps) {
  const router = useRouter();
  const buttonRef = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getGoogleLoginConfig()
      .then((config) => {
        if (cancelled || !config.enabled) return;
        setEnabled(true);
        return loadGoogleScript().then(() => {
          if (cancelled || !buttonRef.current || !window.google) return;
          window.google.accounts.id.initialize({
            client_id: config.client_id,
            callback: async (response) => {
              try {
                const loginResponse = await loginWithGoogle(response.credential);
                persistSession(loginResponse.access_token, loginResponse.user);
                router.replace(loginResponse.redirect_to);
                router.refresh();
              } catch (err) {
                onError(err instanceof Error ? err.message : "No se pudo iniciar sesión con Google");
              }
            },
          });
          window.google.accounts.id.renderButton(buttonRef.current, {
            theme: currentTheme(),
            size: "large",
            width: 320,
            text: "continue_with",
          });
          setReady(true);
        });
      })
      // Google Identity Services no cargó (red, bloqueador de scripts, etc.)
      // -- degradar en silencio, el login con contraseña sigue funcionando.
      .catch(() => setEnabled(false));

    return () => {
      cancelled = true;
    };
  }, [router, onError]);

  if (!enabled) return null;

  return (
    <div className="google-signin-block">
      <div className="google-signin-divider">
        <span>o continúa con</span>
      </div>
      <div ref={buttonRef} className="google-signin-button" aria-busy={!ready} />
    </div>
  );
}
