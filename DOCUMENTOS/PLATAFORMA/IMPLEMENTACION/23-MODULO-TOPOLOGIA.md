# Implementación — Módulo Topología de Red

> Basado en: `PLANIFICACION/23-MODULO-TOPOLOGIA.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-08 · **23-P1 documentado para PR**

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
- **Representación:** los dispositivos se dibujan como nodos custom con icono Lucide por `device_type`, borde por `criticality` y fallback visual neutro. Las conexiones se dibujan como aristas `smoothstep`, con color por `link_type`, trazo discontinuo para `trunk`, `vpn` y `wifi`, y grosor derivado de `bandwidth_mbps`.
- **Layout:** P1 usa layout determinista client-side, no auto-layout externo: cada `cluster` del backend crea un nodo padre de sede, y los activos se ordenan por `TYPE_RANK` (`firewall` → `router/cloud` → `switch` → `server/AP` → `endpoint/camera/other`). Esto evita persistir coordenadas y mantiene el diagrama read-only.
- **Bundle:** en la rama de implementación `feat/issue-4-backend`, `package-lock.json` incluye `@xyflow/react` y `@xyflow/system`. La evidencia registrada allí reporta `@xyflow/react@12.11.2`, 3.2 MB + 1.3 MB instalados sin comprimir y `/dashboard/devices` en 66.3 kB propios / 201 kB First Load JS. En esta rama de documentación, `npm ci` no instala `@xyflow/react` porque el cambio de frontend vive en la rama de implementación; por eso la build local actual de esta rama mide `/dashboard/devices` en 7.03 kB / 141 kB.
- **Permisos:** 23-P1 no añade rutas backend ni mutaciones. La UI consume sólo `GET /devices/topology?client_id=` mediante `getTopology()` y `QK.topology(clientId)`.
- **Aislamiento multi-tenant:** el aislamiento sigue en `TopologyService.build()`, que valida `client.organization_id == current_user.organization_id` y devuelve 404 si el cliente no pertenece a la organización. La ruta mantiene roles `super_admin`, `admin` y `collaborator`; la degradación visual para `client` en el componente oculta IP, pero no cambia permisos del endpoint.
- **Seguridad:** no se introducen secretos, almacenamiento nuevo ni exposición de configuraciones. El parser, la persistencia de `raw_config` y cualquier consentimiento/cifrado asociado quedan fuera de P1.
- **Límites de alcance:** 23-P1 es visualización read-only. No incluye editor de conexiones, drag-and-drop para crear enlaces, parser de configs, generación de alertas, export PNG/SVG/PDF, persistencia de posiciones ni "Aplicar a la topología". Esos ítems permanecen en P2/P3/P4.

### Evidencia verificable

- Commit de implementación frontend: `df2106892d1e8ead41b3766e734ac4a7ab4b0adb` (`feat(frontend): añadir topología visual de red`).
- Archivos modificados por la implementación: `PY-MK/frontend/package.json`, `PY-MK/frontend/package-lock.json`, `PY-MK/frontend/src/components/devices/network-topology.tsx`, `PY-MK/frontend/src/app/(admin)/dashboard/devices/page.tsx`, `PY-MK/frontend/src/app/globals.css`, `PY-MK/frontend/src/lib/query-keys.ts`.
- `git show --stat df2106892d1e8ead41b3766e734ac4a7ab4b0adb`: confirma 7 archivos modificados y la incorporación de `network-topology.tsx`.
- `git diff --check`: ✅ sin salida en esta rama de documentación.
- `NEXT_PUBLIC_API_URL=/api/v1 npm run build` en `PY-MK/frontend` de esta rama (`docs/issue-4`, 2026-08-08): ✅ compila; genera 41 rutas; conserva warnings de lint preexistentes; `/dashboard/devices` queda en 7.03 kB y 141 kB First Load JS porque esta rama no contiene aún la dependencia visual.
- `NEXT_PUBLIC_API_URL=/api/v1 npm run build` en `PY-MK/frontend` de la rama de implementación (`feat/issue-4-backend`, evidencia registrada el 2026-08-07): ✅ compila; genera 41 rutas; conserva warnings de lint preexistentes; `/dashboard/devices` queda en 66.3 kB y 201 kB First Load JS.
- Primer intento paralelo de `NEXT_PUBLIC_API_URL=/api/v1 npm run build`: ❌ falló con `ENOENT .next/types/routes.d.ts` por concurrencia sobre el mismo `.next`; reejecución serial posterior: ✅.
- `PYTHONPATH=. pytest -q` en `PY-MK/backend` (`docs/issue-4`, 2026-08-08): ❌ no ejecuta porque `pytest` no está instalado en PATH.
- `python3 -m venv .venv` en `PY-MK/backend` (`docs/issue-4`, 2026-08-08): ❌ bloqueado por `ensurepip` ausente; el entorno pide instalar `python3.14-venv`. No se instalaron dependencias globales.
- `PY-MK/frontend/next.config.ts`: sin cambios; los dos rewrites `/api/v1/:path*/` y `/api/v1/:path*` permanecen.
- Contrato de topología (rama `test/issue-4`): `PYTHONPATH=. pytest -q tests/test_topology.py` valida nodos por tipo y criticidad, enlaces, agrupación por sede, estado vacío y selección de activo mediante `id`; la misma suite valida el aislamiento entre organizaciones, permisos de edición y la vista degradada del cliente sin IPs ni puertos.

### Evidencia visual para PR

- Pendiente explícito de PR: adjuntar capturas de `/dashboard/devices` en pestaña "Topología" con un cliente con conexiones, incluyendo vista desktop y mobile, panel lateral tras click en nodo, estado vacío y modo claro/oscuro.
- Tarea pendiente: ejecutar el bucle visual con la rama de implementación servida localmente y adjuntar las capturas al PR. Esta rama de documentación no puede cerrar la validación visual porque no contiene el componente `NetworkTopology` ni `@xyflow/react`.
- El bucle visual no queda marcado como completado en este checklist hasta que esas capturas estén adjuntas al PR o se registre una validación manual equivalente con navegador.

## ✅ P2 — Editor de conexiones — Resuelto 2026-08-09

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 27 | Modal de alta de conexión (origen, destino, tipo, puertos, VLAN) | ✅ | `network-topology.tsx` — reutiliza `components/ui/modal.tsx`, el modal genérico |
| 28 | Eliminar conexión con `confirmDelete` | ✅ | `onEdgeClick` → `confirmDelete()` → `deleteConnection()` |
| 29 | Crear conexión arrastrando entre nodos | ✅ | `nodesConnectable={canEdit}` + `onConnect` — los `<Handle>` ya existían en `DeviceNode` desde P1, solo faltaba habilitar la interacción |
| 30 | Validación: no auto-enlace, no duplicado | ✅ | Auto-enlace: rechazado en frontend antes de abrir el modal y en backend (400, ya existía). Duplicado: **antes se devolvía la conexión existente en silencio** (200, indistinguible de un alta real) — ahora `connection_service.py` responde 409 con mensaje claro |

Solo `super_admin`/`admin`/`collaborator` ven los controles de edición (`canEdit`, mismos roles que ya exige el backend en `POST`/`DELETE /device-connections`); el rol `client` sigue con el diagrama de solo lectura de P1 sin cambios. Validado con `tests/test_topology.py`: conexión duplicada → 409, auto-enlace → 400, admin puede eliminar una conexión.

## ✅ P3 — Config Visualizer (parser Cisco IOS) — Resuelto 2026-08-09

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 31 | Tabla `device_configs` + migración | ✅ | `db/models/device_config.py`, migración `20260809_02` |
| 32 | Carga de archivo con File API — **parseo en el navegador** | ✅ | `components/devices/config-visualizer.tsx` — `FileReader`, nada viaja al servidor salvo guardado explícito |
| 33 | Detección de vendor por sintaxis | ✅ | `lib/config-parser/detect-vendor.ts` — Cisco/MikroTik/pfSense/no reconocido |
| 34 | Parser Cisco IOS: interfaces, VLANs, trunk/access, IP, rutas | ✅ | `lib/config-parser/cisco-ios.ts` |
| 35 | Tarjetas de especificación por interfaz | ✅ | `config-visualizer.tsx` — tabla modo/VLAN/IP/descripción/estado |
| 36 | `parse_warnings` para sintaxis no cubierta | ✅ | Sub-líneas no reconocidas *dentro* de un bloque `interface`/`vlan` se registran con contexto; secciones enteras fuera de alcance (aaa, crypto, ntp, banners, ACLs) se ignoran sin advertencia — están documentadas como no cubiertas, no son "sintaxis rota" |
| 37 | Documentar comandos soportados y no soportados | ✅ | `config-visualizer.tsx` — panel "Comandos soportados" con la lista de `SUPPORTED_COMMANDS` |

**Endpoint de persistencia opcional:** `POST/GET /device-configs` (`modules/devices/routers/configs.py`) — rechaza vendors no soportados con 400, exige pertenencia a la organización (404 si el dispositivo es de otra), y **nunca devuelve `raw_config`** en las respuestas (solo `has_raw_config: bool`) aunque se haya guardado. Validado con `tests/test_device_configs.py`.

Los 3 agentes de la flota corrieron sin generar ningún commit (se quedaron explorando o terminaron sin mensaje final); se completó manualmente.

## ✅ P4 — Resumen, alertas y export — Resuelto 2026-08-09

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 38 | Resumen ejecutivo en lenguaje natural | ✅ | `lib/config-parser/analysis.ts` → `summarizeConfig()`; cuenta interfaces/activas, VLANs, troncales, accesos, rutas e interfaces de gestión sin IP |
| 39 | Alertas de higiene (puerto sin descripción, VLAN no declarada, shutdown) | ✅ | `analysis.ts` → `hygieneAlerts()`, los 3 casos del criterio de aceptación |
| 40 | Botón "Aplicar a la topología" → crea `device_connections` con revisión previa | ✅ | Backend: `TopologyService.deduce_connections()` (heurística de subred + next-hop, ver docstring) expuesto en `POST /devices/{id}/topology/deduce-connections`; Frontend: `config-visualizer.tsx` abre un modal con checkbox por candidato — nada se crea sin confirmación explícita |
| 41 | Export PNG / SVG | ✅ | `lib/topology-export.ts` — layout propio (mismo criterio que `network-topology.tsx`, sin depender de React Flow), SVG nativo, PNG rasterizado vía `<canvas>` — sin dependencias nuevas |
| 42 | Export PDF con diagrama + inventario (ReportLab existente) | ✅ | `modules/devices/services/topology_pdf.py` — `Drawing` de `reportlab.graphics.shapes` para el diagrama + `Table` para el inventario, mismo patrón que `reports/services/pdf_service.py`; endpoint `GET /devices/topology/export/pdf?client_id=` |
| 43 | Vista degradada para rol `client` (sin IPs ni puertos) | ✅ | No aplica una vista degradada nueva porque el rol `client` no llega a esta pantalla: `Config Visualizer` vive en `/dashboard/devices`, dentro del layout `(admin)` que `DashboardGuard` restringe a `super_admin`/`admin`/`collaborator` — el portal cliente no tiene esta pestaña |

### Heurística de "Aplicar a la topología" — límite honesto

El parser (P3) no extrae vecinos (no hay CDP/LLDP en el alcance de Cisco IOS parseado). "Deducir" candidatos usa dos señales del propio parseo, cruzadas contra los demás dispositivos del mismo cliente:

1. **Misma subred**: la IP de una interfaz local con máscara cae en la misma red que la IP de otro dispositivo.
2. **Next-hop de ruta estática**: el next-hop de una ruta coincide exactamente con la IP de otro dispositivo.

Ambos casos son señales de proximidad de red razonables, no una verdad topológica confirmada — por eso el endpoint devuelve candidatos con `reason` explicado y el frontend nunca crea nada sin que el usuario confirme cada uno en el modal.

### Evidencia verificada (2026-08-09)

- Suite completa: **171 tests pasan, 1 skip** (incluye 5 casos nuevos en `test_topology_export.py`: misma subred, next-hop, sin coincidencias, IP/máscara inválida no rompe el endpoint, aislamiento entre organizaciones, y export PDF genera un documento `%PDF-` válido).
- Smoke test manual end-to-end vía `curl`: cliente → integración → 2 dispositivos en la misma subred → `POST .../deduce-connections` devuelve el candidato con motivo "misma subred" → `POST /device-connections/` con esos IDs crea la conexión real (201) → `GET .../topology/export/pdf` devuelve `200`, `content-type: application/pdf`, documento válido de 1 página verificado con `file`.
- `npx tsc --noEmit` sin errores en el frontend.
- Nota de integración: los 3 agentes de la flota (`feat/issue-17-backend`, `test/issue-17`, `docs/issue-17`) no produjeron ningún commit real — sus ramas quedaron en el mismo commit que su `main` base. La rama de docs (`docs/issue-17`) sí generó un commit, pero documentaba P4 como completo citando como evidencia dependencias preexistentes no relacionadas (`@xyflow/react`, el parser P3 ya mergeado) sin que el código de P4 existiera — se descartó sin mergear y P4 se implementó manualmente desde cero.

---

## Dependencias

| Depende de | Estado |
|---|---|
| Módulo 05 Dispositivos | ✅ cerrado |
| Módulo 03 Clientes | ✅ cerrado |
| Campos ISO en `Device` | ✅ migrados |
| Librería de diagramación | ✅ `@xyflow/react` 12.11.2 aprobado para P1 |

**P1 queda documentado y técnicamente cerrado en la rama de implementación.** Queda pendiente sólo el bucle de validación visual de PR indicado arriba; P2/P3/P4 no forman parte de este cierre.

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
