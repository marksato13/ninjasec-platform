# Actualizaciones UI usuarios (referencia a docs/21)

Referencia: `docs/21-reporte-librerias-plan.md`

## Implementado

- Vista `/dashboard/users` mas profesional y responsive con cards y acciones.
- Boton **Ver** que abre modal con detalle del usuario.
- Ajuste global de `split-grid` para evitar espacios vacios cuando hay un solo panel.

## Cambios clave

- `frontend/src/app/(admin)/dashboard/users/page.tsx`
  - Nuevo modal de detalle.
  - Accion adicional "Ver" en tarjetas.
- `frontend/src/app/globals.css`
  - `split-grid` ahora usa `repeat(auto-fit, minmax(320px, 1fr))` para ocupar todo el ancho disponible.

## Pendiente sugerido

- Replicar modal de detalle en otros modulos (clientes, colaboradores, proyectos).
- Ajustar botones destructivos para consistencia visual en todas las cards.
- Revisar layout de paneles en modulos con 2 columnas para confirmar que el nuevo split-grid mantiene el balance visual.
