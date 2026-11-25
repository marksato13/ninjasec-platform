import { getStoredToken, isTokenExpired } from "@/lib/auth";
import { notifySessionExpired, SessionExpiredError } from "@/lib/session-expired";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8024/api/v1";

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getStoredToken();
  if (token && isTokenExpired(token)) {
    notifySessionExpired();
    throw new SessionExpiredError();
  }
  const isFormData = typeof FormData !== "undefined" && options?.body instanceof FormData;

  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
  });

  // 401 con token enviado: el servidor ya no lo acepta (revocado, usuario
  // desactivado, clave rotada). Es lo mismo que caducar. Sin token, el 401 es de
  // la propia ruta y se trata como cualquier otro error.
  if (response.status === 401 && token) {
    notifySessionExpired();
    throw new SessionExpiredError();
  }

  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const err = await response.json();
      message = (err.message ?? err.detail ?? message) as string;
    } catch { /* ignore */ }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function requestPublic<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options?.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const err = await response.json();
      message = (err.message ?? err.detail ?? message) as string;
    } catch { /* ignore */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function downloadFile(path: string, filenameFallback: string): Promise<void> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filenameFallback;
  a.click();
  URL.revokeObjectURL(url);
}

export function buildQuery(filters: Record<string, string | number | boolean | undefined | null>): string {
  const params = new URLSearchParams();
  for (const [key, val] of Object.entries(filters)) {
    if (val !== undefined && val !== null && val !== "") {
      params.set(key, String(val));
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
