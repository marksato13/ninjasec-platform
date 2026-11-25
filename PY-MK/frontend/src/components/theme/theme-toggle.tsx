"use client";

import { Check, Palette } from "lucide-react";
import { useCallback, useEffect, useId, useRef, useState, useSyncExternalStore } from "react";

import { applyTheme, isThemeId, THEMES, type ThemeId } from "./themes";

// El tema vive en <html data-theme>. Leerlo de ahi mantiene sincronizados todos
// los selectores (barra del panel y del portal) sin estado duplicado.
function subscribeTheme(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => observer.disconnect();
}

function readTheme(): ThemeId {
  const current = document.documentElement.dataset.theme;
  return isThemeId(current) ? current : "dark";
}

/**
 * Selector de tema: un boton que abre un menu con una muestra de color por tema.
 * Teclado: flechas para moverse, Enter/Espacio para elegir, Escape para cerrar
 * (el foco vuelve al boton). Se mantiene el nombre ThemeToggle para que la barra
 * superior y la del portal no cambien.
 */
export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribeTheme, readTheme, () => "dark" as ThemeId);
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const close = useCallback((returnFocus: boolean) => {
    setOpen(false);
    if (returnFocus) buttonRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    const items = menuRef.current?.querySelectorAll<HTMLButtonElement>("[role='menuitemradio']");
    const selected = Array.from(items ?? []).find((el) => el.getAttribute("aria-checked") === "true");
    (selected ?? items?.[0])?.focus();

    function onPointer(event: PointerEvent) {
      const target = event.target as Node;
      if (!menuRef.current?.contains(target) && !buttonRef.current?.contains(target)) close(false);
    }
    document.addEventListener("pointerdown", onPointer);
    return () => document.removeEventListener("pointerdown", onPointer);
  }, [open, close]);

  function choose(id: ThemeId) {
    applyTheme(id, true);
    close(true);
  }

  function onMenuKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const items = Array.from(
      menuRef.current?.querySelectorAll<HTMLButtonElement>("[role='menuitemradio']") ?? [],
    );
    const index = items.indexOf(document.activeElement as HTMLButtonElement);
    if (event.key === "Escape") {
      event.preventDefault();
      close(true);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      items[(index + 1) % items.length]?.focus();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      items[(index - 1 + items.length) % items.length]?.focus();
    } else if (event.key === "Home") {
      event.preventDefault();
      items[0]?.focus();
    } else if (event.key === "End") {
      event.preventDefault();
      items[items.length - 1]?.focus();
    } else if (event.key === "Tab") {
      close(false);
    }
  }

  const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];

  return (
    <div className="theme-picker">
      <button
        ref={buttonRef}
        className="button button-ghost button-icon"
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        aria-label={`Tema: ${current.label}. Cambiar tema`}
        title="Cambiar tema"
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" && !open) {
            e.preventDefault();
            setOpen(true);
          }
        }}
      >
        <Palette size={17} strokeWidth={1.9} aria-hidden="true" />
      </button>

      {open ? (
        <div
          ref={menuRef}
          id={menuId}
          className="theme-picker__menu"
          role="menu"
          aria-label="Tema de la interfaz"
          onKeyDown={onMenuKeyDown}
        >
          {THEMES.map((option) => {
            const selected = option.id === theme;
            return (
              <button
                key={option.id}
                type="button"
                role="menuitemradio"
                aria-checked={selected}
                className="theme-picker__item"
                onClick={() => choose(option.id)}
              >
                <span className="theme-picker__swatch" aria-hidden="true" style={{ background: option.swatch[0] }}>
                  <span style={{ background: option.swatch[1] }} />
                  <span style={{ background: option.swatch[2] }} />
                </span>
                <span className="theme-picker__text">
                  <span className="theme-picker__label">{option.label}</span>
                  <span className="theme-picker__hint">{option.hint}</span>
                </span>
                {selected ? <Check size={16} strokeWidth={2.2} aria-hidden="true" className="theme-picker__check" /> : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
