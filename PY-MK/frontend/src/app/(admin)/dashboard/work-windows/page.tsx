"use client";

import { WorkWindowsBoard } from "@/components/work-windows/work-windows-board";

export default function DashboardWorkWindowsPage() {
  return (
    <section className="page-stack">
      <div className="section-heading">
        <div><p className="eyebrow">Operaciones</p><h2>Ventanas de trabajo</h2></div>
      </div>
      <WorkWindowsBoard mode="staff" />
    </section>
  );
}
