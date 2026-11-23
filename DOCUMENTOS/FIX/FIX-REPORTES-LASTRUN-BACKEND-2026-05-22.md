# FIX — Reportes: lastRun persistido en backend

Fecha: 2026-05-22

## Objetivo

Eliminar la dependencia de `localStorage` para mostrar "Ultimo" en cards de reportes y usar datos persistidos de servidor.

## Implementacion

### Backend

Se agrego endpoint nuevo:
- `GET /api/v1/reports/last-exports`

Archivo:
- `PY-MK/backend/app/modules/reports/routers/router.py`

Que devuelve:
- Mapa `{ tipo_reporte: iso_datetime | null }` por organizacion.

Tipos soportados en esta version:
- `consolidated`
- `devices`
- `tickets`
- `reviews`
- `review-pdf`
- `pipeline`

Fuente de verdad:
- `audit_logs` por acciones de exportacion ya registradas (`*.export*`).

### Frontend API

Archivo:
- `PY-MK/frontend/src/lib/api/reports.ts`

Cambios:
- Tipo `LastExportsMap`
- Funcion `getLastExports()`

### Frontend UI reportes

Archivo:
- `PY-MK/frontend/src/app/(admin)/dashboard/reports/page.tsx`

Cambios:
- Se elimino lectura/escritura de `localStorage` para last run.
- Se consume `getLastExports()` con React Query.
- `trackExport()` actualiza cache en memoria para feedback inmediato en la vista.

## Resultado

- "Ultimo" en cards de reportes ya sale del backend (persistente por organizacion).
- Se mantiene UX inmediata tras exportar (actualizacion optimista de cache).
