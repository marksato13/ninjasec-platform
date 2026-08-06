# Módulo: Topología de Red y Config Visualizer

**Ruta prevista:** `/dashboard/devices` (pestaña "Topología") · `/dashboard/clients/[id]`
**Acceso:** `super_admin`, `admin`, `collaborator` · `client` con vista degradada (sin IPs)
**Backend:** `modules/devices` — **ya implementado**, falta la UI

---

## ¿Qué es?

Diagrama de red automático por cliente. Dos vías de alimentación:

1. **Manual/API** — conexiones declaradas en `device_connections` (ya operativo)
2. **Config Visualizer** — el usuario sube un `running-config` y el parser deduce interfaces, VLANs, troncales y enlaces, generando la topología sola

Resuelve un problema real y caro: en las PYMEs peruanas **nadie tiene el diagrama de red actualizado**. Existe en la cabeza del técnico que se fue o en un Visio de hace tres años.

---

## ⚠️ Estado real: el backend ya existe

Verificado en código el 2026-08-05:

| Componente | Estado | Archivo |
|---|---|---|
| Tabla `device_connections` | ✅ | `db/models/device_connection.py` |
| Migración Alembic | ✅ | `versions/e1d861bf2ce6_devices_iso_p1_connections.py` |
| `GET /devices/topology?client_id=` | ✅ | `modules/devices/routers/router.py:63` |
| `TopologyService.build()` (nodes + edges + clusters) | ✅ | `services/topology_service.py` |
| CRUD `/device-connections` | ✅ | `routers/connections.py` |
| Cliente API TypeScript tipado | ✅ | `frontend/src/lib/api/topology.ts` |
| **Componente visual** | ❌ | **no existe** |
| **Parser de configuraciones** | ❌ | **no existe** |

**Traducción:** el módulo está al ~50%. Falta la parte visible y el parser.

---

## Entidades

### `device_connections` (existente)

| Campo | Descripción |
|---|---|
| `source_device_id` / `target_device_id` | Extremos del enlace (FK con `CASCADE`) |
| `link_type` | `ethernet` · `wifi` · `wan` · `vpn` · `mpls` · `trunk` · `cloud_peering` |
| `port_source` / `port_target` | Puertos físicos (`Gi0/1`, `ether2`) |
| `vlan_id` | VLAN del enlace |
| `bandwidth_mbps` | Ancho de banda nominal |
| `notes` | Observaciones |

Restricción `uq_device_connection_triplet` sobre (source, target, link_type) — evita enlaces duplicados del mismo tipo.

### `device_configs` (nueva, para el Config Visualizer)

| Campo | Descripción |
|---|---|
| `device_id` | Dispositivo al que pertenece |
| `vendor_detected` | `cisco_ios` · `mikrotik` · `pfsense` · `huawei_vrp` |
| `raw_config` | Texto original (opcional — ver reglas) |
| `parsed_json` | Resultado estructurado del parser |
| `uploaded_by` / `uploaded_at` | Trazabilidad |
| `parse_warnings` | Sintaxis no reconocida, para no aparentar que "está roto" |

---

## Contrato de la API de topología

```
GET /devices/topology?client_id=1
{
  "client_id": 1,
  "client_name": "...",
  "nodes":    [{ id, label, device_type, vendor, model, ip_address,
                 status, criticality, data_classification, site_id,
                 responsible_user_id, responsible_user_name, integration_id }],
  "edges":    [{ id, source, target, link_type, port_source,
                 port_target, vlan_id, bandwidth_mbps }],
  "clusters": [{ label, site_id, node_ids }]
}
```

Los `clusters` agrupan por sede — permiten dibujar cajas por local sin lógica adicional en el cliente.

---

## Funcionalidades previstas

### Diagrama interactivo
- Nodo por dispositivo, con icono según `device_type` y **borde coloreado por `criticality`**
- Arista por conexión: grosor según `bandwidth_mbps`, estilo según `link_type` (troncal punteada multicolor, VPN discontinua)
- Agrupación visual por sede usando `clusters`
- Zoom, arrastre y auto-layout jerárquico (firewall arriba → switches → APs/endpoints)
- Clic en nodo → panel lateral con la ficha completa del activo

### Config Visualizer
- Carga del archivo, **parseado en el navegador** — la configuración no viaja al servidor salvo que el usuario lo pida explícitamente
- Detección automática de vendor por sintaxis (`interface GigabitEthernet` → Cisco; `/interface ethernet` → MikroTik; XML → pfSense)
- Tarjeta por interfaz: modo, VLANs permitidas, VLAN nativa, IP, descripción, estado
- Resumen ejecutivo en lenguaje natural: *"3 VLANs configuradas, 2 puertos troncales, 1 puerto de gestión sin IP asignada (posible riesgo), 2 rutas estáticas"*
- Alertas de higiene: puertos sin descripción, VLANs usadas sin declarar, interfaces en shutdown que deberían estar activas
- Botón "Aplicar a la topología" → crea las `device_connections` deducidas

### Exportación
- PNG / SVG del diagrama
- PDF con diagrama + inventario + resumen (reutiliza el motor ReportLab existente)
- Export a formato drawio para edición manual posterior

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver topología del cliente | ✅ | ✅ | ✅ | ⏳¹ |
| Crear / editar conexión | ✅ | ✅ | ✅ | ❌ |
| Eliminar conexión | ✅ | ✅ | ❌ | ❌ |
| Subir configuración | ✅ | ✅ | ✅ | ❌ |
| Aplicar topología deducida | ✅ | ✅ | ❌ | ❌ |
| Exportar diagrama | ✅ | ✅ | ✅ | ⏳¹ |

¹ Vista degradada: sin IPs, sin puertos, sin números de serie — coherente con la decisión ya tomada en el inventario del portal.

---

## Reglas de negocio

1. **La configuración es material sensible.** El parseo ocurre en el navegador por defecto; persistir `raw_config` requiere consentimiento explícito y cifrado en reposo.
2. Un enlace deducido por el parser se marca como `origen: auto` y **no pisa** una conexión declarada manualmente.
3. La topología respeta la frontera de organización: `TopologyService` valida `client.organization_id` antes de construir nada.
4. El cliente nunca ve IPs ni puertos en su vista de topología.
5. El parser documenta explícitamente qué comandos soporta. Sintaxis no reconocida va a `parse_warnings`, nunca se descarta en silencio.

---

## Alcance acotado (decisión importante)

Parsear todos los vendors es un proyecto de años — NAPALM y los parsers de Ansible llevan una década. Para que esto sea entregable:

| Fase | Alcance |
|---|---|
| **P1** | UI del diagrama sobre el backend ya existente. **Cero parser.** |
| **P2** | Parser Cisco IOS: interfaces, VLANs, trunk/access, IP, rutas estáticas |
| **P3** | Resumen ejecutivo + alertas de higiene + export PDF |
| **P4** | Segundo vendor (MikroTik o pfSense XML) sobre parser modular |

**P1 es la mejor relación valor/esfuerzo de todo el roadmap:** el backend ya está hecho, solo falta pintar.

---

## Decisión técnica pendiente

| Opción | A favor | En contra |
|---|---|---|
| **`@xyflow/react`** (React Flow) | Interactivo, auto-layout, nodos custom, encaja con React 19 | Dependencia nueva (~50 kB) |
| **Mermaid.js** | Declarativo, ya se renderiza en muchos contextos | Poco interactivo, layout limitado |
| **D3.js** | Control total | Mucho más código para el mismo resultado |

**Recomendación: React Flow.** El requisito de "clic en nodo → ficha del activo" descarta a Mermaid.

---

## Conexión con otros módulos

- **05 — Dispositivos:** fuente de los nodos
- **04 — Integraciones:** agrupa los dispositivos por consola
- **03 — Clientes:** eje del diagrama
- **28 — NetDoctor:** las alertas de higiene del parser alimentan el diagnóstico
- **24 — Cumplimiento:** el diagrama es evidencia del control ISO 27001 A.8.1 (inventario de activos)
