# NinjaSec - Fase B - Permisos y hardening de auth

## Objetivo

Hacer que los datos queden correctamente aislados por organizacion y rol, y bloquear cuentas inactivas de forma centralizada.

## Cambios aplicados

### 1. Validacion de usuarios inactivos

- `get_current_user` ahora bloquea cuentas con `is_active = false` o `status != ACTIVE`.
- Respuesta: `403` con mensaje de cuenta inactiva.

Archivo:
- `backend/app/common/deps/auth.py`

### 2. Scoping por organizacion y rol en endpoints

Se aplico filtrado por `organization_id` y reglas por rol en los listados clave:

- `clients`: admin/collab ven solo su organizacion, client ve solo su empresa
- `projects`: admin ve su organizacion, collab ve proyectos donde es miembro, client ve los suyos
- `reports` y `report_runs`: admin/collab por organizacion, client por su empresa
- `integrations`: admin/collab por organizacion, client por su empresa
- `devices`: admin/collab por organizacion via integraciones, client por su empresa
- `collection/snapshots`: admin/collab por organizacion
- `audit-logs`: admin por organizacion
- `organizations`: admin solo su organizacion
- `users`: admin solo usuarios de su organizacion
- `service-requests`: admin solo solicitudes de servicios de su organizacion
- `collaborators`: admin solo perfiles de su organizacion

### 3. Controles en operaciones de escritura

En operaciones de creacion o eliminacion se valida que el `organization_id` coincide con el del usuario autenticado.

Ejemplos:

- crear usuarios, clientes, proyectos, reportes, integraciones, servicios
- eliminar clientes, proyectos, integraciones, servicios

## Estado de frontend

Los guards actuales ya validan roles:

- `dashboard` solo para admin/super_admin
- `portal` solo para client/collaborator

No se requirieron cambios en UI para completar esta fase.

## Siguiente paso recomendado

Iniciar la Fase C (sitio publico y captacion) o continuar con pruebas de seguridad basicas.
