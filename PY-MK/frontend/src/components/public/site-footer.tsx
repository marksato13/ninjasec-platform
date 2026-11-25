import Image from "next/image";
import Link from "next/link";

import { capsulaActiva } from "@/lib/capsulas";

export function SiteFooter() {
  const conApi = capsulaActiva("telemetria");

  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div>
          <Image className="site-footer__logo" src="/brand/logo-ninja-tech.webp" alt="Ninja Tech" width={180} height={180} />
          <h3>Ninja Tech</h3>
          <p>
            {conApi
              ? "Plataforma y firma tecnológica orientada a integraciones API, reporting automatizado, dashboards y servicios especializados para infraestructura y ciberseguridad."
              : "Ciberseguridad y desarrollo de software para pequeñas y medianas empresas, en dos áreas: Ninja Sec y Ninja Dev. Un equipo de estudiantes y profesionales que practican con casos reales."}
          </p>
        </div>

        <div>
          <h4>Enlaces</h4>
          <ul>
            <li><Link href="/servicios">Servicios</Link></li>
            <li><Link href="/proyectos">Proyectos</Link></li>
            {/* La solucion describe conectores por API: va con la capsula. */}
            {conApi && <li><Link href="/solucion">Solucion</Link></li>}
            <li><Link href="/agenda-demo">{conApi ? "Agenda Demo" : "Agenda reunión"}</Link></li>
            <li><Link href="/colabora">Colabora</Link></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
