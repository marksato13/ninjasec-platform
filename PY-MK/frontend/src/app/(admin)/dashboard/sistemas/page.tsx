"use client";

import { SistemasLista } from "@/components/ninja-dev/sistemas-lista";

export default function SistemasPage() {
  return (
    <section className="page-stack">
      <div className="section-heading">
        <div><p className="eyebrow">Ninja Dev</p><h2>Sistemas del cliente</h2></div>
      </div>
      <SistemasLista />
    </section>
  );
}
