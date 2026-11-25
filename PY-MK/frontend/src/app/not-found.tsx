import Image from "next/image";
import Link from "next/link";

export default function NotFound() {
  return (
    <main className="not-found-shell">
      <div className="not-found-card">
        <Image src="/brand/anim/busca-404.webp" alt="Kuro buscando con una lupa" width={240} height={240} unoptimized priority />
        <div className="not-found-content">
          <p className="eyebrow">Error 404</p>
          <h1>Kuro no encuentra esta ruta</h1>
          <p>
            La página que buscas no existe o fue movida. Vuelve al inicio o
            agenda una reunión si necesitas ayuda.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/">Volver al inicio</Link>
            <Link className="button button-ghost" href="/contacto">Contactar soporte</Link>
          </div>
        </div>
      </div>
    </main>
  );
}
