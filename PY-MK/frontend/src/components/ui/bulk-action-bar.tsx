"use client";

import type { ReactNode } from "react";

export type BulkAction = {
  label: string;
  onClick: () => void | Promise<void>;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  icon?: ReactNode;
  disabled?: boolean;
};

type BulkActionBarProps = {
  count: number;
  itemLabel: string;
  itemLabelPlural?: string;
  actions: BulkAction[];
  onClear: () => void;
};

export function BulkActionBar({ count, itemLabel, itemLabelPlural, actions, onClear }: BulkActionBarProps) {
  if (count === 0) return null;
  const label = count === 1 ? itemLabel : (itemLabelPlural ?? `${itemLabel}s`);

  return (
    <div className="bulk-action-bar" role="toolbar" aria-label="Acciones en lote">
      <span className="bulk-action-bar-count">
        {count} {label} seleccionado{count === 1 ? "" : "s"}
      </span>
      <div className="bulk-action-bar-actions">
        {actions.map((action) => (
          <button
            key={action.label}
            type="button"
            className={`button button-${action.variant ?? "secondary"} button-sm`}
            onClick={() => action.onClick()}
            disabled={action.disabled}
          >
            {action.icon}
            {action.label}
          </button>
        ))}
        <button type="button" className="button button-ghost button-sm" onClick={onClear}>
          Cancelar
        </button>
      </div>
    </div>
  );
}
