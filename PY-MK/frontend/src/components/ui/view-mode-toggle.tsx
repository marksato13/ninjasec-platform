"use client";

import { LayoutGrid, List } from "lucide-react";

type ViewModeToggleProps = {
  mode: "cards" | "table";
  onChange: (mode: "cards" | "table") => void;
};

export function ViewModeToggle({ mode, onChange }: ViewModeToggleProps) {
  return (
    <div className="view-toggle">
      <button
        type="button"
        onClick={() => onChange("cards")}
        title="Vista cards"
        className={`view-toggle__btn ${mode === "cards" ? "view-toggle__btn--active" : ""}`}
      >
        <LayoutGrid size={15} />
      </button>
      <button
        type="button"
        onClick={() => onChange("table")}
        title="Vista tabla"
        className={`view-toggle__btn ${mode === "table" ? "view-toggle__btn--active" : ""}`}
      >
        <List size={15} />
      </button>
    </div>
  );
}
