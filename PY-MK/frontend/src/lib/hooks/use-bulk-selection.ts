"use client";

import { useMemo, useState } from "react";

export function useBulkSelection<T extends string | number>(visibleIds: T[]) {
  const [selected, setSelected] = useState<Set<T>>(new Set());

  const visibleSet = useMemo(() => new Set(visibleIds), [visibleIds]);
  const selectedVisible = useMemo(
    () => [...selected].filter((id) => visibleSet.has(id)),
    [selected, visibleSet]
  );
  const allSelected = visibleIds.length > 0 && selectedVisible.length === visibleIds.length;

  function toggle(id: T) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((current) => {
      if (allSelected) {
        const next = new Set(current);
        for (const id of visibleIds) next.delete(id);
        return next;
      }
      return new Set([...current, ...visibleIds]);
    });
  }

  function clear() {
    setSelected(new Set());
  }

  return {
    selected: selectedVisible,
    selectedSet: selected,
    isSelected: (id: T) => selected.has(id),
    allSelected,
    toggle,
    toggleAll,
    clear,
    count: selectedVisible.length,
  };
}
