# Implementación — Módulo Usuarios

> Basado en: `DOCUMENTOS/PLATAFORMA/13-MODULO-USUARIOS.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Vista Cards (agrupada por rol)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Grupos por rol: Super Admins / Administradores / Colaboradores / Clientes | ✅ | `users/page.tsx` → `ROLE_ORDER` + `ROLE_LABELS` |
| 2 | Avatar con iniciales y hue por nombre | ✅ | `users/page.tsx` → `getInitials()` + `getAvatarHue()` |
| 3 | Nombre completo + email | ✅ | `users/page.tsx` |
| 4 | Badge estado Activo/Inactivo | ✅ | `users/page.tsx` → `getStatusBadgeClass()` |
| 5 | Cargo (job_title) | ✅ | `users/page.tsx` |
| 6 | Área de acceso derivada del rol | ✅ | `users/page.tsx` → `getAccessLabel(user.role_code)` |
| 7 | Último acceso (relativo: Hoy / Ayer / Hace N días) | ✅ | `users/page.tsx` → `lastLoginLabel()` |
| 8 | Fecha de creación | ✅ | `users/page.tsx` → `formatDate()` |
| 9 | Borde con color según si está activo o inactivo | ✅ | `users/page.tsx` → `borderLeft: user.is_active ? success : muted` |

### Vista Tabla

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | Columnas: Avatar, Nombre/Email, Cargo, Rol, Estado, Último acceso, Acciones | ✅ | `users/page.tsx` |
| 11 | Toggle vista cards/tabla | ✅ | `users/page.tsx` → `LayoutGrid` / `List` icons |

### Filtros

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 12 | Búsqueda por nombre, email o rol | ✅ | `users/page.tsx` → `query` state |
| 13 | Pills clickables con conteo por rol | ✅ | `users/page.tsx` → `ROLE_OPTIONS` con `roleCounts` |
| 14 | Filtro por estado (activo / inactivo) | ✅ | `users/page.tsx` → `statusFilter` |
| 15 | Rango fechas de creación (desde/hasta) | ✅ | `users/page.tsx` → `createdFrom` / `createdTo` |
| 16 | Rango fechas de actualización | ✅ | `users/page.tsx` → `updatedFrom` / `updatedTo` |

### Acciones por rol

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 17 | Ver todos los usuarios: admin/super_admin | ✅ | `users/page.tsx` |
| 18 | Crear usuario: admin/super_admin | ✅ | `users/page.tsx` → `<UserForm />` |
| 19 | Editar nombre y cargo: admin/super_admin | ✅ | `users/page.tsx` → modal edit |
| 20 | Activar/desactivar: toggle en modal edit | ✅ | `users/page.tsx` → `toggle-switch` |
| 21 | Cambiar rol: **solo super_admin** | ✅ | `users/page.tsx` → `{isSuperAdmin && <select rol>}` |
| 22 | Envía `role_code` al backend solo si super_admin | ✅ | `users/page.tsx` → `...(isSuperAdmin && editRole ? { role_code: editRole } : {})` |
| 23 | Eliminar usuario: **solo super_admin** | ✅ | `users/page.tsx` → `{isSuperAdmin && <button Eliminar>}` |
| 24 | Ver detalle completo (modal) | ✅ | `users/page.tsx` → modal `viewOpen` con todos los campos |

### Backend (ya implementado previamente)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 25 | `PUT /users/{id}` acepta `role_code` solo si super_admin | ✅ | `users/routers/router.py` → validación de rol en update |
| 26 | `DELETE /users/{id}` solo super_admin | ✅ | `users/routers/router.py` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/app/(admin)/dashboard/users/page.tsx` | Agregado `import { QK }` + reemplazado `["users"]` por `QK.users()` en 4 ocurrencias. **Nuevo:** link "Ver auditoría →" en el modal de edición que abre `/dashboard/audit?entity_type=users&entity_id={user.id}` en nueva pestaña |
| `frontend/src/app/(admin)/dashboard/audit/page.tsx` | **Nuevo:** soporte para `?entity_type=X&entity_id=N` via `useSearchParams`; nuevo input "ID específico" y nuevo state `filterEntityId`. Componente envuelto en `<Suspense>` para evitar el bailout de SSG (mismo patrón que `/login`). Banner descriptivo cuando el filtro por ID está activo |

---

## Archivos de referencia (sin cambios necesarios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/users.ts` | `getUsers()`, `updateUser()`, `deleteUser()` |
| `frontend/src/components/forms/user-form.tsx` | Formulario de creación de usuario |
| `backend/app/modules/users/routers/router.py` | CRUD completo de usuarios con guards de rol |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~13-P-01~~ | ~~Anti-patrón useEffect/setUsers~~ | ✅ **Implementado** en sesión anterior |
| ~~13-P-02~~ | ~~Auditoría de cambios de usuario en la UI~~ | ✅ **Implementado**: link "Ver auditoría →" en el modal de edición del usuario que abre `/dashboard/audit?entity_type=users&entity_id={id}` en nueva pestaña. La página de auditoría ahora lee `useSearchParams` y aplica los filtros automáticamente. Además tiene un input adicional para filtrar por ID específico desde la UI |
| ~~13-P-03~~ | ~~Error genérico para email duplicado~~ | ✅ **Implementado** en sesión anterior |
