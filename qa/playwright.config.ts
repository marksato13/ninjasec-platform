import { defineConfig, devices } from "@playwright/test";

/**
 * Configuración de las pruebas E2E de NinjaSec.
 *
 * Dos proyectos porque la plataforma tiene DOS shells distintos, con guardas
 * de sesión y navegación diferentes: el dashboard (super_admin, admin,
 * collaborator) y el portal del cliente (client). Separarlos permite correr
 * uno solo mientras se trabaja en él.
 */

const BASE_URL = process.env.NINJASEC_BASE_URL ?? "http://localhost:3018";
const EN_CI = !!process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  // Un test lento no debe colgar el pipeline entero.
  timeout: 45_000,
  expect: { timeout: 10_000 },

  fullyParallel: true,
  // Evita que alguien suba un .only y deje media suite sin correr.
  forbidOnly: EN_CI,

  // Un reintento en CI para DETECTAR flaky, combinado con failOnFlakyTests
  // para no esconderlo: si un test necesita el reintento, el pipeline se
  // pone rojo igual. El reintento sirve para etiquetar, no para disimular.
  retries: EN_CI ? 1 : 0,
  failOnFlakyTests: EN_CI,

  // En CI, un solo worker: el stack de Docker Compose es compartido y los
  // tests escriben en la misma base de datos.
  workers: EN_CI ? 1 : undefined,

  reporter: EN_CI
    ? [["html", { open: "never" }], ["github"], ["list"]]
    : [["html", { open: "never" }], ["list"]],

  use: {
    baseURL: BASE_URL,
    // El producto es para PYMEs peruanas: fechas, moneda y formato locales.
    // Sin esto, un test que compara "21/11/2026" pasa en una máquina y
    // falla en otra.
    locale: "es-PE",
    timezoneId: "America/Lima",
    // Solo se guardan al fallar: en verde no interesan y pesan.
    trace: "retain-on-failure",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
    actionTimeout: 10_000,
  },

  projects: [
    {
      name: "dashboard",
      testMatch: /dashboard\/.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "portal",
      testMatch: /portal\/.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "publico",
      testMatch: /publico\/.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
