"use client";

import { DesplieguesBoard } from "@/components/ninja-dev/despliegues-board";

export default function DesplieguesPage() {
  return (
    <section className="page-stack">
      <div className="section-heading">
        <div><p className="eyebrow">Ninja Dev</p><h2>Despliegues</h2></div>
      </div>
      <DesplieguesBoard />
    </section>
  );
}
