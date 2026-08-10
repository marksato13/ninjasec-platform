# Implementación — Roles y Accesos

> Basado en: `DOCUMENTOS/PLATAFORMA/01-ROLES-Y-ACCESOS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

| # | Regla del documento | Estado | Archivos |
|---|---------------------|--------|----------|
| 1 | Collaborator accede al backoffice `/dashboard` | ✅ | `frontend/.../dashboard-guard.tsx` |
| 2 | Collaborator ve menú reducido (sin Leads, Reportes, Usuarios, Config) | ✅ | `frontend/.../sidebar.tsx` |
| 3 | Dashboard KPI solo visible para admin/super_admin | ✅ | `frontend/.../sidebar.tsx` (adminOnly) |
| 4 | Auditoria solo visible para super_admin en el menú | ✅ | `frontend/.../sidebar.tsx` (isSuperAdmin) |
| 5 | Eliminar usuario: solo super_admin (backend) | ✅ | `backend/.../users/routers/router.py` |
| 6 | Eliminar usuario: botón solo visible para super_admin (frontend) | ✅ | `frontend/.../users/page.tsx` |
| 7 | Cambiar rol: solo super_admin (backend) | ✅ | `backend/.../users/schemas/user.py` + `router.py` |
| 8 | Cambiar rol: selector solo visible para super_admin (frontend) | ✅ | `frontend/.../users/page.tsx` |
| 9 | Cliente redirigido a `/portal` (no `/dashboard`) | ✅ | `frontend/.../dashboard-guard.tsx` |
| 10 | Colaborador redirigido a `/portal` si accede sin auth | ✅ | `frontend/.../dashboard-guard.tsx` |
| 11 | JWT expiry chequeado en el cliente antes de cada request | ✅ | `frontend/.../lib/auth.ts` + `client.ts` + `dashboard-guard.tsx` + `portal-shell.tsx` + `login-form.tsx` |
| 12 | Admin no puede editar super_admin ni a otros admin | ✅ | `backend/.../users/routers/router.py` (guards 403 en `update_user`) |
| 13 | DELETE de usuario requiere tipear el email para confirmar | ✅ | `frontend/.../lib/alerts.ts` (`confirmDeleteStrict`) + `users/page.tsx` |

---

## Matriz aplicada en el sidebar

| Módulo en menú | super_admin | admin | collaborator |
|----------------|:-----------:|:-----:|:------------:|
| Dashboard KPI  | ✅ | ✅ | ❌ (adminOnly) |
| Proyectos      | ✅ | ✅ | ✅ |
| Integraciones  | ✅ | ✅ | ✅ (solo ver) |
| Dispositivos   | ✅ | ✅ | ✅ |
| Revisiones     | ✅ | ✅ | ✅ |
| Tickets        | ✅ | ✅ | ✅ |
| Clientes       | ✅ | ✅ | ✅ (solo ver) |
| Colaboradores  | ✅ | ✅ | ✅ (solo ver) |
| Leads          | ✅ | ✅ | ❌ (adminOnly) |
| Servicios      | ✅ | ✅ | ❌ (adminOnly) |
| Usuarios       | ✅ | ✅ | ❌ (grupo oculto) |
| Postulaciones  | ✅ | ✅ | ❌ (grupo oculto) |
| Reportes       | ✅ | ✅ | ❌ (grupo oculto) |
| Aprobaciones   | ✅ | ✅ | ❌ (grupo oculto) |
| Auditoria      | ✅ | ❌ | ❌ (isSuperAdmin) |
| Configuracion  | ✅ | ✅ | ❌ (grupo oculto) |

---

## Archivos modificados

### Frontend

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/dashboard/dashboard-guard.tsx` | Agregado `DASHBOARD_ROLES = ["super_admin", "admin", "collaborator"]`; cliente redirige a `/portal`; rol desconocido redirige a `/login`. Chequeo `isTokenExpired()` antes de validar sesión |
| `frontend/src/components/dashboard/sidebar.tsx` | Reestructurado `navGroups` con campo `staffAllowed` por grupo y `adminOnly` por item; `Colaboradores` movido al grupo `commercial` para que collaborators lo vean |
| `frontend/src/components/dashboard/portal-shell.tsx` | Chequeo `isTokenExpired()` antes de cargar el portal del cliente |
| `frontend/src/components/dashboard/login-form.tsx` | Lee `?expired=1` y muestra banner "Tu sesión expiró" |
| `frontend/src/lib/auth.ts` | Helpers `getTokenExpiry()` e `isTokenExpired()` (decodifica payload JWT, compara `exp` contra `Date.now()`) |
| `frontend/src/lib/api/client.ts` | `request()` aborta y redirige a `/login?expired=1` si el token está expirado antes de hacer fetch |
| `frontend/src/lib/alerts.ts` | Nuevo `confirmDeleteStrict({ expected })` con input que requiere tipear el valor exacto |
| `frontend/src/app/(admin)/dashboard/users/page.tsx` | `handleDelete()` usa `confirmDeleteStrict` con `expected = user.email` (doble confirmación) |

### Backend

| Archivo | Cambio |
|---------|--------|
| `backend/app/modules/users/schemas/user.py` | Agregado `role_code: str \| None` a `UserUpdate` |
| `backend/app/modules/users/routers/router.py` | Lógica de cambio de rol: verifica `super_admin` antes de aplicar; busca `Role` por code y actualiza `role_id` + `role_code`. Admin no puede editar a super_admin (403) ni a otros admin (403) — sólo a sí mismo y a roles inferiores |

---

## Pendientes / No implementados

| # | Regla | Razón |
|---|-------|-------|
| ~~01-P-01~~ | ~~Collaborator ve solo revisiones/proyectos asignados~~ | ✅ **Implementado**: revisiones → `reviewer_user_id == current_user.id`; proyectos → join con `ProjectMember.user_id == current_user.id`. También colaboradores solo pueden editar su propio perfil (`403` si no es el dueño). |
| ~~01-P-02~~ | ~~JWT expira en 24h — cliente valida antes de llamar API~~ | ✅ **Implementado**: `isTokenExpired()` decodifica el payload JWT y compara `exp` contra `Date.now()`. Se chequea (1) antes de cada fetch en `client.ts`, (2) al montar `DashboardGuard` y (3) al montar `PortalShell`. Si expiró → `clearSession()` + redirect a `/login?expired=1`; el login muestra banner amarillo "Tu sesión expiró". |
| ~~01-P-03~~ | ~~Admin no puede cambiar rol de otro admin ni del super_admin~~ | ✅ **Implementado**: en `PUT /users/{id}` el backend ahora bloquea con 403 cuando `current_user.role == 'admin'` intenta editar un super_admin, y bloquea con 403 cuando intenta editar a otro admin distinto de sí mismo. Verificado vía pruebas: admin→super_admin=403, admin→other_admin=403, admin→self=200, admin→collaborator=200. |
| ~~01-P-04~~ | ~~`DELETE /users/{id}` con confirmación adicional~~ | ✅ **Implementado**: en frontend ahora se requiere tipear el email exacto del usuario para habilitar el botón "Eliminar definitivamente" (`confirmDeleteStrict`). Backend sigue sólo accesible para `super_admin`. Para producción se puede sumar rate-limit a nivel reverse-proxy. |
| ~~01-P-05~~ | ~~`POST /users/` no restringe qué `role_code` se puede asignar al crear~~ | ✅ **Resuelto 2026-08-09**: `create_user()` ahora rechaza con 403 si `current_user.role != super_admin` y el `role_code` del payload es `super_admin` **o** `admin` (restringido también admin↔admin, por consistencia con `update_user`/`01-P-03`). Altas de `admin`/`super_admin` quedan además marcadas en el audit log (`metadata_json` con `privileged: true`). Verificado en `tests/test_users_security_isolation.py`: admin→super_admin=403, admin→admin=403, admin→collaborator=201, super_admin→super_admin=201. |
| ~~01-P-06~~ | ~~Login con Google~~ | ✅ **Implementado (issue #83, 2026-08-10)**: `POST /auth/google` verifica el ID token que entrega Google Identity Services en el navegador (`google.oauth2.id_token.verify_oauth2_token`, sin intercambio de Authorization Code -- no hace falta `client_secret` ni `redirect_uri`). **Política deliberada: Google solo funciona como método de entrada a una cuenta ya existente** (creada por un admin en el módulo de Usuarios) -- si el email no tiene cuenta, `404` con mensaje explícito, nunca auto-crea. Decidir a qué organización asignar a un desconocido es una decisión de seguridad multi-tenant real; la opción segura es no tomarla sola. `GET /auth/google/config` (público) expone `{enabled, client_id}` para que el frontend decida si muestra el botón -- vacío/deshabilitado por defecto (`GOOGLE_CLIENT_ID` sin configurar), degrada limpio sin romper el login normal. `components/dashboard/google-sign-in-button.tsx` carga el script de Google bajo demanda solo si está habilitado. 8 tests nuevos en `tests/test_auth_google.py` (verificación de token mockeada, sin credenciales reales -- registrar la app en Google Cloud Console es acción humana, fuera de alcance del código). |

---

## Cómo se aplica el patrón en otros documentos

Este archivo sirve de plantilla. Para cada `.md` en `DOCUMENTOS/PLATAFORMA/`:

1. Leer el documento origen
2. Identificar las reglas implementables (backend, frontend, config)
3. Implementar los cambios
4. Crear `IMPLEMENTACION/XX-NOMBRE.md` con:
   - Checklist ✅/❌/⚠️
   - Tabla de archivos modificados
   - Sección de pendientes con razón
