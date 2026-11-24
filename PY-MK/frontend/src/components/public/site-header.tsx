"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getMenuPublico } from "@/lib/api";
import { capsulaActiva } from "@/lib/capsulas";

const links = [
  { href: "/", label: "Inicio" },
  { href: "/nosotros", label: "Nosotros" },
  { href: "/servicios", label: "Servicios" },
  { href: "/proyectos", label: "Proyectos" },
  { href: "/solucion", label: "Solucion" },
  { href: "/contacto", label: "Contacto" },
  { href: "/agenda-demo", label: "Agenda Demo" },
  { href: "/colabora", label: "Colabora" },
  { href: "/login", label: "Login" },
];

export function SiteHeader() {
  const pathname = usePathname();
  // Lo que se muestra lo decide el servidor (menus editables por rol).
  // Mientras no llega, o si falla, se muestra todo: la barra nunca se queda
  // vacia por un fallo de red.
  const [visibles, setVisibles] = useState<string[] | null>(null);
  // En pantallas chicas el menu va plegado detras de un boton.
  const [abierto, setAbierto] = useState(false);

  useEffect(() => {
    let vivo = true;
    getMenuPublico()
      .then((r) => {
        if (vivo) setVisibles(r.visibles);
      })
      .catch(() => {
        /* se queda con todos los enlaces */
      });
    return () => {
      vivo = false;
    };
  }, []);

  const conApi = capsulaActiva("telemetria");
  // Sin la plataforma no hay demo que agendar: la pagina sirve para pedir una reunion.
  const etiqueta = (l: { href: string; label: string }) =>
    l.href === "/agenda-demo" && !conApi ? "Agenda reunión" : l.label;
  // Sin respuesta del servidor se muestran los enlaces por defecto, pero NO los que dependen
  // de la capsula apagada: /solucion devuelve 404 y un enlace roto es peor que no ponerlo.
  const porDefecto = links.filter((l) => l.href !== "/solucion" || conApi);
  const enlaces = visibles ? links.filter((l) => visibles.includes(l.href)) : porDefecto;

  // El subtitulo promete reporting por API, y los conectores todavia son
  // simulados: solo se dice con la capsula de telemetria encendida.
  const subtitulo = conApi
    ? "API Reporting Platform"
    : "Ciberseguridad y desarrollo";

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand-mark" href="/">
          <span className="brand-mark__logo">NT</span>
          <span>
            <strong>Ninja Tech</strong>
            <small>{subtitulo}</small>
          </span>
        </Link>

        <button
          type="button"
          className="site-nav-toggle"
          aria-expanded={abierto}
          aria-controls="menu-publico"
          aria-label={abierto ? "Cerrar el menú" : "Abrir el menú"}
          onClick={() => setAbierto((v) => !v)}
        >
          <span aria-hidden>{abierto ? "✕" : "☰"}</span>
        </button>

        <nav id="menu-publico" className={`site-nav ${abierto ? "site-nav--open" : ""}`}>
          {enlaces.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setAbierto(false)}
              className={`site-nav__link ${pathname === link.href ? "site-nav__link--active" : ""}`}
            >
              {etiqueta(link)}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
