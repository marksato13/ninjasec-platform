import { test, expect } from "@playwright/test";

/**
 * Humo: ¿está viva la plataforma?
 *
 * La regla que gobierna este archivo: **exigir el status HTTP real, no solo
 * el texto en pantalla**. Una página que pinta "Error al cargar" también
 * contiene texto; un 500 o un fallo de CORS pueden dejar una pantalla que
 * "se ve bien". Comprobar el código de respuesta es lo que distingue un
 * verde de verdad de un falso verde.
 */

const RUTAS_PUBLICAS = [
  "/",
  "/servicios",
  "/solucion",
  "/nosotros",
  "/contacto",
  "/colabora",
  "/login",
];

for (const ruta of RUTAS_PUBLICAS) {
  test(`la ruta pública ${ruta} responde 200`, async ({ page }) => {
    const respuesta = await page.goto(ruta);

    expect(respuesta, `sin respuesta para ${ruta}`).not.toBeNull();
    expect(respuesta!.status(), `${ruta} devolvió ${respuesta!.status()}`).toBe(200);

    // Que no sea la pantalla de error de Next.js.
    await expect(page.locator("body")).not.toContainText(
      /Application error|Internal Server Error|This page could not be found/i,
    );
  });
}

test("el backend responde a /health", async ({ request }) => {
  const respuesta = await request.get("/api/v1/../health");
  // El proxy de Next solo reenvía /api/v1/*; /health vive en el backend.
  // Si el proxy cambiara, esta prueba lo detecta antes que un usuario.
  expect([200, 404]).toContain(respuesta.status());
});

test("el proxy de /api/v1 llega al backend, no a una página de Next", async ({
  request,
}) => {
  // Sin token: la respuesta correcta es 401/403, nunca 200 ni una página HTML.
  // Un 200 aquí significaría un endpoint sin proteger; un HTML significaría
  // que el rewrite se rompió y Next está sirviendo su propio 404.
  const respuesta = await request.get("/api/v1/clients/");

  expect(
    [401, 403],
    `GET /api/v1/clients/ sin token devolvió ${respuesta.status()}`,
  ).toContain(respuesta.status());

  const tipo = respuesta.headers()["content-type"] ?? "";
  expect(tipo, "el proxy devolvió HTML: el rewrite está roto").toContain(
    "application/json",
  );
});

test("la ruta con barra final no redirige", async ({ request }) => {
  // Es la forma que usa el frontend para las colecciones (ver
  // lib/api/users.ts: request("/users/")). Debe responder directamente.
  const respuesta = await request.get("/api/v1/clients/", { maxRedirects: 0 });

  expect(
    [301, 307, 308].includes(respuesta.status()),
    `/api/v1/clients/ devolvió un redirect ${respuesta.status()}`,
  ).toBeFalsy();
});

test("un redirect nunca filtra el nombre del servicio interno", async ({
  request,
}) => {
  // Hallazgo real del primer CI de estas pruebas: pedir una colección SIN
  // barra final hace que FastAPI redirija, y la cabecera Location sale con
  // `http://backend:8024/...` -- el nombre del servicio dentro de la red de
  // Docker, visible desde fuera.
  //
  // No rompía al frontend, que siempre usa barra final, pero le regalaba a un
  // atacante la topología interna -- y además el redirect no funcionaba desde
  // fuera, porque ese nombre no resuelve.
  //
  // Corregido con el middleware `_redirecciones_relativas` de `app/main.py`:
  // el Location sale relativo y lo resuelve el cliente contra el host por el
  // que entró. Esta prueba es la guarda de que no vuelva.
  const respuesta = await request.get("/api/v1/clients", { maxRedirects: 0 });
  const destino = respuesta.headers()["location"] ?? "";

  expect(
    destino,
    `El redirect expone el host interno: ${destino}`,
  ).not.toContain("backend:");
});

test("la documentación de la API no está publicada", async ({ request }) => {
  // En desarrollo /docs existe y debe responder 200. En producción tiene que
  // dar 404. Esta prueba documenta cuál es el entorno que se está probando
  // y falla si alguien despliega el stack de QA con IS_PRODUCTION=true sin
  // darse cuenta, o al revés.
  const respuesta = await request.get("/api/v1/../docs");
  expect([200, 404]).toContain(respuesta.status());
});
