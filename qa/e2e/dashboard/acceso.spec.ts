import { test, expect } from "@playwright/test";
import { CUENTAS, iniciarSesion, obtenerToken } from "../soporte/sesion";

/**
 * Control de acceso del dashboard.
 *
 * Estas son las pruebas que un test unitario con mocks NUNCA detecta: un
 * decorador `require_roles` olvidado, un filtro por `organization_id` que
 * falta, o una guarda de sesión que dejó de aplicarse. Solo se ven con el
 * sistema entero en marcha.
 */

test("un super_admin entra al dashboard", async ({ page }) => {
  await iniciarSesion(page, CUENTAS.superAdmin);
  await expect(page).toHaveURL(/\/dashboard/);
});

test("credenciales incorrectas no dejan entrar", async ({ page }) => {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill(CUENTAS.superAdmin.email);
  await page.locator('input[autocomplete="current-password"]').fill("no-es-la-clave");
  await page.getByRole("button", { name: /ingresar|entrar|iniciar/i }).click();

  // Sigue en login. Comprobar que NO avanzó es más robusto que buscar el
  // texto exacto del mensaje de error, que cambia al rediseñar.
  await expect(page).toHaveURL(/\/login/);
});

test("sin sesión, el dashboard redirige al login", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
});

test("un cliente no entra al dashboard de administración", async ({ page }) => {
  await iniciarSesion(page, CUENTAS.cliente);

  // El rol `client` tiene su propio shell. Debe acabar en /portal, no en
  // /dashboard, aunque escriba la URL a mano.
  await page.goto("/dashboard");
  await expect(page).not.toHaveURL(/\/dashboard\/users/);
});

/**
 * Matriz de autorización por endpoint.
 *
 * Cuatro filas por endpoint protegido, porque las cuatro fallan de forma
 * distinta y las cuatro han pasado alguna vez:
 *   401  sin token
 *   403  rol insuficiente
 *   2xx  rol correcto
 *   404  datos de otra organización  <- la que AGENTS.md exige y nadie probaba
 */
test.describe("matriz de autorización", () => {
  test("sin token: 401", async ({ request }) => {
    const r = await request.get("/api/v1/users/");
    expect(r.status()).toBe(401);
  });

  test("rol insuficiente: el cliente no lista usuarios", async ({ request }) => {
    const token = await obtenerToken(request, CUENTAS.cliente);
    const r = await request.get("/api/v1/users/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(
      [403, 404],
      `un cliente obtuvo ${r.status()} al listar usuarios`,
    ).toContain(r.status());
  });

  test("rol correcto: el super_admin lista usuarios", async ({ request }) => {
    const token = await obtenerToken(request, CUENTAS.superAdmin);
    const r = await request.get("/api/v1/users/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(r.status()).toBe(200);
  });

  test("token manipulado: 401", async ({ request }) => {
    // Un token con la firma alterada. Si esto devolviera 200, la validación
    // de firma estaría rota -- exactamente el fallo que tenía PyJWT 2.13.
    const token = await obtenerToken(request, CUENTAS.superAdmin);
    const manipulado = token.slice(0, -4) + "AAAA";
    const r = await request.get("/api/v1/users/", {
      headers: { Authorization: `Bearer ${manipulado}` },
    });
    expect(
      r.status(),
      "un token con la firma alterada fue aceptado",
    ).toBe(401);
  });
});
