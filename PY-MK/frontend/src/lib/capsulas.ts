/**
 * Cápsulas de funcionalidad: qué pantallas existen en esta instancia.
 *
 * El criterio y los límites están en
 * `DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md`. En corto: hay módulos
 * terminados a medias, y uno devuelve datos que parecen reales y no lo son.
 * Ni se borran ni se exponen: se apagan.
 *
 * El backend es la fuente de verdad -- si su router no está registrado, la
 * pantalla no tiene de dónde leer. Aquí se replica la lista para dos cosas
 * que el backend no puede hacer:
 *
 *  1. No pintar la entrada del menú.
 *  2. Cerrar la página con `notFound()` si alguien teclea la URL.
 *
 * Lo segundo es lo que separa **apagar** de **esconder**. Esconder solo el
 * menú deja la ruta en pie, y adivinar la URL llega igual.
 */

/** Rutas del panel que pertenecen a una cápsula apagada. */
const RUTAS_DE_CAPSULA: Record<string, readonly string[]> = {
  telemetria: [
    "/dashboard/integrations",
    "/dashboard/hardening",
    "/dashboard/soc-report",
  ],
};

/**
 * Cápsulas encendidas en el build.
 *
 * Se lee de `NEXT_PUBLIC_CAPSULAS_ACTIVAS`, con el mismo formato que la
 * variable `CAPSULAS_ACTIVAS` del backend: nombres separados por comas.
 *
 * Tiene que ser `NEXT_PUBLIC_` porque la decide el build: el menú se pinta
 * en el cliente. Y por eso mismo **no es un control de seguridad**: es
 * gestión de alcance. Lo que protege de verdad es que el router del backend
 * no esté registrado.
 */
function capsulasActivas(): Set<string> {
  const crudo = process.env.NEXT_PUBLIC_CAPSULAS_ACTIVAS ?? "";
  return new Set(
    crudo
      .split(",")
      .map((parte) => parte.trim())
      .filter(Boolean),
  );
}

/** Si una cápsula concreta está encendida. */
export function capsulaActiva(nombre: string): boolean {
  return capsulasActivas().has(nombre);
}

/**
 * Si una ruta del panel está disponible.
 *
 * Una ruta que no pertenece a ninguna cápsula está siempre disponible: el
 * valor por defecto es "visible", para que añadir una pantalla nueva no
 * exija tocar este archivo.
 */
export function rutaDisponible(ruta: string): boolean {
  const activas = capsulasActivas();

  for (const [capsula, rutas] of Object.entries(RUTAS_DE_CAPSULA)) {
    if (activas.has(capsula)) continue;
    // Prefijo, no igualdad: /dashboard/integrations/42 también cae.
    if (rutas.some((base) => ruta === base || ruta.startsWith(`${base}/`))) {
      return false;
    }
  }
  return true;
}

/**
 * Para usar al principio de una página de cápsula.
 *
 * ```tsx
 * import { notFound } from "next/navigation";
 * import { rutaDisponible } from "@/lib/capsulas";
 *
 * if (!rutaDisponible("/dashboard/integrations")) notFound();
 * ```
 */
export const CAPSULAS_CONOCIDAS = Object.keys(RUTAS_DE_CAPSULA);
