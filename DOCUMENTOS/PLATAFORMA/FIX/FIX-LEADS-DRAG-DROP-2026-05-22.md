# FIX — Leads Kanban con drag & drop

Fecha: 2026-05-22

## Objetivo

Cerrar pendiente del modulo Leads: permitir mover cards entre columnas con drag & drop, respetando transiciones validas del pipeline.

## Implementacion

Archivo modificado:
- `PY-MK/frontend/src/app/(admin)/dashboard/leads/page.tsx`

Cambios aplicados:

1. Estados nuevos de UI para DnD:
- `dragLeadId`
- `dragOverColumn`

2. Soporte drag en cada card:
- `draggable={isAdmin}`
- `onDragStart` / `onDragEnd`

3. Soporte drop en cada columna:
- `onDragOver`
- `onDragEnter`
- `onDragLeave`
- `onDrop`

4. Validacion de transiciones al soltar:
- Se reutiliza `TRANSITIONS`.
- Solo mueve si `toStatus` esta permitido desde el estado actual.
- Si no esta permitido, no hace cambio.

5. Feedback visual:
- Columna destino se resalta con borde punteado.
- Card arrastrada se muestra con opacidad reducida.

## Resultado

- Ya existe movimiento real por drag & drop en el Kanban de Leads.
- Se mantiene la regla de negocio de transiciones permitidas.
- No se rompe el flujo actual por botones (ambos metodos siguen funcionando).
