---
name: ninjasec-puertas-ci
description: Las puertas del CI de NinjaSec y cómo replicarlas en local. Usar al verificar una entrega, antes de hacer commit o push, cuando un PR sale en rojo, o cuando haya que saber por qué falla backend-tests, frontend-build o alguno de los tres checks de seguridad.
---

# Puertas del CI de NinjaSec

El workflow `.github/workflows/ci.yml` corre en cada `pull_request` y en
cada push a `main` y `develop`. Son **tres jobs** que producen **cinco
checks obligatorios**, porque `security` es un workflow reutilizable y cada
herramienta publica el suyo.

## Los nombres exactos

```
Backend tests
Frontend build
Security / Gitleaks
Security / Semgrep CE
Security / Trivy filesystem
```

Protección en `main` y en `develop`: `strict: true` (la rama tiene que
estar al día con su base) y `allow_force_pushes: false`.

> **No escribas estos nombres de memoria.** Llevan barras y espacios
> exactos. Una vez se escribieron en ASCII, un `·` se convirtió en `?` y la
> rama quedó esperando un check que no iba a existir nunca. Si hay que
> tocarlos, se leen de la API:
> `gh api repos/marksato13/ninjasec-platform/branches/main/protection --jq '.required_status_checks.contexts'`

## Puerta 1 — Backend tests

```bash
cd PY-MK/backend
PYTHONPATH=. pytest -q
```

En CI se levanta `postgres:16-alpine` con la base
`ninjasec_migrations_test` y se pasa `ALEMBIC_TEST_DATABASE_URL`: hay
pruebas que **aplican las migraciones de verdad** contra un catálogo real.
`test_alembic_bootstrap` es la que caza que los índices de una migración no
estén también en los modelos.

El `JWT_SECRET_KEY` se genera al vuelo con `openssl rand -hex 32`. No hay
secreto de CI que pueda filtrarse.

## Puerta 2 — Frontend build

```bash
cd PY-MK/frontend
npm ci
npm audit --audit-level=critical
NEXT_PUBLIC_API_URL=/api/v1 npm run build
```

`npm audit` **bloquea en crítico**. Dos avisos ganados a pulso:

- Si lees su resultado desde PowerShell, **lee el JSON**. Una tubería con
  `Select-Object` contamina el código de salida: ya dio un verde con una
  vulnerabilidad crítica dentro.
- `npm ci` exige que `package-lock.json` esté al día con `package.json`.

## Puerta 3 — Security (tres checks)

| Check | Qué caza |
| --- | --- |
| `Security / Gitleaks` | Secretos en el **historial completo**, no solo en el diff |
| `Security / Semgrep CE` | Patrones inseguros en el código |
| `Security / Trivy filesystem` | CVE en dependencias |

En local, lo que sí se puede correr:

```bash
gitleaks protect --staged --no-banner --redact
```

Semgrep y Trivy solo corren en CI. **Dilo así en el informe**; no los
declares verdes.

Gitleaks mira el historial: un secreto commiteado y luego borrado en otro
commit **sigue estando ahí**. Por eso el escaneo va antes del commit.

## Lo que añade el PR #128, cuando entre

```
e2e              Playwright contra el stack en Docker
contrato-api     oasdiff sobre el OpenAPI exportado
```

Mientras ese PR siga abierto no son obligatorios, y no se declaran.

## La trampa de la dependencia circular

En noviembre dos arreglos se bloquearon mutuamente: el de PyJWT no pasaba
`Frontend build` por el Next vulnerable que había en `main`, y el de Next no
pasaba Trivy por el PyJWT vulnerable.

**La salida correcta fue unir los dos arreglos en una sola rama** para que
el CI pasara de verdad. No `--admin`, no saltarse la puerta. Si vuelve a
pasar, ese es el patrón.

## Cómo se reporta

Una línea por check, con el resultado real, y **diciendo cuáles no se
ejecutaron y por qué**:

```
Backend tests               OK (63 pruebas, 0 fallos)
Frontend build              OK
npm audit                   OK (0 críticas)
Security / Gitleaks         OK
Security / Semgrep CE       no ejecutada en local - solo corre en CI
Security / Trivy filesystem no ejecutada en local - solo corre en CI
```

Nunca declares en verde una puerta que no corriste.

## Si el PR ya está en rojo

```bash
gh pr checks <numero>
gh run view <run-id> --log-failed
```

Se corrige **en la misma rama**. Un pendiente es un solo PR.
