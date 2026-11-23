---
description: Abre un pendiente de NinjaSec — worktree, rama desde origin/main y ficha en CORTEX
argument-hint: 12-P-03
---

Prepara el trabajo de **$1**. Ejecuta en orden y **detente en el primero que
falle**.

## 1. Confirmar que el pendiente existe

Búscalo en `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-*.md`. Si no aparece
tal cual, **detente**: el id puede estar mal o el pendiente ya estar tachado.

Lee sus criterios y su módulo. Lee también el `PLANIFICACION/NN-*.md`
correspondiente si existe: ahí está el requisito, no solo el checklist.

## 2. Proteger el trabajo ajeno

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git worktree list
```

Si ya hay un worktree de esa área con cambios sin commitear, **úsalo o
repórtalo**; no abras otro encima. Hoy hay 16 árboles vivos y uno de ellos
lleva días con trabajo sin guardar.

## 3. Actualizar y ramificar

```bash
# [LAPTOP Bash] -> lo ejecuto yo
cd "C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/EMPRESA NINJA-SEC"
git fetch --prune origin
git worktree add "../ninjasec-wt-<tema>" -b <tipo>/<slug> origin/main
```

**Desde `origin/main`, nunca desde el `main` local**, que se queda atrás.

Tipos: `feature/`, `fix/`, `chore/`, `docs/`, `hotfix/`. No hay `release/`.

El `<tema>` del worktree es corto y recordable; el `<slug>` de la rama sale
del título del pendiente, en minúsculas y con guiones.

## 4. Escribir la ficha

Crea `CORTEX/40-TAREAS/$1-<slug>.md` desde
`CORTEX/40-TAREAS/TEMPLATE.md`. Obligatorio:

- El *frontmatter* completo: `pendiente`, `rama`, `worktree`, `estado`.
- Los criterios numerados `CA-1`, `CA-2`… descompuestos de lo que dice el
  checklist, uno por uno y verificables.
- Los tres bloques: **hechos auditados** con evidencia `archivo:línea`,
  **supuestos** con quién los confirma, **decisiones pendientes** con quién
  decide.
- **Fuera de alcance explícito.**
- La tabla de aislamiento multi-tenant, si toca alguna ruta.

Si quedan decisiones abiertas que afectan al diseño, el plan técnico se
queda como *«sin definir»*: **no se programa con criterios ambiguos.**

Para auditar el estado real del código antes de escribir los hechos, usa el
subagente `ns-explorador`. Es barato y es exactamente para esto.

## 5. Dejarlo listo para despachar

Al terminar, resume: worktree y rama creados, ficha escrita, qué decisiones
quedan abiertas, y si se puede pasar a `/ns-despachar $1` o hay que cerrar
algo antes.

No empieces a implementar desde aquí.
