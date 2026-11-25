# Módulo: Colaboradores

**Ruta:** `/dashboard/collaborators`
**Acceso:** `super_admin`, `admin` (completo) | `collaborator` (ver)

---

## ¿Qué es?

Directorio del equipo interno de Ninja Tech. Muestra perfiles de todos los profesionales con sus skills, certificaciones, disponibilidad y especialidad.

---

## Perfil de colaborador

Cada colaborador tiene:
- **Nombre completo** y foto/avatar generado
- **Cargo** (Pen Tester Sr., Analista SOC, Ing. Infraestructura, etc.)
- **Especialidad** (área principal de expertise)
- **Disponibilidad** (indicator de dot colorido)
- **Skills** (lista de habilidades técnicas)
- **Certificaciones** (certificados profesionales)
- **Área** (Operaciones, Administración, Comercial, etc.)

---

## Estados de disponibilidad

| Estado | Color | Descripción |
|--------|-------|-------------|
| `available` | 🟢 Verde | Disponible para asignaciones |
| `busy` | 🔴 Rojo | Ocupado con proyecto actual |
| `partial` | 🟡 Amarillo | Disponibilidad parcial |
| `off` | ⚫ Gris | Vacaciones o licencia |

---

## Vistas disponibles

### Vista Cards
- Grid de cards con avatar, nombre, cargo y disponibilidad
- Borde izquierdo con el color de disponibilidad
- Skills expandibles con "+N más" cuando hay muchas
- Botones: Ver perfil completo | Editar

### Vista Tabla
- Fila compacta por colaborador
- Columnas: Avatar, Nombre, Cargo, Área, Disponibilidad, Acciones

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator |
|--------|:-----------:|:-----:|:------------:|
| Ver directorio | ✅ | ✅ | ✅ |
| Crear colaborador | ✅ | ✅ | ❌ |
| Editar colaborador | ✅ | ✅ | Solo el propio |
| Cambiar disponibilidad | ✅ | ✅ | Solo el propio |
| Eliminar colaborador | ✅ | ❌ | ❌ |

---

## Relación con otros módulos

- Los colaboradores son los **técnicos asignados** en Tickets de Soporte
- Son los **revisores** en Revisiones de Seguridad
- Son los **miembros del equipo** en Proyectos
- Tienen un usuario correspondiente en el módulo de Usuarios (rol `collaborator`)

---

## Datos técnicos

- Endpoint: `GET /api/v1/collaborators`
- Actualizar: `PATCH /api/v1/collaborators/{id}`
- Skills: `GET /api/v1/skills` | `POST /api/v1/collaborators/{id}/skills`
