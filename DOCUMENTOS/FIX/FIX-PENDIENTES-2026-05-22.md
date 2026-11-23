# Implementacion de pendientes (inicio)

Fecha: 2026-05-22

## Cambios implementados hoy (sin tocar Integraciones/Inventario)

### 1) Revisiones: exportar PDF desde el listado

Se agrego accion directa "PDF" en cada card de `/dashboard/security-reviews` para descargar sin entrar al detalle.

Archivo:
- `PY-MK/frontend/src/app/(admin)/dashboard/security-reviews/page.tsx`

### 2) Migracion Alembic de pendientes estructurales

Se creo migracion unica para cerrar pendientes documentados:
- `clients.city`
- `clients.country`
- `collaborator_profiles.area`
- `collaborator_profiles.photo_url`
- `services.price_label`
- `projects.budget_label`
- `devices.integration_id` nullable (inventario base)

Archivo:
- `PY-MK/backend/app/db/migrations/versions/20260522_01_pending_schema_updates.py`

## Pendientes siguientes recomendados

1. Leads: drag & drop real en Kanban (actualmente botones).
2. Reportes: persistir `lastRun` en backend (no localStorage).
3. Colaboradores: upload real de avatar (no solo URL).
4. CI: crear workflows ejecutables (test backend + build/lint frontend).
