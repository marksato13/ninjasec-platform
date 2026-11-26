# Implementación - Ninja Dev: operación y gestión de clientes

> Basado en: `PLANIFICACION/35-NINJA-DEV-OPERACION-Y-CLIENTES.md`
> Creado: 2026-11-25. 35-P-01 tiene el backend en revisión (PR #53).

## Checklist

| ID | Requisito | Estado | Evidencia esperada |
|---|---|---|---|
| `35-P-01` | Sistemas del cliente y entornos | 🟡 Backend en PR #53 | ✅ Migración `20261201_01` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 9 pruebas de permisos por rol, 404 ajeno, 422 secretos y auditoría, más 3 mutaciones detectadas; 🟡 pantallas en PR de `feat/secciones-ninja-dev`: `/dashboard/sistemas`, ficha `/dashboard/sistemas/[id]` con entornos, pestaña **Sistemas** en la ficha del cliente y **Mis sistemas** en el portal (`/portal/sistemas`). Probado contra PostgreSQL desechable: el cliente no ve repositorio, ubicación de claves, entorno oculto ni despliegues fallidos |
| `35-P-02` | Registro de despliegues | 🟡 Backend en PR #58 | ✅ Migración `20261201_02` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 7 pruebas: regla de checklist en `prod` (422), avance «Versión X publicada» en la bitácora una sola vez, cliente solo ve `prod` que llegó y sin checklist, roles, 404 ajeno y auditoría; ✅ 4 mutaciones detectadas; 🟡 pantalla `/dashboard/despliegues` y bloque en la ficha del sistema (registrar, corregir, quitar solo admin), en PR de `feat/secciones-ninja-dev`. Comprobado en vivo: `ok` a `prod` sin checklist → 422 |
| `35-P-03` | Solicitudes de cambio en Tickets | 🟡 Backend en PR #57 | ✅ Migración `20261201_03` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 5 pruebas: flujo abrir → estimar → aprobar/rechazar → convertir en tarea, roles, 404 ajeno y otra organización, garantía, auditoría; 3 mutaciones detectadas; 🟡 pantallas en PR `feat/cambios-y-uat-ui` (ver abajo) |
| `35-P-04` | Estimador de costos | Pendiente | Tarifas solo admin (prueba de 403/404); versión aprobada inmutable; propuesta de hitos C3 |
| `35-P-05` | Pruebas de aceptación (UAT) | 🟡 Backend en PR #61 | ✅ `tests/test_pruebas_de_aceptacion.py`: 7 pruebas, 4 mutaciones detectadas; suite `605 passed`; migración `20261202_01` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio). 🟡 Pantallas en PR `feat/cambios-y-uat-ui` (ver abajo) |
| `35-P-06` | Documentos desde plantilla | Pendiente | Generación en borrador interno; publicar es acción del admin |
| `35-P-07` | Mantenimiento y SLA | 🔒 Bloqueado | Decisión comercial de Mark (horas por plan, tiempos de respuesta, exceso) |
| `35-P-08` | Panel Ninja Dev | 🟡 En PR de `feat/secciones-ninja-dev` | `/dashboard/panel-dev`, solo con datos de la API: sistemas en producción, vencimientos a 30 días (garantía, dominio, certificado), despliegues fallidos o revertidos, cambios por estimar o esperando al cliente, y UAT con casos observados o lista para el acta (hasta 25 proyectos). Grupo de menú **Ninja Dev** en servidor y panel; `test_menus_por_rol.py` y `test_modos_backend.py` lo fijan |

## Pantallas de 35-P-03 y 35-P-05

Dentro de páginas que ya existían; sin rutas ni entradas de menú nuevas.

| Dónde | Qué |
|---|---|
| Panel · `/dashboard/support-tickets` | Filtro por tipo (incidencias, cambios); en cada fila, insignias de tipo, sistema y fase del cambio o garantía. Crear: tipo y sistema del cliente (obligatorio para un cambio). Detalle de un cambio (`components/tickets/solicitud-cambio.tsx`): estimar o reestimar (admin y colaborador), decisión del cliente con su motivo, convertir en tarea (solo admin: proyecto existente del cliente o nuevo, responsable del equipo) |
| Portal · `/portal/tickets` | «Pedir un cambio» sobre uno de sus sistemas; el cliente ve las horas y aprueba (`confirmApprove`) o rechaza (`askReason`, mínimo 5 caracteres). Las incidencias de un sistema en garantía muestran «En garantía hasta …». **Arreglo:** «Abiertos» pedía solo `open`; un ticket `in_progress` o `pending` (un cambio ya convertido) no salía en ninguna pestaña. Ahora se piden todos y se separan abiertos de `resolved`/`closed` |
| Panel · `/dashboard/projects/[id]` | Pestaña «Aceptación» (`components/uat/pruebas-aceptacion.tsx`): casos con pasos y resultado esperado; añadir, editar, corregir un observado (vuelve a pendiente), subir y bajar; quitar solo admin y no aprobados. Barra de progreso y aviso «Listo para el acta de conformidad» con `ready_for_signoff` |
| Portal · `/portal/projects/[id]` | El mismo componente en modo cliente: «Funciona» o «Observar» (nota de al menos 5 caracteres) según `can_decide`. Si el proyecto no tiene casos, la sección no aparece |

Evidencia (2026-11-25): `tsc` y `eslint` sin errores en los archivos tocados;
`next build --webpack` compila. Recorrido de extremo a extremo con un
Chromium propio sobre PostgreSQL 16 desechable y la API real: el cliente abre
el cambio, el colaborador estima 8 h, el cliente aprueba, el colaborador no ve
«Convertir», el admin lo convierte; el motivo de rechazo de 3 caracteres y la
observación de 2 se bloquean; el equipo añade y reordena un caso; el cliente
aprueba uno y observa otro; el «listo para acta» sale en panel y portal. A
390 px, seis pantallas sin scroll horizontal; ningún diálogo nativo.

Lo que falta en el backend (anotado, no se cambió aquí):

- `GET /support-tickets/` no filtra por `kind` ni por varios estados: el
  panel y el portal filtran en el cliente.
- Un cambio puede crearse sin `system_id`; la pantalla lo exige, la API no.
- Un colaborador no recibe los sistemas de un cliente con el que no trabaja:
  la insignia cae a «Sistema #id».

## Reglas de implementación

- Un PR por fila. El backend se fusiona antes que su pantalla.
- Las pantallas reutilizan el cliente API, las query keys y las alertas
  existentes; nunca `alert()` ni `window.confirm`.
- Nada de precios, tarifas ni datos de clientes reales en el repo: es público.
