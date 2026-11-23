# Módulo: Clientes

**Ruta:** `/dashboard/clients` | `/dashboard/clients/[id]`
**Acceso:** `super_admin`, `admin`

---

## ¿Qué es?

Gestión centralizada de todas las empresas clientes de NinjaSec. Cada cliente tiene su perfil completo con integaciones, dispositivos, tickets, servicios contratados y revisiones de seguridad.

---

## Listado de clientes (`/dashboard/clients`)

### Información visible por cliente
- Nombre de la empresa
- Sector / industria
- País y ciudad
- Número de dispositivos activos
- Tickets abiertos (badge)
- Estado de la relación (activo / suspendido)
- Botón para ir al perfil detallado

### Acciones disponibles
| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Crear nuevo cliente | ✅ | ✅ |
| Ver perfil de cliente | ✅ | ✅ |
| Editar datos del cliente | ✅ | ✅ |
| Exportar listado XLSX | ✅ | ✅ |

---

## Perfil de cliente (`/dashboard/clients/[id]`)

Página de 360° del cliente con tabs:

### Tab: Resumen
- KPIs del cliente: tickets abiertos, dispositivos activos, servicios contratados, consolas activas
- Botón de exportar reporte consolidado en PDF

### Tab: Integraciones
- Consolas pfSense / FortiGate asignadas a este cliente
- Estado de salud de cada consola
- Próxima expiración de licencia

### Tab: Dispositivos
- Inventario de activos monitoreados por este cliente
- Filtro por tipo (firewall, switch, server, endpoint)
- Estado de cada dispositivo (active / maintenance / offline)

### Tab: Tickets
- Historial de tickets de soporte de este cliente
- Filtro por estado y prioridad

### Tab: Revisiones
- Auditorías de seguridad realizadas para este cliente
- Estado (scheduled / in_progress / closed)
- Hallazgos por revisión

### Tab: Servicios
- Servicios contratados por el cliente
- Estado de cada solicitud de servicio

---

## Relación con otros módulos

```
Cliente
  ├── Integraciones (1 cliente → N consolas)
  │     └── Dispositivos (1 consola → N dispositivos)
  ├── Tickets de soporte (1 cliente → N tickets)
  ├── Revisiones de seguridad (1 cliente → N revisiones)
  ├── Servicios contratados (1 cliente → N servicios)
  └── Usuario portal (1 cliente → N usuarios con rol "client")
```

---

## Datos técnicos

- Endpoint principal: `GET /api/v1/clients`
- Perfil completo: `GET /api/v1/clients/{id}`
- Exportar PDF: `GET /api/v1/reports/client/{id}/pdf`
