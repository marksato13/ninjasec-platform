# Puertas de CI

Lo que corre en cada PR, y su equivalente en local. Abrir un PR sin pasar
esto es gastar un PR en rojo.

Estado del workflow en `origin/main` al **2026-11-22**.

## Lo que corre hoy

```
backend-tests    pytest con PostgreSQL 16 real
frontend-build   npm ci + npm audit --audit-level=critical + npm run build
security         reusable -> Gitleaks + Semgrep CE + Trivy filesystem
```

Los tres producen **cinco** checks obligatorios, porque `security` es un
workflow reutilizable y cada herramienta publica el suyo:

```
Backend tests
Frontend build
Security / Gitleaks
Security / Semgrep CE
Security / Trivy filesystem
```

## Lo que añade el PR #128, cuando entre

```
e2e              Playwright contra el stack en Docker
contrato-api     oasdiff sobre el OpenAPI exportado
```

Mientras ese PR siga abierto, no son obligatorios. **No los declares verdes
si no corrieron.**

## Puerta 1 — backend

```bash
# [LAPTOP Bash] -> lo ejecuto yo
cd PY-MK/backend
PYTHONPATH=. pytest -q
```

En CI se levanta `postgres:16-alpine` con la base
`ninjasec_migrations_test` y se pasa `ALEMBIC_TEST_DATABASE_URL`, porque hay
pruebas que **aplican las migraciones de verdad** contra un catálogo real.
Ahí es donde se cazó que había 23 índices en la migración y ninguno en los
modelos.

El `JWT_SECRET_KEY` se genera al vuelo con `openssl rand -hex 32`. No hay
secreto de CI que filtrar.

## Puerta 2 — frontend

```bash
# [LAPTOP Bash] -> lo ejecuto yo
cd PY-MK/frontend
npm ci
npm audit --audit-level=critical
NEXT_PUBLIC_API_URL=/api/v1 npm run build
```

**`npm audit` es bloqueante en crítico.** Y una advertencia ganada a pulso:
no leas su código de salida a través de una tubería de PowerShell —
`Select-Object` lo contamina y da un falso verde. Lee el JSON.

## Puerta 3 — seguridad

Tres herramientas, tres checks:

| Check | Qué caza |
| --- | --- |
| `Security / Gitleaks` | Secretos en el historial |
| `Security / Semgrep CE` | Patrones inseguros en el código |
| `Security / Trivy filesystem` | CVE en dependencias |

En local, lo mínimo antes de commitear:

```bash
# [LAPTOP Bash] -> lo ejecuto yo
gitleaks protect --staged --no-banner --redact
```

Trivy es el que bloqueó la cadena circular de noviembre: el arreglo de PyJWT
no pasaba `frontend-build` por el Next vulnerable de `main`, y el de Next no
pasaba Trivy por el PyJWT vulnerable. **La salida fue unir los dos arreglos
en una rama**, no saltarse la puerta con `--admin`.

## Cómo se reporta

Una por una, y **diciendo cuáles no se ejecutaron y por qué**:

```
Backend tests              OK (63 pruebas)
Frontend build             OK
Security / Gitleaks        OK
Security / Semgrep CE      no ejecutada en local - solo corre en CI
Security / Trivy filesystem no ejecutada en local - solo corre en CI
```

Nunca declares en verde una puerta que no corriste. Es la regla que más
veces ha evitado una entrega falsa en este repo.

## Si el PR ya está en rojo

```bash
# [LAPTOP Bash] -> lo ejecuto yo
gh pr checks <numero>
gh run view <run-id> --log-failed
```

Se corrige en la misma rama y se vuelve a subir. Un pendiente es un solo PR.

Ver también: [[Ciclo-de-vida]] · [[Automatizaciones]]
