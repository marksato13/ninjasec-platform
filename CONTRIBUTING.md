# Cómo contribuir

Gracias por sumarte. Este repositorio es **público**: no subas datos reales de
clientes, credenciales ni volcados de base de datos, ni en código, ni en
capturas, ni en issues.

## Antes de empezar

1. Lee [`AGENTS.md`](AGENTS.md): son las reglas del proyecto y mandan sobre todo
   lo demás.
2. Lee [`README.md`](README.md) para saber qué hace la plataforma hoy, y
   [`PY-MK/CLAUDE.md`](PY-MK/CLAUDE.md) para la arquitectura y las convenciones.
3. Acuerda la tarea con el mantenedor antes de escribir código, y comprueba que
   no haya ya un PR abierto para lo mismo:
   `gh pr list --repo marksato13/ninjasec-platform`.

## Entorno local

```bash
git switch develop
cd PY-MK/infra
cp .env.example .env      # valores propios; .env nunca se versiona
docker compose -p ninjasec up -d --build
```

Web en <http://localhost:3018>, API en <http://localhost:8024/docs>. Las
credenciales de la siembra solo valen en tu entorno local.

## Flujo (GitFlow)

| Paso | Regla |
| --- | --- |
| Rama | Desde `develop`: `feature/<slug>`, `fix/<slug>`, `docs/<slug>` o `chore/<slug>`. El CI rechaza otros nombres |
| Commits | En español: `tipo(ámbito): descripción`, p. ej. `fix(tickets): orden por prioridad` |
| PR | Contra `develop`, una incidencia por PR, con la verificación pegada |
| Fusión | La hace el mantenedor. `main` y `develop` no aceptan push directo |
| Publicación | `develop → main` la hace el mantenedor; producción se actualiza sola |

## Verificación que se pega en el PR

Cada puerta se reporta como **pasó**, **falló** o **no se ejecutó (y por qué)**,
con la salida real ([detalle en `AGENTS.md`](AGENTS.md#reporte-de-verificación-tres-estados-nunca-dos)).

```bash
cd PY-MK/backend && PYTHONPATH=. pytest -q
cd PY-MK/frontend && npm ci && NEXT_PUBLIC_API_URL=/api/v1 npm run build
gitleaks protect --staged --no-banner --redact
```

## Reglas de código que más se olvidan

- Toda ruta protegida valida **rol** y **`organization_id`**; lo que no le
  corresponde a quien pregunta devuelve **404**, no 403.
- Toda mutación crítica se registra con `AuditService`.
- Cambios de base de datos solo con una migración de Alembic nueva y probada
  (sube, baja y vuelve a subir).
- Frontend: el cliente API, las query keys y las alertas existentes; nunca
  `alert()` ni `window.confirm`.
- Textos, comentarios y commits en español; identificadores en inglés.

## Si usas un asistente de IA

Dale primero `AGENTS.md` y `PY-MK/CLAUDE.md`. Claude Code los carga solo al
abrirse en la raíz del repo (vía [`CLAUDE.md`](CLAUDE.md)). Pídele que te diga
qué archivos va a tocar y cómo lo va a verificar **antes** de editar, y revisa
tú el diff: el PR es tuyo.

Autenticación, `organization_id`, migraciones y secretos se tocan solo con
acuerdo previo del mantenedor.
