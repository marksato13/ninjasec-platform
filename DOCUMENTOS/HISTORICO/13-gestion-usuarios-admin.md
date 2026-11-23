# NinjaSec - Gestion de usuarios (Admin)

## Objetivo

Permitir administracion completa de usuarios con edicion, eliminacion, filtros y auditoria basica.

## Funcionalidades

- edicion de nombre, cargo y estado activo
- eliminacion con confirmacion
- cargos predefinidos con opcion "Otro"
- filtros por rol, estado, texto libre
- filtros por fecha de creacion y actualizacion
- visualizacion de fechas de creacion y actualizacion

## Archivos clave

- `backend/app/modules/users/schemas/user.py`
- `frontend/src/app/(admin)/dashboard/users/page.tsx`
- `frontend/src/components/forms/user-form.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/constants.ts`
