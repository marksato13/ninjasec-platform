"use client";

import { WorkWindowsBoard } from "@/components/work-windows/work-windows-board";
import { getStoredUser } from "@/lib/auth";

// El cliente autoriza o rechaza; el colaborador pide y ejecuta las de sus proyectos.
export default function PortalWorkWindowsPage() {
  const role = getStoredUser()?.role;
  return (
    <section className="page-stack">
      <WorkWindowsBoard mode={role === "client" ? "client" : "staff"} />
    </section>
  );
}
