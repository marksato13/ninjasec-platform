# FIX — Colaboradores: upload real de avatar

Fecha: 2026-05-22

## Objetivo

Pasar de "URL manual" a carga real de imagen para foto de colaborador.

## Implementacion

### Backend

1. Endpoint de upload por perfil:
- `POST /api/v1/collaborators/{profile_id}/photo`
- Archivo: `PY-MK/backend/app/modules/collaborators/routers/router.py`

Reglas:
- Roles permitidos: `super_admin`, `admin`, `collaborator`.
- `collaborator` solo puede subir su propia foto.
- Formatos permitidos: JPG, PNG, WEBP.
- Tamano maximo: 5MB.
- Guarda archivo en: `backend/app/static/uploads/collaborators/`.
- Actualiza `photo_url` del perfil con ruta ` /static/uploads/collaborators/... `.

2. Servir archivos estaticos desde backend:
- `app.mount("/static", StaticFiles(directory="app/static"), name="static")`
- Archivo: `PY-MK/backend/app/main.py`

3. Directorios creados:
- `PY-MK/backend/app/static/`
- `PY-MK/backend/app/static/uploads/`
- `PY-MK/backend/app/static/uploads/collaborators/`

### Frontend

1. API de colaboradores:
- Nueva funcion `uploadCollaboratorPhoto(profileId, file)` usando `FormData`.
- Archivo: `PY-MK/frontend/src/lib/api/collaborators.ts`

2. UI en modal de editar colaborador:
- Campo `input type=file` para subir imagen real.
- Estado de carga "Subiendo...".
- Al terminar, actualiza `photo_url`, cache y vista.
- Archivo: `PY-MK/frontend/src/app/(admin)/dashboard/collaborators/page.tsx`

3. Resolucion de URL de foto:
- Se agrego helper `resolvePhotoUrl()` para convertir rutas `/static/...` en URL completa cuando `NEXT_PUBLIC_API_URL` es absoluto.

## Resultado

- Ya existe upload real de avatar desde la pantalla de Colaboradores.
- Se mantiene compatibilidad con URL manual en `photo_url`.
- Se aplican restricciones de tipo/tamano y permisos por rol.
