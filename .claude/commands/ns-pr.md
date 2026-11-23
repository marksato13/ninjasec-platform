---
description: Commit, push y PR de un pendiente de NinjaSec, con el checklist de implementación tachado
argument-hint: 12-P-03
---

Entrega **$1**. Solo se llega aquí con `/ns-verificar` en verde.

## 1. Comprobar antes de tocar nada

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git status --short --branch
git diff --check
```

- Si hay archivos que no son de **$1**, detente y repórtalos.
- Si aparece `.env`, un secreto, una caché o un log: detente. No lo
  commitees y no lo borres sin avisar.
- Si la rama está atrás de `origin/main`, actualízala: la protección es
  `strict: true` y una rama desactualizada no se fusiona.

## 2. Tachar el pendiente con evidencia

En `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-*.md`, el pendiente **$1** se
tacha y se le añade la evidencia: archivo y línea, prueba que lo cubre, o
salida del comando.

**Nunca se borra la línea.** Es la regla del repo y lo que permite leer el
historial dentro de un año.

## 3. Commit

Mensaje en español, con el id del pendiente. El cuerpo explica **por qué**,
no qué —el qué ya está en el diff— y declara qué se verificó y qué no.

Termina con las líneas de atribución que corresponda.

```bash
# [LAPTOP Bash] -> lo ejecuto yo
gitleaks protect --staged --no-banner --redact
git commit
```

El escaneo de secretos va **antes** del commit, no después. Gitleaks mira el
historial completo en CI: un secreto commiteado y luego borrado sigue ahí.

## 4. Push y PR

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git push -u origin <rama>
gh pr create --base main --title "<tipo>(<ámbito>): <qué>" --body-file <archivo>
```

El cuerpo del PR dice, separado:

- **Qué cambia y por qué.**
- **Qué se verificó**, con el resultado real.
- **Qué NO se verificó**, con el motivo.
- **Riesgos** y qué vigilar después del merge.

## 5. Esperar el CI de verdad

```bash
# [LAPTOP Bash] -> lo ejecuto yo
gh pr checks <numero> --watch
```

Los cinco checks obligatorios, con su nombre exacto:

```
Backend tests
Frontend build
Security / Gitleaks
Security / Semgrep CE
Security / Trivy filesystem
```

## 6. Merge

Con los cinco en verde, el merge de un PR propio está autorizado desde el
2026-11-20.

**Nunca con `--admin`.** Si un check bloquea, se arregla la causa. Cuando
dos PR se bloquearon en círculo —PyJWT frente a Next— la salida fue unir los
dos arreglos en una rama para que el CI pasara de verdad, no saltárselo.

Después del merge, actualiza la ficha con el número de PR y el estado, y
limpia el worktree si ya no hace falta:

```bash
# [LAPTOP Bash] -> lo ejecuto yo
git cherry origin/main origin/<rama>      # un '+' = commit NO integrado
git worktree remove "../ninjasec-wt-<tema>"
```

## Lo que sigue siendo de Mark

Exponer al público, rotar G-03, crear cuentas y gastar dinero. Ver
`CORTEX/30-CICLO/Frontera-de-autonomia.md`.
