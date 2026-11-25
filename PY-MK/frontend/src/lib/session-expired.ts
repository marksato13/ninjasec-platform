import { clearSession } from "@/lib/auth";

/**
 * Aviso de sesión caducada, desacoplado del router.
 *
 * El cliente API no es un componente y no puede usar `useRouter`. En vez de
 * recargar la página entera con `window.location`, emite este evento; quien lo
 * escucha (`SesionExpiradaListener`, montado en los guards del panel y del portal)
 * lo cancela y navega con el router de Next. Si nadie lo escucha —una página
 * pública, por ejemplo—, se cae al `window.location` de siempre.
 */
export const SESSION_EXPIRED_EVENT = "ninjasec:sesion-expirada";
export const LOGIN_EXPIRED_PATH = "/login?expired=1";

/**
 * Lo lanza el cliente API tras avisar. Quien la captura no debe volver a
 * redirigir: la navegación ya está en marcha y otra la pisaría.
 */
export class SessionExpiredError extends Error {
  constructor() {
    super("Sesión expirada");
    this.name = "SessionExpiredError";
  }
}

/** Varias peticiones en paralelo fallan a la vez: una sola navegación basta. */
const VENTANA_MS = 3000;
let ultimoAviso = 0;

export function notifySessionExpired(): void {
  clearSession();
  if (typeof window === "undefined") return;

  const ahora = Date.now();
  if (ahora - ultimoAviso < VENTANA_MS) return;
  ultimoAviso = ahora;

  const evento = new Event(SESSION_EXPIRED_EVENT, { cancelable: true });
  const nadieLoAtendio = window.dispatchEvent(evento);
  if (nadieLoAtendio) {
    // Respaldo deliberado: fuera de React no hay router y nadie montó el listener.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = LOGIN_EXPIRED_PATH;
  }
}
