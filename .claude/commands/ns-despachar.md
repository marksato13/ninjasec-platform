---
description: Clasifica un pendiente de NinjaSec y le asigna motor y modelo según la política de enrutado
argument-hint: 12-P-03
---

Decide **quién** hace **$1** y con **qué modelo**, y escríbelo en su ficha.

Lee `CORTEX/10-ENRUTADO/Politica-de-enrutado.md` antes de clasificar. Si no
está en contexto, cárgala.

## 1. Leer la ficha

`CORTEX/40-TAREAS/$1-*.md`. Si no existe, **detente**: primero `/ns-abrir $1`.

Si la ficha tiene decisiones pendientes que afectan al diseño, **detente
también**. No se despacha trabajo con el alcance abierto.

## 2. Clasificar

Aplica los cuatro ejes en este orden. **El primero que dispare, manda.**

**Eje 1 — radio de daño.** ¿El cambio puede filtrar datos de otro tenant,
romper el login, perder datos o exponer un secreto? Mira si toca:

- cualquier archivo bajo `PY-MK/backend/app/core/`
- cualquier consulta o ruta con `organization_id`
- cualquier migración de Alembic
- `.env`, el seed de contraseñas, JWT o configuración de producción

→ **T4. Claude principal, Opus 5, no se delega.** Fin de la clasificación.

**Eje 2 — contexto propio.** ¿Hace falta conocer `AGENTS.md`, las
convenciones del repo o el estado de los PR? → Se queda en Claude.

**Eje 3 — volumen.** ¿Muchos archivos y poca decisión? → Modelo barato.

**Eje 4 — verificabilidad.** ¿Hay una prueba que diga sí o no sin criterio
humano? → Se puede delegar con red de seguridad.

Si dudas entre dos clases, **gana la más cara.**

## 3. Asignar

| Clase | Motor | Modelo |
| --- | --- | --- |
| T0 barrido | subagente `ns-explorador` | haiku |
| T1 mecánica | OpenCode | `opencode/deepseek-v4.1-flash-free` o `opencode/glm-5.3-flash` |
| T2 backend acotado | subagente `ns-backend` | opus |
| T3 frontend | subagente `ns-frontend` | sonnet |
| **T4 seguridad / tenancy** | **principal, sin delegar** | **opus** |
| T5 segunda opinión | Codex CLI | GPT-5.3-Codex |
| T6 investigación | subagente + WebSearch | sonnet |
| T7 negocio y redacción | principal | opus |
| T8 verificación | subagente `ns-revisor-ci` | sonnet |

## 4. Si sale fuera de Claude

Codex y OpenCode **no han leído `AGENTS.md`**. Antes de lanzarlos, escribe
en la ficha, en el bloque de despacho:

- **Qué se le entrega:** el contexto exacto, autocontenido. Un archivo, un
  patrón, un diff. Nada de «mira el repo».
- **Qué NO se le manda:** nunca `.env`, claves, datos del seed de clientes
  ni volcados de base. Hay modelos gratis que pueden entrenar con lo enviado.
- **Cómo se verifica:** qué prueba concreta dice sí o no.

Comandos:

```bash
# [LAPTOP Bash] -> lo ejecuto yo
codex exec --cd "<ruta del worktree>" "Revisa el diff de HEAD contra origin/main. ¿Qué falla?"
opencode run --model opencode/deepseek-v4.1-flash-free "<tarea autocontenida>"
```

A Codex se le da el diff **sin contarle la intención**. Si le explicas qué
intentabas, te confirma tu propio sesgo en vez de romperlo.

## 5. Escribir el despacho en la ficha

Rellena el bloque **Despacho** del TEMPLATE con clase, motor, modelo,
motivo, qué se entrega y cómo se verifica. El motivo es la parte que
importa: dentro de un mes nadie recordará por qué.

Actualiza también el *frontmatter*: `clase`, `motor`, `modelo`.

## 6. Comprobar el presupuesto

Si es trabajo largo, mira la cuota de cada motor antes de lanzarlo y manda
el trabajo largo al que tenga la ventana semanal más holgada.

**Salvo en T4**: si no hay cuota de Opus, se espera. No hay plan B.

## Al terminar

Di en una línea: **clase, motor, modelo y el motivo**. Y si la clase es T4,
dilo explícitamente para que quede claro que no sale de aquí.
