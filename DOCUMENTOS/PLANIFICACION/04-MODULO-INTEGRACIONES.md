# Módulo: Integraciones

**Ruta:** `/dashboard/integrations` | `/dashboard/integrations/[id]`
**Acceso:** `super_admin`, `admin`

---

## ¿Qué es?

Las integraciones son las consolas de red configuradas para cada cliente. Actualmente soporta:
- **pfSense** — firewall open source
- **FortiGate** — firewall Fortinet

Cada integración representa una consola instalada en una sede del cliente y es el origen de los datos de dispositivos y alertas.

---

## Listado de integraciones

### Información visible
- Nombre de la consola (ej: "pfSense - Blue Shield HQ")
- Tipo (pfSense / FortiGate)
- Cliente al que pertenece
- Ambiente (producción / staging / DR)
- Estado de salud (semáforo: verde / amarillo / rojo)
- Días para vencimiento de licencia

### Indicador de salud (HealthIndicator)
| Color | Significado |
|-------|-------------|
| 🟢 Verde | Consola activa, licencia vigente, sin alertas |
| 🟡 Amarillo | Licencia próxima a vencer (< 30 días) o sin revisión reciente |
| 🔴 Rojo | Licencia vencida o consola offline |

---

## Detalle de integración (`/dashboard/integrations/[id]`)

### KPIs del detalle
- Dispositivos activos conectados a esta consola
- Dispositivos en revisión pendiente
- Días hasta vencimiento de licencia (relativo)
- Total de revisiones de seguridad hechas sobre esta consola

### Información adicional
- Tipo de licencia (standard / enterprise / trial)
- Usuario responsable de la consola
- Ambiente donde está desplegada
- Fecha de último review

---

## Acciones disponibles

| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Ver listado | ✅ | ✅ |
| Crear integración | ✅ | ✅ |
| Editar integración | ✅ | ✅ |
| Ver detalle completo | ✅ | ✅ |
| Eliminar integración | ✅ | ❌ |

---

## Alertas automáticas generadas

El sistema genera alertas en el Dashboard cuando:
1. La licencia de una integración venció (crítica)
2. La licencia vence en menos de 30 días (warning)
3. No se ha realizado una revisión en más de 90 días

---

## Datos técnicos

- Endpoint: `GET /api/v1/integrations`
- Detalle: `GET /api/v1/integrations/{id}`
- Las alertas de licencia se evalúan en `/api/v1/collection/alerts`
