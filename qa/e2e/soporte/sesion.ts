import { expect, type Page, type APIRequestContext } from "@playwright/test";

/**
 * Credenciales del seed de desarrollo (backend/app/db/seed.py).
 *
 * Solo existen cuando SEED_ON_STARTUP=true e IS_PRODUCTION=false, es decir
 * nunca en producción: app/main.py no siembra si is_production. Por eso
 * estas pruebas no pueden correr contra producción, y es deliberado.
 */
export const CUENTAS = {
  superAdmin: { email: "admin@ninjasec.local", password: "change-me" },
  admin: { email: "ops@ninjasec.local", password: "admin123" },
  colaborador: { email: "collab@ninjasec.local", password: "temp123" },
  cliente: { email: "client@ninjasec.local", password: "client123" },
  // Pertenece a OTRA organización. Es la pieza que hace posible probar el
  // aislamiento multi-tenant de verdad.
  clienteOtraOrg: { email: "client2@ninjasec.local", password: "client123" },
} as const;

export type Cuenta = (typeof CUENTAS)[keyof typeof CUENTAS];

/**
 * Inicia sesión por la interfaz, como lo haría una persona.
 *
 * No se atajan los pasos escribiendo el token en localStorage: eso probaría
 * que el dashboard pinta, no que el login funciona. El login es el flujo
 * que más veces se rompe y el que más caro sale romper.
 */
export async function iniciarSesion(page: Page, cuenta: Cuenta) {
  await page.goto("/login");

  await page.locator('input[type="email"]').fill(cuenta.email);
  await page.locator('input[autocomplete="current-password"]').fill(cuenta.password);
  await page.getByRole("button", { name: /ingresar|entrar|iniciar/i }).click();

  // Esperar a salir de /login es más fiable que esperar un texto concreto
  // del dashboard, que cambia cada vez que se rediseña.
  await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 });
}

/**
 * Pide un token por la API. Útil para preparar estado sin pasar por la UI.
 */
export async function obtenerToken(
  request: APIRequestContext,
  cuenta: Cuenta,
): Promise<string> {
  const respuesta = await request.post("/api/v1/auth/login", {
    data: { email: cuenta.email, password: cuenta.password },
  });
  expect(
    respuesta.ok(),
    `Login por API falló para ${cuenta.email}: ${respuesta.status()}`,
  ).toBeTruthy();
  const cuerpo = await respuesta.json();
  return cuerpo.access_token ?? cuerpo.token;
}
