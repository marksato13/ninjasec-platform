# Módulo: Servicios

**Ruta:** `/dashboard/services` (admin) | `/portal/services` (cliente)
**Acceso:** `super_admin`, `admin` (gestión) | `client` (solicitar)

---

## ¿Qué es?

Catálogo de servicios que Ninja Tech ofrece a sus clientes. Los clientes pueden ver el catálogo y solicitar servicios desde su portal. El equipo admin gestiona el catálogo y el estado de las solicitudes.

---

## Catálogo de servicios (tipos)

Ejemplos de servicios que puede ofrecer Ninja Tech:
- Auditoría de seguridad externa
- Pen testing de aplicaciones web
- Monitoreo continuo de infraestructura
- Configuración y hardening de firewall
- Respuesta ante incidentes (IR)
- Capacitación en ciberseguridad
- Análisis de vulnerabilidades
- Cumplimiento normativo (ISO 27001, NIST)

---

## Estados de solicitud de servicio

```
NEW → REVIEW → CLOSED
```

| Estado | Color | Descripción |
|--------|-------|-------------|
| `NEW` | 🔵 Azul | Solicitud recién enviada |
| `REVIEW` | 🟡 Amarillo | En evaluación por el equipo |
| `CLOSED` | ⚫ Gris | Cerrada (aprobada, rechazada o completada) |

---

## Vista del catálogo (admin y cliente)

### Cards de servicio
- Borde izquierdo en color verde seguridad
- Icono de escudo
- Nombre del servicio
- Descripción
- Precio referencial (si aplica)
- Botón "Solicitar" (disponible para clientes y admin)

---

## Gestión de solicitudes (solo admin)

### Tabla de solicitudes
Columnas: ID, Cliente, Servicio, Estado, Fecha

### Acciones sobre solicitudes
- Transicionar de estado (NEW → REVIEW → CLOSED) con botones inline
- Ver detalle de la solicitud

---

## Acciones disponibles

| Acción | super_admin | admin | client |
|--------|:-----------:|:-----:|:------:|
| Ver catálogo | ✅ | ✅ | ✅ |
| Crear servicio en catálogo | ✅ | ✅ | ❌ |
| Solicitar servicio | ✅ | ✅ | ✅ |
| Ver solicitudes (todas) | ✅ | ✅ | Solo propias |
| Cambiar estado de solicitud | ✅ | ✅ | ❌ |
| Eliminar del catálogo | ✅ | ❌ | ❌ |

---

## Datos técnicos

- Catálogo: `GET /api/v1/services`
- Solicitudes: `GET /api/v1/services/requests`
- Nueva solicitud: `POST /api/v1/services/requests`
- Actualizar estado: `PATCH /api/v1/services/requests/{id}`
