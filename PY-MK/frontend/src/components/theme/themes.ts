/** Temas disponibles. Los colores de cada uno viven en globals.css. */
export const THEME_KEY = "ninjasec_theme";

export type ThemeId = "dark" | "light" | "ninja-sec" | "ninja-dev" | "medianoche";

export type ThemeOption = {
  id: ThemeId;
  label: string;
  hint: string;
  /** Fondo, superficie y acento, para la muestra del menu. */
  swatch: [string, string, string];
  scheme: "dark" | "light";
};

export const THEMES: ThemeOption[] = [
  { id: "dark", label: "Oscuro", hint: "El de siempre", swatch: ["#060D18", "#0F1E35", "#3B82F6"], scheme: "dark" },
  { id: "light", label: "Claro", hint: "Para oficinas con mucha luz", swatch: ["#F0F4FA", "#FFFFFF", "#2563EB"], scheme: "light" },
  { id: "ninja-sec", label: "Ninja Sec", hint: "Azul marino y cian del logo", swatch: ["#050B1A", "#0B1630", "#22D3EE"], scheme: "dark" },
  { id: "ninja-dev", label: "Ninja Dev", hint: "Índigo y violeta", swatch: ["#0A0820", "#16113A", "#A78BFA"], scheme: "dark" },
  { id: "medianoche", label: "Alto contraste", hint: "Texto blanco, bordes marcados", swatch: ["#010409", "#0A0F1C", "#7CB8FF"], scheme: "dark" },
];

export function isThemeId(value: unknown): value is ThemeId {
  return THEMES.some((t) => t.id === value);
}

export function readStoredTheme(): ThemeId | null {
  try {
    const stored = window.localStorage.getItem(THEME_KEY);
    return isThemeId(stored) ? stored : null;
  } catch {
    return null;
  }
}

export function applyTheme(id: ThemeId, persist: boolean) {
  const option = THEMES.find((t) => t.id === id) ?? THEMES[0];
  document.documentElement.dataset.theme = option.id;
  document.documentElement.style.colorScheme = option.scheme;
  if (!persist) return;
  try {
    window.localStorage.setItem(THEME_KEY, option.id);
  } catch {
    // Sin almacenamiento (ventana privada, datos bloqueados): el tema dura la sesion.
  }
}
