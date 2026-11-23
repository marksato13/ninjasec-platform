# Módulo: Usuarios

**Ruta:** `/dashboard/users`
**Acceso:** `super_admin` (total) | `admin` (parcial)

---

## ¿Qué es?

Gestión de todas las cuentas de acceso al sistema — tanto del equipo interno (admin, collaborator) como de los clientes (client). Es el módulo de control de identidades y roles.

---

## Campos de un usuario

| Campo | Descripción |
|-------|-------------|
| Nombre completo | Nombre y apellidos |
| Email | Identificador único / login |
| Rol | super_admin / admin / collaborator / client |
| Cargo | Función o puesto (ej: "Pen Tester Sr.") |
| Estado | Activo / Inactivo |
| Acceso | Área de acceso derivada del rol |
| Último acceso | Fecha del último login |
| Creado | Fecha de creación de la cuenta |

---

## Vistas disponibles

### Vista Cards (por rol)
Los usuarios se agrupan por rol con encabezado de sección:
- **Super Admins** (badge celeste)
- **Administradores** (badge azul)
- **Colaboradores** (badge verde)
- **Clientes** (badge ámbar)

Cada card muestra: avatar, nombre, email, badge de estado (Activo/Inactivo), cargo, área de acceso, último acceso y fecha de creación.

### Vista Tabla
Filas compactas con avatar, nombre/email, cargo, rol, estado, último acceso y acciones.

---

## Filtros disponibles

- Búsqueda por nombre, email o rol
- Filtro por rol (pills clickables con conteo)
- Filtro por estado (activo / inactivo)
- Rango de fechas de creación
- Rango de fechas de actualización

---

## Acciones disponibles

| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Ver todos los usuarios | ✅ | ✅ |
| Crear usuario | ✅ | ✅ |
| Editar nombre y cargo | ✅ | ✅ |
| Activar / desactivar cuenta | ✅ | ✅ |
| Cambiar rol | ✅ | ❌ |
| Eliminar usuario | ✅ | ❌ |
| Ver detalle completo | ✅ | ✅ |

---

## Toggle de estado (activo/inactivo)

El interruptor en el modal de edición permite activar o desactivar una cuenta sin eliminarla. Un usuario inactivo no puede hacer login pero su historial se conserva.

---

## Relación con otros módulos

- Los usuarios con rol `collaborator` tienen un perfil en el módulo **Colaboradores**
- Los usuarios con rol `client` tienen acceso al **Portal Cliente** y están vinculados a una empresa cliente
- Todos los cambios de usuarios quedan registrados en **Auditoría**

---

## Datos técnicos

- Endpoint: `GET /api/v1/users`
- Crear: `POST /api/v1/auth/register`
- Editar: `PATCH /api/v1/users/{id}`
- Eliminar: `DELETE /api/v1/users/{id}` (solo super_admin)
