# Instrucciones para agentes

Este archivo gobierna todo el repositorio. Para cualquier cambio dentro de
`PY-MK/`, leer además [`PY-MK/CLAUDE.md`](PY-MK/CLAUDE.md) completamente.

## Fuentes de verdad

1. `DOCUMENTOS/PLATAFORMA/PLANIFICACION/NN-*.md`: requisitos del módulo.
2. `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-*.md`: checklist y evidencia.
3. `DOCUMENTOS/PLATAFORMA/ROADMAP.md`: orden de trabajo.
4. `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/00-BACKLOG-GLOBAL.md`: inventario.

`tash/` es material histórico y nunca prevalece sobre esas fuentes.

## Flujo obligatorio

1. Trabajar en una rama y worktree propios; nunca directamente en `main`.
2. Antes de editar, identificar el pendiente `NN-P-NN` y sus criterios.
3. Un agente modifica únicamente los archivos asignados a su subtarea.
4. Backend, tests y documentación se separan cuando puedan ejecutarse en
   paralelo sin tocar los mismos archivos.
5. Ejecutar las pruebas proporcionales al cambio y registrar el resultado.
6. Actualizar el checklist de implementación con evidencia verificable.
7. Abrir un Pull Request; el merge requiere autorización humana explícita.

## Comandos de verificación

Backend:

```bash
cd PY-MK/backend
PYTHONPATH=. pytest -q
```

Frontend:

```bash
cd PY-MK/frontend
npm ci
NEXT_PUBLIC_API_URL=/api/v1 npm run build
```

Secretos:

```bash
gitleaks protect --staged --no-banner --redact
```

## Reglas de seguridad

- Nunca leer, mostrar, registrar ni versionar `.env`, tokens, cookies o claves.
- No usar credenciales seed fuera de entornos locales desechables.
- Toda ruta protegida valida rol y `organization_id`; datos de otro tenant
  devuelven 404 para no confirmar su existencia.
- Toda mutación crítica registra auditoría mediante `AuditService`.
- No ejecutar `DELETE`, `DROP`, `docker compose down -v` ni migraciones sobre
  una base con datos sin autorización y respaldo comprobado.
- No iniciar `28-P3` ni `30-P6` sin cumplir sus puertas de seguridad.
- No activar despliegues, modelos de pago ni servicios públicos por inferencia.

## Convenciones

- Documentación, UI, comentarios y commits: español.
- Identificadores de código: inglés.
- No quitar los dos rewrites de `frontend/next.config.ts`.
- No quitar `from __future__ import annotations` de servicios con `def list`.
- Frontend usa el cliente API, query keys y alertas existentes; nunca `alert()`
  ni `window.confirm`.
- Un pendiente resuelto se tacha con evidencia; nunca se borra del historial.

## Estado conocido

- Línea base al 2026-08-07: 63 pruebas backend pasan.
- El frontend compila 41 rutas con warnings de lint existentes.
- Alembic G-01/G-02 sigue bloqueando despliegue self-hosted.
- La siguiente funcionalidad del roadmap es 23-P1, UI de topología.
