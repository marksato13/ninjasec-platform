# Worktrees — un árbol por tarea

`AGENTS.md` lo exige: *«Trabajar en una rama y worktree propios; nunca
directamente en `main`»*. Esta página dice cómo, y qué trampas tiene en esta
máquina.

## La convención que ya está en uso

Los worktrees son **hermanos** de la carpeta del repo, en
`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\`, y se llaman
`ninjasec-wt-<tema>`:

```
EMPRESA NINJA-SEC/          <- el principal, en main. No se trabaja aquí
ninjasec-wt-bd/             <- fix/indices-y-slug-servicios
ninjasec-wt-qa/             <- feat/qa-playwright
ninjasec-wt-tenant/         <- fix/fuga-multitenant
...
```

El `<tema>` es corto y recordable, no el id del pendiente: varios pendientes
de la misma área comparten árbol mientras no estén en vuelo a la vez.

## Crear uno

```bash
# [LAPTOP Bash] -> lo ejecuto yo
cd "C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/EMPRESA NINJA-SEC"
git fetch --prune origin
git worktree add "../ninjasec-wt-<tema>" -b <tipo>/<slug> origin/main
```

**Siempre desde `origin/main`, nunca desde el `main` local.** El `main`
local se queda atrás: al escribir esto estaba en `932b1eb` mientras
`origin/main` iba por `5ea9892`, **19 commits por delante**. Ramificar del
local es heredar bugs ya corregidos.

Tipos de rama, según `AGENTS.md` y lo que ya hay en el remoto:
`feature/`, `fix/`, `chore/`, `docs/`, `hotfix/`. **No hay `release/`**, y
es deliberado.

## Cerrar uno

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git worktree remove "../ninjasec-wt-<tema>"
git worktree prune
```

Antes de borrar la rama, comprobar que su contenido está integrado. Con
`git cherry`, que compara por **contenido** y no por SHA —un *squash merge*
cambia el SHA y `git log` miente:

```bash
git cherry origin/main origin/<rama>     # un '+' = commit NO integrado
```

No uses `git diff origin/main...origin/<rama>`: eso muestra lo que la rama
aportó desde el punto de divergencia, no lo que falta en `main`.

## La trampa de los árboles abandonados

Al escribir esto había **18 worktrees vivos**, varios con ramas ya
fusionadas y uno con trabajo sin commitear que llevaba días ahí
(`ninjasec-wt-payload`, los ocho `VARCHAR` → `TEXT`).

Un worktree abandonado no avisa. Lo único que lo caza es mirar:

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git worktree list
```

`CORTEX/herramientas/estado.ps1` lo incluye en su salida por eso mismo.

## Lo que nunca se hace en un worktree

`git stash`, `git reset --hard`, `git clean` y `git restore` destruyen
trabajo que puede no ser tuyo. Si `git status` muestra cambios que no son de
tu tarea: **detente y repórtalos**. No los descartes.

Ver también: [[Ciclo-de-vida]] · [[Puertas-de-CI]]
