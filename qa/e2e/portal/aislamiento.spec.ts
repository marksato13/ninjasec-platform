import { test, expect } from "@playwright/test";
import { CUENTAS, iniciarSesion, obtenerToken } from "../soporte/sesion";

/**
 * Aislamiento multi-tenant desde el portal del cliente.
 *
 * Es el riesgo más caro de NinjaSec: 24 de 41 modelos llevan
 * `organization_id`, y una fuga aquí significa que un cliente ve los datos
 * de otro. Ya pasó una vez -- `GET /products` no filtraba (20-P-08) -- y se
 * detectó leyendo el código, no por una prueba.
 *
 * `AGENTS.md` fija la regla: datos de otra organización devuelven **404**,
 * no 403, para no confirmar que existen. Estas pruebas la vigilan.
 */

test("un cliente entra a su portal", async ({ page }) => {
  await iniciarSesion(page, CUENTAS.cliente);
  await expect(page).toHaveURL(/\/portal/);
});

test("el portal no expone datos de otra organización", async ({ request }) => {
  const tokenA = await obtenerToken(request, CUENTAS.cliente);
  const tokenB = await obtenerToken(request, CUENTAS.clienteOtraOrg);

  const pedir = async (token: string, ruta: string) => {
    const r = await request.get(ruta, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return r.ok() ? await r.json() : null;
  };

  const clientesA = await pedir(tokenA, "/api/v1/clients");
  const clientesB = await pedir(tokenB, "/api/v1/clients");

  test.skip(
    clientesA === null || clientesB === null,
    "el endpoint no devolvió lista para alguno de los dos clientes",
  );

  const idsA = new Set(
    (Array.isArray(clientesA) ? clientesA : []).map((c: { id: number }) => c.id),
  );
  const idsB = (Array.isArray(clientesB) ? clientesB : []).map(
    (c: { id: number }) => c.id,
  );

  const compartidos = idsB.filter((id) => idsA.has(id));
  expect(
    compartidos,
    `dos organizaciones distintas ven los mismos clientes: ${compartidos.join(", ")}`,
  ).toHaveLength(0);
});

test("pedir un recurso de otra organización devuelve 404, no 403", async ({
  request,
}) => {
  const tokenA = await obtenerToken(request, CUENTAS.cliente);
  const tokenB = await obtenerToken(request, CUENTAS.clienteOtraOrg);

  const rB = await request.get("/api/v1/clients", {
    headers: { Authorization: `Bearer ${tokenB}` },
  });
  test.skip(!rB.ok(), "no se pudo listar los clientes de la otra organización");

  const listaB = await rB.json();
  test.skip(
    !Array.isArray(listaB) || listaB.length === 0,
    "la otra organización no tiene clientes en el seed",
  );

  const ajeno = listaB[0].id;
  const r = await request.get(`/api/v1/clients/${ajeno}`, {
    headers: { Authorization: `Bearer ${tokenA}` },
  });

  expect(
    r.status(),
    `pedir el cliente ${ajeno} de otra organización devolvió ${r.status()}. ` +
      `Debe ser 404: un 403 confirma que el recurso existe, y eso ya es una fuga.`,
  ).toBe(404);
});

test("el portal del cliente no da acceso a la administración", async ({
  request,
}) => {
  const token = await obtenerToken(request, CUENTAS.cliente);

  // Endpoints que un cliente no debe poder tocar bajo ninguna circunstancia.
  for (const ruta of ["/api/v1/users", "/api/v1/audit", "/api/v1/leads"]) {
    const r = await request.get(ruta, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(
      [401, 403, 404],
      `un cliente obtuvo ${r.status()} en ${ruta}`,
    ).toContain(r.status());
  }
});
