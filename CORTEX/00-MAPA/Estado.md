# Estado

> Esta página la reescribe `/ns-estado`. Lo de abajo es la última lectura,
> no una verdad permanente. Si la fecha tiene más de una semana, vuelve a
> correr el comando antes de decidir nada con ella.

**Última lectura: 2026-11-22**

## Dónde estoy

Montando CORTEX. Rama `feat/cortex-workspace`, worktree
`ninjasec-wt-cortex`, base `origin/main` en `5ea9892`.

## PR abiertos

| PR | Estado |
| --- | --- |
| #134 hosting | Verde, sin fusionar |
| #133 guía SGSI | Verde, sin fusionar |
| #132 índices y slug | Verde, sin fusionar |
| #131 fugas multi-tenant | 1 check todavía en curso |
| #128 Playwright | **Rojo** en `E2E · Playwright` |
| #117 staging ESXi | **Rojo** en `Frontend build` y `Security / Trivy filesystem` |

Más 5 de Dependabot sin triar.

## Lo que está parado

- **`ninjasec-wt-payload`**: ocho archivos modificados y una migración sin
  añadir a git. Lleva días ahí.
- **18 worktrees vivos**, varios con ramas ya fusionadas.
- **`main` local va 19 commits por detrás de `origin/main`.** Ramificar de
  él es heredar bugs ya corregidos.

## Lo que bloquea el despliegue

1. Contraseñas del seed en texto plano.
2. Rotar G-03 — **de Mark**.
3. Copias de seguridad de Postgres.

## Decisión esperando a Mark

¿Los dos sistemas adicionales son estáticos, o alguno necesita backend?
4 GB (~S/ 250/año) frente a 8 GB (~S/ 430/año).

Ver [[Tablero]] para el detalle · [[MOC-Cortex]]
