# Módulo: Dispositivos

**Ruta:** `/dashboard/devices`
**Acceso:** `super_admin`, `admin`, `collaborator`

---

## ¿Qué es?

Inventario de todos los activos de red monitoreados a través de las integraciones (consolas pfSense/FortiGate). Cada dispositivo pertenece a una integración y por ende a un cliente.

---

## Tipos de dispositivos

| Tipo | Descripción |
|------|-------------|
| `firewall` | Dispositivo firewall principal |
| `switch` | Switch de red |
| `server` | Servidor físico o virtual |
| `endpoint` | PC, laptop, estación de trabajo |
| `router` | Router o dispositivo de borde |
| `ap` | Access Point WiFi |
| `camera` | Cámara de seguridad IP |
| `other` | Otro tipo de activo |

---

## Estados de dispositivo

| Estado | Color | Descripción |
|--------|-------|-------------|
| `active` | 🟢 Verde | Funcionando con normalidad |
| `maintenance` | 🟡 Amarillo | En mantenimiento programado |
| `pending_review` | 🟠 Naranja | Necesita revisión o actualización |
| `offline` | 🔴 Rojo | Sin conexión o con falla |
| `decommissioned` | ⚫ Gris | Dado de baja del inventario |

---

## Funcionalidades

### Filtros disponibles
- Por tipo de dispositivo (clickable pills)
- Por cliente
- Por integración / consola

### Vista de cards agrupadas por tipo
Los dispositivos se agrupan visualmente por su tipo con un encabezado de sección. Dentro de cada grupo se muestran cards con:
- Nombre e IP del dispositivo
- Estado (badge con color semáforo)
- Cliente e integración a la que pertenece
- Modelo / fabricante
- Última actualización

### Banner de alerta
Si hay dispositivos en `pending_review`, aparece un banner de advertencia en la parte superior con el conteo.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator |
|--------|:-----------:|:-----:|:------------:|
| Ver inventario | ✅ | ✅ | ✅ |
| Agregar dispositivo | ✅ | ✅ | ❌ |
| Editar dispositivo | ✅ | ✅ | ✅ |
| Cambiar estado | ✅ | ✅ | ✅ |
| Eliminar dispositivo | ✅ | ❌ | ❌ |

---

## Relación con otros módulos

- Cada dispositivo pertenece a una **Integración** → que pertenece a un **Cliente**
- Los dispositivos `pending_review` generan alertas en el **Dashboard**
- Un dispositivo puede estar asociado a una **Revisión de Seguridad**

---

## Portal cliente

Los clientes pueden ver sus propios dispositivos en `/portal/inventory` con información simplificada (sin IPs ni datos técnicos sensibles).
