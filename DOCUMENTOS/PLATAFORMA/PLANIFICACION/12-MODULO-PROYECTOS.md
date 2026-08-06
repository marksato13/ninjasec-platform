# Módulo: Proyectos

**Ruta:** `/dashboard/projects`
**Acceso:** `super_admin`, `admin` (completo) | `collaborator` (asignados)

---

## ¿Qué es?

Pipeline de proyectos activos y en planificación. Gestiona los proyectos de implementación, configuración y consultoría que NinjaSec ejecuta para sus clientes.

---

## Estados de proyecto

| Estado | Color | Descripción |
|--------|-------|-------------|
| `PLANNING` | 🔵 Azul | En planificación, no iniciado |
| `ACTIVE` | 🟢 Verde | En ejecución |
| `ON_HOLD` | 🟡 Amarillo | Pausado temporalmente |
| `COMPLETED` | ⚫ Gris | Finalizado exitosamente |
| `CANCELLED` | 🔴 Rojo | Cancelado |

---

## Tipos de proyecto

| Tipo | Descripción |
|------|-------------|
| `implementation` | Implementación de solución nueva |
| `consulting` | Consultoría técnica |
| `audit` | Auditoría de seguridad |
| `support` | Proyecto de soporte continuo |
| `training` | Capacitación al equipo del cliente |

---

## Información de un proyecto

- **Nombre** del proyecto
- **Cliente** asociado
- **Tipo** y **área**
- **Estado** actual
- **Fechas:** inicio estimado / inicio real / fin estimado / fin real
- **Equipo asignado** (colaboradores)
- **Presupuesto** (referencial)
- **Descripción** y objetivos

---

## Vistas disponibles

### Vista Cards (pipeline)
- Cards agrupadas por estado
- Borde con color de estado
- Nombre, cliente y fechas clave
- Badge de estado

### Vista Tabla
- Filas compactas con todos los campos
- Acciones inline

---

## Filtros disponibles

- Por estado
- Por tipo de proyecto
- Por cliente
- Por área

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator |
|--------|:-----------:|:-----:|:------------:|
| Ver todos los proyectos | ✅ | ✅ | Solo asignados |
| Crear proyecto | ✅ | ✅ | ❌ |
| Editar proyecto | ✅ | ✅ | ❌ |
| Actualizar estado | ✅ | ✅ | ✅ asignados |
| Asignar equipo | ✅ | ✅ | ❌ |
| Eliminar proyecto | ✅ | ❌ | ❌ |

---

## Datos técnicos

- Endpoint: `GET /api/v1/projects`
- Crear: `POST /api/v1/projects`
- Actualizar: `PATCH /api/v1/projects/{id}`
