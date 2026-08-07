# Implementación — Módulo Topología de Red

> Basado en: `PLANIFICACION/23-MODULO-TOPOLOGIA.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-07 · **23-P1 implementado en rama de frontend**

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

## ✅ P1 — Diagrama visual (sin parser)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 14 | Decidir librería de diagramación | ✅ | Se eligió `@xyflow/react` 12.11.2 en `PY-MK/frontend/package.json` |
| 15 | Instalar dependencia y verificar bundle | ✅ | `package-lock.json`; `/dashboard/devices`: 66.3 kB propios, 201 kB First Load JS |
| 16 | Componente `<NetworkTopology />` | ✅ | `PY-MK/frontend/src/components/devices/network-topology.tsx` |
| 17 | Nodo custom con icono por `device_type` | ✅ | Lucide: `Shield`, `Router`, `Network`, `Server`, `Radio`, `Monitor`, `Cloud`, fallback `HelpCircle` |
| 18 | Borde de nodo coloreado por `criticality` | ✅ | `CRITICALITY_COLOR` con cuatro niveles y fallback neutro |
| 19 | Arista con estilo según `link_type` | ✅ | `LINK_COLOR`; `trunk`, `vpn` y `wifi` usan trazos discontinuos |
| 20 | Grosor de arista según `bandwidth_mbps` | ✅ | `bandwidthWidth()` usa escala logarítmica limitada |
| 21 | Agrupación visual por sede usando `clusters` | ✅ | Nodos `group` padre por sede, con fallback "Sin sede" |
| 22 | Auto-layout jerárquico | ✅ | `TYPE_RANK`: firewall → router/cloud → switch → server/AP → endpoint/camera/other |
| 23 | Panel lateral al hacer clic en nodo | ✅ | Ficha del activo; rol `client` no muestra dirección IP |
| 24 | Pestaña "Topología" en `/dashboard/devices` | ✅ | `PY-MK/frontend/src/app/(admin)/dashboard/devices/page.tsx` añade tabs Inventario/Topología |
| 25 | Estado vacío (cliente sin conexiones) | ✅ | Mensajes para selección, carga, error y topología no declarada |
| 26 | Soporte de tema claro/oscuro | ✅ | `PY-MK/frontend/src/app/globals.css` usa tokens CSS existentes y adapta React Flow |

### Decisiones técnicas de 23-P1

- **Librería:** se aprueba `@xyflow/react` porque cubre nodos custom, zoom/pan, minimapa, controles, aristas con estilos, grupos por sede y click en nodo para ficha del activo. Mermaid queda descartado para P1 porque no resuelve bien interacción de ficha ni composición React.
- **Amortización:** la dependencia queda aceptada para 23-P1 y se reutilizaría en `27-P3` si ese editor visual se implementa; no implica arrancar ni documentar `27-P3` como hecho.
- **Bundle:** `npm ls @xyflow/react --depth=0` confirma `@xyflow/react@12.11.2`. `du -sh node_modules/@xyflow/react node_modules/@xyflow/system` reporta 3.2 MB + 1.3 MB instalados sin comprimir. La build de Next reporta `/dashboard/devices` con 66.3 kB propios y 201 kB First Load JS.
- **Permisos:** 23-P1 no añade rutas backend ni mutaciones. La UI consume sólo `GET /devices/topology?client_id=` mediante `getTopology()` y `QK.topology(clientId)`.
- **Aislamiento multi-tenant:** el aislamiento sigue en `TopologyService.build()`, que valida `client.organization_id == current_user.organization_id` y devuelve 404 si el cliente no pertenece a la organización. La ruta mantiene roles `super_admin`, `admin` y `collaborator`; la degradación visual para `client` en el componente oculta IP, pero no cambia permisos del endpoint.
- **Límites de alcance:** 23-P1 es visualización read-only. No incluye editor de conexiones, drag-and-drop para crear enlaces, parser de configs, generación de alertas, export PNG/SVG/PDF ni "Aplicar a la topología". Esos ítems permanecen en P2/P3/P4.

### Evidencia verificable 2026-08-07

- Commit de implementación frontend: `df2106892d1e8ead41b3766e734ac4a7ab4b0adb` (`feat(frontend): añadir topología visual de red`).
- Archivos modificados por la implementación: `PY-MK/frontend/package.json`, `PY-MK/frontend/package-lock.json`, `PY-MK/frontend/src/components/devices/network-topology.tsx`, `PY-MK/frontend/src/app/(admin)/dashboard/devices/page.tsx`, `PY-MK/frontend/src/app/globals.css`, `PY-MK/frontend/src/lib/query-keys.ts`.
- `git diff --check HEAD^ HEAD` en `feat/issue-4-backend`: sin salida, sin errores de whitespace.
- `NEXT_PUBLIC_API_URL=/api/v1 npm run build` en `PY-MK/frontend`: ✅ compila; genera 41 rutas; conserva warnings de lint preexistentes; `/dashboard/devices` queda en 66.3 kB y 201 kB First Load JS.
- Primer intento paralelo de `NEXT_PUBLIC_API_URL=/api/v1 npm run build`: ❌ falló con `ENOENT .next/types/routes.d.ts` por concurrencia sobre el mismo `.next`; reejecución serial posterior: ✅.
- `PYTHONPATH=. pytest -q`: no ejecutado en este entorno porque `pytest` no está instalado en PATH.
- `python3 -m pytest -q`: no ejecutado en este entorno porque `/usr/bin/python3` no tiene módulo `pytest`, aunque `requirements.txt` declara `pytest==8.4.0`.
- `PY-MK/frontend/next.config.ts`: sin cambios; los dos rewrites `/api/v1/:path*/` y `/api/v1/:path*` permanecen.

### Evidencia visual para PR

- Pendiente explícito de PR: adjuntar capturas de `/dashboard/devices` en pestaña "Topología" con un cliente con conexiones, incluyendo vista desktop y mobile, panel lateral tras click en nodo, estado vacío y modo claro/oscuro.
- El bucle visual no queda marcado como completado en este checklist hasta que esas capturas estén adjuntas al PR o se registre una validación manual equivalente con navegador.

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
| 43 | Vista degradada para rol `client` (sin IPs ni puertos) | ⏳ |

---

## Dependencias

| Depende de | Estado |
|---|---|
| Módulo 05 Dispositivos | ✅ cerrado |
| Módulo 03 Clientes | ✅ cerrado |
| Campos ISO en `Device` | ✅ migrados |
| Librería de diagramación | ✅ `@xyflow/react` 12.11.2 aprobado para P1 |

**Sin bloqueos para P1.** Queda pendiente la evidencia visual de PR indicada arriba; P2/P3/P4 no forman parte de este cierre.

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
