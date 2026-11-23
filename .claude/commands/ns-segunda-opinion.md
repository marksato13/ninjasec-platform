---
description: Pide a Codex una revisión adversarial del diff actual, sin contarle la intención
argument-hint: (opcional) número de PR
---

Clase **T5**: segundo par de ojos de otra familia de modelos.

El valor no está en la capacidad, está en el **sesgo**. Dos modelos de la
misma familia pasan por alto los mismos errores. Un revisor de otra familia
rompe esa correlación por poco dinero.

## 1. Preparar el diff

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git diff origin/main...HEAD > "<scratchpad>/diff-a-revisar.patch"
wc -l "<scratchpad>/diff-a-revisar.patch"
```

Si es un PR concreto: `gh pr diff $1 > "<scratchpad>/diff-a-revisar.patch"`.

Si el diff pasa de unas 2.000 líneas, pártelo por área. Un revisor que no
cabe en su ventana no revisa, adivina.

## 2. Lanzar Codex

```bash
# [LAPTOP Bash] -> lo ejecuto yo
codex exec --cd "<ruta del worktree>" "Revisa este diff y dime qué falla: errores de corrección, casos no cubiertos, condiciones de carrera, fugas de recursos. No propongas refactorizaciones de estilo."
```

**No le cuentes qué intentabas hacer.** Si le das la intención, te confirma
tu propio razonamiento en vez de atacarlo. Dale el diff y la pregunta.

## 3. Lo que NO se le manda

- `.env`, claves, tokens, el seed de credenciales.
- Datos reales de clientes.
- Volcados de base.

Si el diff los contiene, ese diff no debería existir: vuelve al paso 1 de
`/ns-pr`.

## 4. Triar lo que devuelva

Cada hallazgo entra en una de tres cajas:

| Caja | Qué hacer |
| --- | --- |
| **Confirmado** | Lo reproduces en el código. Se arregla |
| **Plausible** | No lo puedes confirmar ni descartar. Se anota en la ficha como riesgo |
| **Falso** | Codex no conoce las convenciones del repo. Se descarta **diciendo por qué** |

La tercera caja se llena mucho y es normal: Codex no ha leído `AGENTS.md`.
No sabe que los datos de otro tenant devuelven 404 a propósito, ni por qué
`from __future__ import annotations` tiene que quedarse.

## 5. Reportar

Qué dijo, qué confirmaste, qué descartaste y por qué. **Un hallazgo de otro
agente no es una verdad**: es una hipótesis con un buen origen.

Si no encontró nada que no supieras, dilo también. También es información:
significa que la revisión propia iba bien.
