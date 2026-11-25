"use client";

import { Check, Search } from "lucide-react";
import { useId, useMemo, useState } from "react";

export type ChipOption = { id: number; code?: string; name: string; group?: string };

type ChipPickerProps = {
  label: string;
  options: ChipOption[];
  selected: number[];
  onToggle: (id: number) => void;
  emptyText?: string;
};

/**
 * Seleccion multiple de un catalogo como chips, con buscador. Los elegidos se
 * muestran primero y el contador va en la etiqueta. Cada chip es un boton con
 * aria-pressed, asi que funciona con teclado y lector de pantalla.
 */
export function ChipPicker({ label, options, selected, onToggle, emptyText = "Sin resultados." }: ChipPickerProps) {
  const [query, setQuery] = useState("");
  const searchId = useId();

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? options.filter((o) => `${o.code ?? ""} ${o.name} ${o.group ?? ""}`.toLowerCase().includes(q))
      : options;
    return [...filtered].sort((a, b) => Number(selected.includes(b.id)) - Number(selected.includes(a.id)));
  }, [options, query, selected]);

  return (
    <fieldset className="chip-picker">
      <legend className="form-label">
        {label}
        {selected.length > 0 ? <span className="chip-picker__count">{selected.length} elegidas</span> : null}
      </legend>
      <label className="chip-picker__search" htmlFor={searchId}>
        <Search size={15} aria-hidden="true" />
        <input
          id={searchId}
          type="search"
          placeholder="Buscar por código o nombre"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label={`Buscar en ${label.toLowerCase()}`}
        />
      </label>
      <div className="chip-picker__list">
        {options.length === 0 ? (
          <p className="chip-picker__empty">El catálogo está vacío. Agrega elementos más abajo.</p>
        ) : visible.length === 0 ? (
          <p className="chip-picker__empty">{emptyText}</p>
        ) : null}
        {visible.map((option) => {
          const on = selected.includes(option.id);
          return (
            <button
              key={option.id}
              type="button"
              className={`chip${on ? " is-on" : ""}`}
              aria-pressed={on}
              onClick={() => onToggle(option.id)}
            >
              {on ? <Check size={13} strokeWidth={2.4} aria-hidden="true" /> : null}
              {option.code ? <span className="chip__code">{option.code}</span> : null}
              <span>{option.name}</span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
