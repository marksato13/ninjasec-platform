# Módulo: Dashboard Principal

**Ruta:** `/dashboard`
**Acceso:** `super_admin`, `admin`

---

## ¿Qué muestra?

El dashboard es la pantalla de mando operativo. Agrega información crítica de todos los módulos en tiempo real.

### Barra de alertas
- Muestra el total de alertas críticas activas
- Se activa el pulso rojo (`pulse-critical`) cuando hay alertas críticas
- Contenido: licencias vencidas + tickets sin resolver críticos + hallazgos de revisiones

### 4 KPI Cards (métricas principales)
| KPI | Fuente de datos |
|-----|----------------|
| Revisiones ejecutadas (%) | Módulo Revisiones — closed / total |
| Hallazgos críticos abiertos | Módulo Revisiones — findings abiertos de severidad critical |
| Tickets abiertos | Módulo Tickets — status = open o in_progress |
| Activos monitoreados | Módulo Dispositivos — total de devices activos |

### Accesos rápidos
Atajos a los 4 módulos más usados: Revisiones, Tickets, Clientes, Inventario.

### Actividad reciente
Últimas 5 acciones registradas en el log de auditoría: creaciones, actualizaciones, eliminaciones de cualquier módulo.

### Panel de alertas detallado
Lista expandida de todas las alertas activas con:
- Severidad (crítica / warning)
- Mensaje descriptivo
- Tipo de alerta (integration / support_ticket / review)
- Fecha de generación

---

## Interacción con roles

| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Ver dashboard completo | ✅ | ✅ |
| Filtrar por cliente | ✅ | ✅ |
| Refrescar alertas manualmente | ✅ | ✅ |
| Ver actividad reciente (audit) | ✅ | ✅ |

---

## Filtro por cliente

El dropdown "Todos los clientes" permite aislar las métricas de un cliente específico.  
Al seleccionar un cliente, los KPIs se recalculan mostrando solo sus datos.

---

## Datos técnicos

- Las alertas se generan en el backend al consultar `/api/v1/collection/alerts`
- La actividad reciente viene de `/api/v1/audit/logs?limit=5`
- No hay websocket — el refresh es manual o al recargar la página
