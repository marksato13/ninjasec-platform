import { request, requestPublic } from "./client";

/**
 * Menús editables por rol.
 *
 * Esto decide QUÉ SE MUESTRA, no qué se permite: lo que protege una pantalla
 * es el `require_roles` del backend. Ver `backend/app/core/navegacion.py`.
 */

export type Superficie = "public" | "staff" | "portal";

export type MisMenus = {
  role: string;
  /** Rutas visibles del panel del equipo, o null si el rol no entra al panel. */
  staff: string[] | null;
  /** Rutas visibles del portal, o null si el rol no entra al portal. */
  portal: string[] | null;
};

export type OpcionMenu = {
  clave: string;
  etiqueta: string;
  grupo: string;
  capsula: string | null;
  capsula_encendida: boolean;
  /** Audiencias a las que el backend deja usar esta pantalla. */
  permitidas: string[];
  /** Audiencias a las que no se puede ocultar. */
  obligatoria_para: string[];
  /** Solo trae las audiencias de `permitidas`. */
  visible: Record<string, boolean>;
};

export type SuperficieMenu = {
  audiencias: string[];
  opciones: OpcionMenu[];
};

export type ConfigMenus = {
  superficies: Record<Superficie, SuperficieMenu>;
};

export type CambioMenu = {
  superficie: Superficie;
  clave: string;
  audiencia: string;
  visible: boolean;
};

/** Sin sesión: la barra del sitio web. */
export const getMenuPublico = () =>
  requestPublic<{ visibles: string[] }>("/navigation/public");

export const getMisMenus = () => request<MisMenus>("/navigation/me");

export const getConfigMenus = () => request<ConfigMenus>("/navigation/config");

export const saveConfigMenus = (cambios: CambioMenu[]) =>
  request<ConfigMenus>("/navigation/config", {
    method: "PUT",
    body: JSON.stringify({ cambios }),
  });
