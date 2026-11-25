"use client";

import Link from "next/link";

import { ThemeToggle } from "@/components/theme/theme-toggle";
import { getSessionDisplayName, getStoredUser } from "@/lib/auth";


function getInitials(name?: string | null) {
  if (!name) return "NS";
  const parts = name.split(" ").filter(Boolean);
  const initials = parts.slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
  return initials || "NS";
}

export function PortalHeader({ onToggleSidebar }: { onToggleSidebar?: () => void }) {
  const user = getStoredUser();

  return (
    <header className="portal-header">
      <div className="portal-header__title">
        <strong style={{ fontSize: "0.95rem" }}>Portal de clientes</strong>
        <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>Ninja Tech</span>
      </div>

      <div className="portal-header__actions">
        {onToggleSidebar ? (
          <button className="sidebar-toggle" type="button" aria-label="Abrir menú" onClick={onToggleSidebar}>
            <span />
            <span />
            <span />
          </button>
        ) : null}
        <ThemeToggle />
        <Link className="button button-ghost profile-chip" href="/portal/profile">
          <span className="profile-avatar">{getInitials(user?.name || user?.email)}</span>
          <span className="profile-label">{getSessionDisplayName()}</span>
        </Link>
      </div>
    </header>
  );
}
