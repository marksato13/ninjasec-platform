---
description: Dónde estoy ahora en NinjaSec — PR, CI, worktrees y trabajo sin commitear
---

Lee el estado real y reescribe `CORTEX/00-MAPA/Estado.md`. **No cambies
nada más.**

## 1. Recoger

```bash
# [LAPTOP Bash] -> lo ejecuto yo
cd "C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/EMPRESA NINJA-SEC"
git fetch --prune origin
gh pr list --author "@me" --json number,title,mergeable,headRefName
gh pr list --author app/dependabot --json number,title --jq 'length'
git worktree list
```

Para cada PR propio, su CI:

```bash
gh pr checks <numero>
```

Y para cada worktree, si tiene trabajo sin commitear:

```bash
git -C "<ruta>" status --short
```

## 2. Comprobar el atraso

`main` local se queda atrás. Compara siempre:

```bash
git rev-parse --short HEAD origin/main
git log --oneline HEAD..origin/main | wc -l
```

Si hay diferencia, dilo: ramificar del `main` local es heredar bugs ya
corregidos.

## 3. Escribir

Reescribe `CORTEX/00-MAPA/Estado.md` con la fecha de hoy y estas secciones:

- **Dónde estoy** — rama y worktree actuales, y sobre qué base
- **PR abiertos** — número, estado del CI, si es fusionable
- **Lo que está parado** — worktrees con cambios sin commitear, ramas ya
  fusionadas sin limpiar
- **Lo que bloquea el despliegue**
- **Decisión esperando a Mark**

## 4. Reportar

En el chat, **tres líneas como máximo**: qué está verde y listo, qué está
rojo, y qué está parado sin que nadie lo mire.

El detalle ya está en el archivo. No lo repitas.

## Lo que este comando no hace

No fusiona, no commitea, no crea ramas y no toca ningún PR. Solo mira y
escribe una página.
