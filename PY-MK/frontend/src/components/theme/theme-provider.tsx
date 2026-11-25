"use client";

import { useEffect } from "react";

import { applyTheme, readStoredTheme } from "./themes";

export function ThemeProvider() {
  useEffect(() => {
    const stored = readStoredTheme();
    if (stored) {
      applyTheme(stored, false);
      return;
    }
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    applyTheme(prefersLight ? "light" : "dark", false);
  }, []);

  return null;
}
