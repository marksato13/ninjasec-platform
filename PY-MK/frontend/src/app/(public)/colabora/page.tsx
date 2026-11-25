import { JobApplicationForm } from "@/components/public/job-application-form";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { metadatosDePagina } from "@/lib/sitio";

export const metadata = {
  ...metadatosDePagina(
    "/colabora",
    "Colabora",
    "Forma parte de Ninja Tech como colaborador en proyectos de ciberseguridad y desarrollo.",
  ),
};

export default function ColaboraPage() {
  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Colabora</p>
        <h1>Forma parte de Ninja Tech.</h1>
        <p>
          Buscamos estudiantes y profesionales con interés en infraestructura y redes, nube (AWS),
          ciberseguridad y desarrollo de software. Trabajarás en casos reales, con seguimiento.
        </p>
      </section>
      <JobApplicationForm />
    </PublicPageShell>
  );
}
