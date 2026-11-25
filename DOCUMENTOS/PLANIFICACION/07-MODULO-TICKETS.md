# Módulo: Tickets de Soporte

**Ruta:** `/dashboard/support-tickets` (admin) | `/portal/tickets` (cliente)
**Acceso:** `super_admin`, `admin`, `collaborator`, `client`

---

## ¿Qué es?

Sistema de gestión de incidentes y solicitudes de soporte técnico. Los clientes abren tickets desde el portal y el equipo Ninja Tech los atiende con SLA definidos por prioridad.

---

## Estados del ticket

```
open → in_progress → pending → resolved → closed
```

| Estado | Descripción |
|--------|-------------|
| `open` | Recién creado, sin asignar |
| `in_progress` | Técnico asignado, trabajando |
| `pending` | Esperando respuesta del cliente o proveedor |
| `resolved` | Solución aplicada, pendiente confirmación del cliente |
| `closed` | Cerrado definitivamente |

---

## Prioridades y SLA

| Prioridad | Color | SLA máximo |
|-----------|-------|------------|
| `critical` | 🔴 Rojo | 4 horas |
| `high` | 🟠 Naranja | 8 horas |
| `medium` | 🟡 Amarillo | 24 horas |
| `low` | 🟢 Verde | 72 horas |

> Un ticket es **vencido** si lleva más horas abiertas que su SLA sin estar resuelto o cerrado.

---

## Categorías de ticket

| Categoría | Descripción |
|-----------|-------------|
| `support` | Soporte técnico general |
| `incident` | Incidente de seguridad activo |
| `request` | Solicitud de cambio o configuración |
| `maintenance` | Mantenimiento programado |

---

## Funcionalidades del backoffice (admin/collaborator)

### Bandeja por estado (tabs)
- Cada tab muestra los tickets en ese estado
- Badge con el conteo por estado
- Indicador ⚠ con número de tickets vencidos por estado

### Filtros disponibles
- Por cliente
- Por prioridad
- Por rango de fechas (apertura)

### Detalle del ticket
- Historial de eventos (cambios de estado, notas manuales, asignaciones)
- Selector de estado para transicionar
- Selector de técnico asignado
- Campo de resolución / notas finales
- Botón "Agregar evento" para registro manual de seguimiento

---

## Funcionalidades del portal cliente

- Ver solo sus tickets
- Crear nuevo ticket con título, descripción y prioridad
- Ver el estado y eventos de cada ticket
- NO pueden reasignar ni cambiar estado (solo el equipo Ninja Tech)

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|--------|:-----------:|:-----:|:------------:|:------:|
| Ver todos los tickets | ✅ | ✅ | ✅ | Solo propios |
| Crear ticket | ✅ | ✅ | ✅ | ✅ |
| Asignar técnico | ✅ | ✅ | ❌ | ❌ |
| Cambiar estado | ✅ | ✅ | ✅ | ❌ |
| Agregar evento | ✅ | ✅ | ✅ | ❌ |
| Exportar XLSX | ✅ | ✅ | ❌ | ❌ |
| Importar XLSX | ✅ | ✅ | ❌ | ❌ |
| Eliminar ticket | ✅ | ❌ | ❌ | ❌ |

---

## Alertas automáticas

Los tickets `open` o `in_progress` que superen su SLA aparecen como alertas en el Dashboard con severidad según prioridad.

---

## Datos técnicos

- Endpoint: `GET /api/v1/support-tickets`
- Eventos: `POST /api/v1/support-tickets/{id}/events`
- Exportar: `GET /api/v1/support-tickets/export/xlsx`
