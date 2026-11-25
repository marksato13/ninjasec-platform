"use client";

import { useId, type KeyboardEvent } from "react";

import { levelTone } from "./severity";

type ScalePickerProps = {
  label: string;
  value: number;
  onChange: (value: number) => void;
  /** Texto de ayuda para los extremos, p. ej. ["Rara", "Casi segura"]. */
  ends?: [string, string];
  min?: number;
  max?: number;
};

/**
 * Escala 1–5 como segmentos (grupo de radio). El segmento elegido toma el color
 * de su severidad. Teclado: flechas izquierda/derecha y Inicio/Fin.
 */
export function ScalePicker({ label, value, onChange, ends, min = 1, max = 5 }: ScalePickerProps) {
  const labelId = useId();
  const levels = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    let next = value;
    if (event.key === "ArrowRight" || event.key === "ArrowUp") next = Math.min(max, value + 1);
    else if (event.key === "ArrowLeft" || event.key === "ArrowDown") next = Math.max(min, value - 1);
    else if (event.key === "Home") next = min;
    else if (event.key === "End") next = max;
    else return;
    event.preventDefault();
    onChange(next);
    const group = event.currentTarget;
    requestAnimationFrame(() => group.querySelector<HTMLButtonElement>(`[data-level="${next}"]`)?.focus());
  }

  return (
    <div className="form-field">
      <span className="form-label" id={labelId}>
        {label}
      </span>
      <div className="scale-picker" role="radiogroup" aria-labelledby={labelId} onKeyDown={onKeyDown}>
        {levels.map((level) => {
          const selected = level === value;
          return (
            <button
              key={level}
              type="button"
              role="radio"
              aria-checked={selected}
              tabIndex={selected ? 0 : -1}
              data-level={level}
              className={`scale-picker__step${selected ? ` is-selected sev-${levelTone(level)}` : ""}`}
              onClick={() => onChange(level)}
            >
              {level}
            </button>
          );
        })}
      </div>
      {ends ? (
        <span className="scale-picker__ends" aria-hidden="true">
          <span>{ends[0]}</span>
          <span>{ends[1]}</span>
        </span>
      ) : null}
    </div>
  );
}
