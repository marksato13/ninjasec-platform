# Implementación — Módulo Topología de Red

> Basado en: `PLANIFICACION/23-MODULO-TOPOLOGIA.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-08 · **P1 visual completado**

---

## ✅ Ya implementado (verificado en código 2026-08-05)

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `DeviceConnection` con 7 tipos de enlace | ✅ | `db/models/device_connection.py` |
| 2 | Constraint única (source, target, link_type) | ✅ | `uq_device_connection_triplet` |
| 3 | `ondelete=CASCADE` en ambos extremos | ✅ | `device_connection.py` |
| 4 | Migración Alembic | ✅ | `versions/e1d861bf2ce6_devices_iso_p1_connections.py` |
| 5 | Campos ISO en `Device`: `criticality`, `data_classification`, `responsible_user_id` | ✅ | `db/models/device.py` |
| 6 | `GET /devices/topology?client_id=` | ✅ | `modules/devices/routers/router.py:63` |
| 7 | `TopologyService.build()` → nodes + edges + clusters | ✅ | `services/topology_service.py` |
| 8 | Validación de frontera de organización | ✅ | `topology_service.py:29-31` |
| 9 | Agrupación por sede (`clusters`) | ✅ | `topology_service.py` |
| 10 | CRUD `/device-connections` | ✅ | `modules/devices/routers/connections.py` |
| 11 | `ConnectionService.list_for_client()` | ✅ | `services/connection_service.py` |
| 12 | Cliente API TypeScript tipado completo | ✅ | `frontend/src/lib/api/topology.ts` |
| 13 | Enum `DeviceLinkType` | ✅ | `db/models/enums.py` |

---

## ⏳ P1 — Diagrama visual (sin parser)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 14 | Decidir librería de diagramación | ✅ | `@xyflow/react` 12.11.2 |
| 15 | Instalar dependencia y verificar bundle | ✅ | Ruta `/dashboard/devices`: 66.3 kB propios, 201 kB First Load JS; paquete instalado 4.4 MB sin comprimir |
| 16 | Componente `<NetworkTopology />` | ✅ | `components/devices/network-topology.tsx` |
| 17 | Nodo custom con icono por `device_type` | ✅ | Iconos Lucide |
| 18 | Borde de nodo coloreado por `criticality` | ✅ | Cuatro niveles y fallback |
| 19 | Arista con estilo según `link_type` | ✅ | Color por tipo; trunk, VPN y wifi discontinuos |
| 20 | Grosor de arista según `bandwidth_mbps` | ✅ | Escala logarítmica limitada |
| 21 | Agrupación visual por sede usando `clusters` | ✅ | Nodos padre por sede |
| 22 | Auto-layout jerárquico | ✅ | Firewall → router/cloud → switch → servidor/AP → endpoint |
| 23 | Panel lateral al hacer clic en nodo | ✅ | Vista degradada para `client` sin IP ni puertos |
| 24 | Pestaña "Topología" en `/dashboard/devices` | ✅ | Selector de cliente compartido |
| 25 | Estado vacío (cliente sin conexiones) | ✅ | Mensajes para selección y topología no declarada |
| 26 | Soporte de tema claro/oscuro | ✅ | Tokens CSS existentes y estilos de React Flow adaptados |

### Evidencia 2026-08-08

- `NEXT_PUBLIC_API_URL=/api/v1 npm run build`: finaliza correctamente, 41 páginas generadas; conserva los warnings de lint preexistentes.
- `/dashboard/devices`: 66.3 kB de código de ruta y 201 kB de First Load JS en la salida de Next.js.
- Los dos rewrites de `frontend/next.config.ts` permanecen sin cambios.
- El frontend sólo consume `GET /devices/topology?client_id=` mediante el cliente TypeScript existente; el aislamiento continúa delegado al endpoint con validación de `organization_id`.
- El endpoint mantiene los roles existentes (`super_admin`, `admin` y `collaborator`), por lo que un perfil `client` no recibe el contrato sensible; adicionalmente, el componente omite IP y detalles de puertos cuando se reutiliza con ese rol.

## ⏳ P2 — Editor de conexiones

| # | Requisito | Estado |
|---|-----------|--------|
| 27 | Modal de alta de conexión (origen, destino, tipo, puertos, VLAN) | ⏳ |
| 28 | Eliminar conexión con `confirmDelete` | ⏳ |
| 29 | Crear conexión arrastrando entre nodos | ⏳ |
| 30 | Validación: no auto-enlace, no duplicado | ⏳ |

## ⏳ P3 — Config Visualizer (parser Cisco IOS)

| # | Requisito | Estado |
|---|-----------|--------|
| 31 | Tabla `device_configs` + migración | ⏳ |
| 32 | Carga de archivo con File API — **parseo en el navegador** | ⏳ |
| 33 | Detección de vendor por sintaxis | ⏳ |
| 34 | Parser Cisco IOS: interfaces, VLANs, trunk/access, IP, rutas | ⏳ |
| 35 | Tarjetas de especificación por interfaz | ⏳ |
| 36 | `parse_warnings` para sintaxis no cubierta | ⏳ |
| 37 | Documentar comandos soportados y no soportados | ⏳ |

## ⏳ P4 — Resumen, alertas y export

| # | Requisito | Estado |
|---|-----------|--------|
| 38 | Resumen ejecutivo en lenguaje natural | ⏳ |
| 39 | Alertas de higiene (puerto sin descripción, VLAN no declarada, shutdown) | ⏳ |
| 40 | Botón "Aplicar a la topología" → crea `device_connections` con `origen: auto` | ⏳ |
| 41 | Export PNG / SVG | ⏳ |
| 42 | Export PDF con diagrama + inventario (ReportLab existente) | ⏳ |
| 43 | Vista degradada para rol `client` (sin IPs ni puertos) | ✅ P1 |

## Evidencia de pruebas

- [x] Contrato de topología: `PYTHONPATH=. pytest -q tests/test_topology.py` valida nodos por tipo y criticidad, enlaces, agrupación por sede, estado vacío y selección de activo mediante `id`.
- [x] Autorización: la misma suite valida el aislamiento entre organizaciones, permisos de edición y la vista degradada del cliente sin IPs ni puertos.

---

## Dependencias

| Depende de | Estado |
|---|---|
| Módulo 05 Dispositivos | ✅ cerrado |
| Módulo 03 Clientes | ✅ cerrado |
| Campos ISO en `Device` | ✅ migrados |
| Librería de diagramación | ✅ `@xyflow/react` 12.11.2 |

**Sin bloqueos.** P1 puede empezar hoy mismo.

---

## Estimación

| Fase | Esfuerzo | Valor |
|---|---|---|
| P1 | 1 sesión | 🔥 Muy alto — backend hecho, solo falta pintar |
| P2 | 0.5 sesión | Alto |
| P3 | 2 sesiones | Medio — es donde está el riesgo de scope |
| P4 | 1 sesión | Alto |

**P1 es la mejor relación valor/esfuerzo de todo el roadmap.** El trabajo pesado ya está hecho y sin usar; hoy hay un endpoint completo que nadie consume.

---

## ⚠️ Riesgo de alcance

El parser es el punto donde este módulo puede desbordarse. NAPALM lleva una década parseando configuraciones y sigue incompleto. **Regla:** un solo vendor (Cisco IOS), casos comunes, y documentación explícita de lo no cubierto. Un parser que aparenta soportar todo y falla en silencio es peor que uno honesto y limitado.
