---
description: Qué toca ahora en NinjaSec, priorizado por riesgo y no por orden de llegada
---

Decide qué es lo siguiente y actualiza `CORTEX/40-TAREAS/Tablero.md`.

## 1. Reunir el trabajo

De cuatro sitios, en este orden:

1. **PR abiertos propios** — `gh pr list --author "@me"`, con su CI.
2. **Pendientes `NN-P-NN` sin tachar** en
   `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-*.md`.
3. **Bloqueantes del despliegue** — están en `CORTEX/40-TAREAS/Tablero.md`.
4. **Worktrees con trabajo sin commitear** — `git worktree list` y
   `git -C <ruta> status --short`.

El orden del roadmap está en `DOCUMENTOS/PLATAFORMA/ROADMAP.md` y manda
sobre tu criterio cuando hay empate.

## 2. Priorizar por riesgo

No por orden de llegada. De más urgente a menos:

| Prioridad | Qué |
| --- | --- |
| 1 | Lo que **bloquea el despliegue público** |
| 2 | Lo que es **fuga de datos o fallo de seguridad** — clase T4 |
| 3 | Lo que está **verde y sin fusionar**: ya está pagado, solo falta cobrarlo |
| 4 | Lo que está **rojo** y bloquea a otra cosa |
| 5 | Lo que está **parado sin que nadie lo mire** — worktrees sin commitear |
| 6 | El resto del roadmap |

## 3. Clasificar

A cada entrada, su clase T0–T8 según
`CORTEX/10-ENRUTADO/Politica-de-enrutado.md`. Si no sabes clasificarla, la
ficha todavía no está lista: dilo.

## 4. Escribir

Actualiza `CORTEX/40-TAREAS/Tablero.md` con las secciones que ya tiene. No
inventes secciones nuevas.

## 5. Proponer

Al final, **una recomendación concreta**: el siguiente pendiente, su clase y
por qué ese y no otro. Luego pregunta si tira por ahí.

No arranques a implementar desde este comando. `/ns-inbox` mira y ordena;
`/ns-abrir` es el que empieza.
