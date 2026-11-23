# Reporte de cambios recientes

## Alcance

Cambios en UI/UX del backoffice y portal, estandarizacion visual de cards, roles y sidebar.

## Cambios realizados

### Sidebar y navegacion

- Sidebar mas estrecho con header integrado.
- Iconos con contenedor dedicado (`nav-item-icon-wrap`).
- Estados hover/active con mejor contraste.

Archivos:
- `frontend/src/components/dashboard/sidebar.tsx`
- `frontend/src/components/dashboard/portal-sidebar.tsx`
- `frontend/src/app/globals.css`

### Cards en admin (usuarios, clientes, colaboradores)

- Reemplazo de tablas por cards con avatar y badges.
- Avatares con iniciales y color dinamico.
- Roles/estados estandarizados con helpers compartidos.

Archivos:
- `frontend/src/app/(admin)/dashboard/users/page.tsx`
- `frontend/src/app/(admin)/dashboard/clients/page.tsx`
- `frontend/src/app/(admin)/dashboard/collaborators/page.tsx`
- `frontend/src/lib/role-utils.ts`
- `frontend/src/app/globals.css`

### UX y responsive

- Ajustes de padding, radios, y espaciado global.
- Grid de cards responsive (2-4 columnas, 1 en mobile).

Archivos:
- `frontend/src/app/globals.css`

## Estado actual visible

- `/dashboard/users` con cards, avatar y badges de rol/estado.
- `/dashboard/clients` con cards y estado comercial.
- `/dashboard/collaborators` con cards, disponibilidad y skills.

## Pendientes principales

- UI de proyectos en cards + detalle por rol.
- Modales o ventanas emergentes (si se aprueba libreria).
- Alertas/toasts con libreria sugerida.
