# PY-MK · la aplicación

Backend FastAPI, frontend Next.js e infraestructura Docker de NinjaSec.

La descripción del proyecto, cómo se trabaja y cómo levantarlo está en el
[README de la raíz](../README.md). Aquí solo lo que es propio de esta carpeta.

## Estructura

```
PY-MK/
├── backend/        FastAPI · modular monolith
│   ├── app/
│   │   ├── api/        router central
│   │   ├── core/       config, seguridad, cápsulas, navegación
│   │   ├── common/     dependencias compartidas
│   │   ├── db/         modelos, migraciones (Alembic), seeds de contenido
│   │   └── modules/    un módulo por funcionalidad
│   └── tests/
├── frontend/       Next.js (App Router)
│   └── src/
│       ├── app/        rutas: públicas, panel (/dashboard) y portal (/portal)
│       ├── components/
│       └── lib/        cliente de la API, autenticación, claves de consulta
├── infra/          Docker Compose (dev y producción), Caddy, respaldos, despliegue continuo
├── ARQUITECTURA/   diagramas y decisiones
└── docs/           documentación funcional y de despliegue
```

## Comandos

```bash
# Backend: pruebas
cd backend && PYTHONPATH=. pytest -q

# Frontend: compilar
cd frontend && npm ci && NEXT_PUBLIC_API_URL=/api/v1 npm run build

# Todo el stack
cd infra && docker compose -p ninjasec up -d --build
```

## Reglas que no se rompen

1. **`docker compose -p ninjasec`**: el nombre del proyecto no es opcional.
2. **Los dos *rewrites* de `frontend/next.config.ts`** no se quitan: arreglan un bucle de redirecciones que rompía todos los módulos.
3. **`from __future__ import annotations`** en los servicios con un método `list`.
4. **Multi-tenant:** todo dato de negocio lleva `organization_id`; los de otra organización devuelven 404.
5. **Nada de credenciales en el repositorio.** Los `.env` no se versionan.

Guía completa para quien trabaje en el código: [`CLAUDE.md`](CLAUDE.md).
Despliegue: [`DEPLOY.md`](DEPLOY.md) e [`infra/`](infra/).
