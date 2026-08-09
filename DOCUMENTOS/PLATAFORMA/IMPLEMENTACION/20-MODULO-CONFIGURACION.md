# Implementación — Módulo Configuración

> Basado en: `PLANIFICACION/20-MODULO-CONFIGURACION.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Catálogos

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `Area` con slug y `organization_id` nullable | ✅ | `db/models/area.py` |
| 2 | Modelo `ProjectType` con slug | ✅ | `db/models/project_type.py` |
| 3 | Modelo `Product` ligado a área | ✅ | `db/models/product.py` |
| 4 | `is_active` en los tres catálogos (retiro lógico) | ✅ | los tres modelos |
| 5 | Unicidad de `name` y `slug` compuesta con `organization_id` | ✅ | `db/models/area.py` · `project_type.py` · `product.py` → `UniqueConstraint` + migración `20260806_01` |

### Endpoints

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 6 | `GET /areas` | ✅ | `modules/catalogs/routers/router.py:15` |
| 7 | `GET /project-types` | ✅ | `router.py:25` |
| 8 | `GET /products` filtrado por organización | ✅ | `modules/catalogs/routers/router.py:53` |
| 8b | `POST` / `PUT /areas` | ✅ | `router.py` → `create_area` · `update_area` |
| 8c | `POST` / `PUT /project-types` | ✅ | `router.py` → `create_project_type` · `update_project_type` |
| 8d | `GET /areas/{id}/usage` y `/project-types/{id}/usage` | ✅ | `router.py` → `_contar_uso()` |
| 9 | `POST` / `PUT /doc-types` | ✅ | `modules/docs/routers/router.py:65` / `:90` |

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 10 | Navegación por 3 pestañas | ✅ | `(admin)/dashboard/settings/page.tsx` → `type Tab` |
| 11 | Listado de tipos de proyecto | ✅ | `settings/page.tsx` |
| 12 | Listado de áreas | ✅ | `settings/page.tsx` |
| 13 | Listado + alta de tipos de documento | ✅ | `settings/page.tsx` |
| 14 | Validación Zod en el formulario | ✅ | `docTypeSchema` (name ≥2, scope enum) |
| 15 | Gating por rol (`isSuperAdmin` / `isAdmin`) | ✅ | `settings/page.tsx` → `getStoredUser()` |
| 16 | Pantalla para editar umbrales de alertas | ✅ | `settings/page.tsx` → `GET/PUT /alerts/thresholds` |
| 17 | CRUD de áreas desde Configuración | ✅ | `settings/page.tsx` → pestaña **Áreas** + `POST/PUT /areas` |
| 18 | CRUD de tipos de proyecto desde Configuración | ✅ | `settings/page.tsx` → pestaña **Tipos de proyecto** + `POST/PUT /project-types` |
| 19 | Desactivación con aviso de uso | ✅ | `settings/page.tsx` + `GET /areas/{id}/usage` y `/project-types/{id}/usage` |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~20-P-01~~ | ~~**CRUD de áreas desde la UI**~~ | — | ✅ **Resuelto 2026-08-09**: la pantalla `/dashboard/settings`, pestaña **Áreas**, permite crear, editar y desactivar áreas usando `POST /areas`, `PUT /areas/{id}` y `GET /areas/{id}/usage`. Antes de desactivar un área usada muestra el conteo de dependencias y envía `confirm_deactivation: true` solo tras confirmación del administrador |
| ~~20-P-02~~ | ~~**CRUD de tipos de proyecto desde la UI**~~ | — | ✅ **Resuelto 2026-08-09**: la pantalla `/dashboard/settings`, pestaña **Tipos de proyecto**, permite crear, editar y desactivar tipos usando `POST /project-types`, `PUT /project-types/{id}` y `GET /project-types/{id}/usage`. Mantiene los catálogos globales como visibles/no editables |
| 20-P-03 | CRUD de productos | 🟡 Media | El endpoint `GET` existe; no hay pestaña ni escritura |
| 20-P-04 | Toggle `is_active` de productos desde la UI | 🟡 Media | Áreas y tipos de proyecto ya tienen desactivación con aviso de uso; falta cubrir productos |
| ~~20-P-05~~ | ~~**Pestaña de umbrales operativos**~~ | — | ✅ **Resuelto 2026-08-09**: configuración persistida por organización para umbrales de alertas. Backend en commit `a1ac5e8`: tabla `organization_alert_thresholds`, modelo `OrganizationAlertThreshold`, servicio `get_alert_thresholds()` y `GET/PUT /alerts/thresholds`. El comportamiento mantiene valores por defecto `overdue_days = 7` y `no_review_days = 30` cuando la organización no tiene registro propio |
| ~~20-P-06~~ | ~~Endpoints `POST`/`PUT` para areas y project-types~~ | — | ✅ **Resuelto 2026-08-06**: `catalogs/routers/router.py`. Slug derivado del nombre, unicidad validada con 409, catálogos globales protegidos. Tests en `tests/test_catalogs_write.py` (12) |
| ~~20-P-07~~ | ~~Aviso de uso antes de desactivar~~ | — | ✅ **Reforzado 2026-08-08**: `GET /areas/{id}/usage` y `/project-types/{id}/usage` devuelven el uso. El `PUT` rechaza con `409` y `detail.in_use_by` la desactivación de un catálogo usado salvo que reciba `confirm_deactivation: true`; la baja sigue siendo lógica y conserva las referencias históricas. Tests en `tests/test_catalogs_write.py` |
| ~~20-P-08~~ | ~~**`GET /products` no filtra por organización**~~ | — | ✅ **Resuelto 2026-08-06**: filtro por `organization_id` en los tres catálogos. `Area`/`ProjectType` además admiten globales (`NULL`). Tests en `tests/test_catalogs_tenant_isolation.py` (5) — **verificado que fallan sin el fix** |
| ~~20-P-09~~ | ~~**`unique` global en catálogos multi-tenant**~~ | — | ✅ **Resuelto 2026-08-06**: `UniqueConstraint(organization_id, name/slug)` en `Area`, `ProjectType` y `Product` + migración `20260806_01_catalog_tenant_unique.py`. Tests en `tests/test_catalogs_composite_unique.py` (5) |
| 20-P-10 | `organization_id` nullable en `Area` y `ProjectType` | 🟡 Media | Un registro con `organization_id = NULL` es visible para todos sin que ninguna regla lo declare. Decidir: o es catálogo global explícito, o es `NOT NULL` |
| 20-P-11 | Los catálogos los lee el rol `client` | 🟡 Media | `catalogs/routers/router.py` solo exige `get_current_user`. Un cliente no debería enumerar las áreas internas ni los productos de la consultora |

---

## ✅ Riesgo de aislamiento cerrado — 2026-08-06

`20-P-08` era el pendiente más grave de los módulos 15-22 y no estaba detectado en la primera pasada.

**Lo que había:** `list_products()` ejecutaba `select(Product).where(Product.is_active == True)` sin cláusula de organización, mientras sus vecinos —`collection`, `organizations`, `devices`— sí filtraban. Era una omisión puntual, no un criterio de diseño.

**Cerrado.** Los tres catálogos filtran ahora por `organization_id`, con una distinción deliberada:

| Modelo | `organization_id` | Regla aplicada |
|---|---|---|
| `Product` | `NOT NULL` | Solo la organización propia |
| `Area` · `ProjectType` | nullable | Propia **+** globales (`NULL`), que son los del seed |

**Verificado de verdad:** los tests se ejecutaron contra el código original y **fallaron los 3 de aislamiento**. Un test que pasa antes y después del fix no prueba nada.

`20-P-09` era el complemento: sin unicidad compuesta, el segundo tenant no podía dar de alta sus propios catálogos. Resuelto con `UniqueConstraint(organization_id, name/slug)` y la migración `20260806_01`.

> ⚠️ **Un límite que queda escrito:** en PostgreSQL los `NULL` son distintos entre sí, así que la restricción compuesta no impide dos catálogos globales con el mismo nombre. Los globales vienen del seed, que sí es controlado. Si algún día se permite crearlos por API, hace falta un índice parcial.

---

## Estado real del módulo

Era el módulo **menos completo** de los construidos: funcionaba como *visor*, no como panel. Tras la sesión del 2026-08-06 ya tiene escritura real de `areas` y `project_types`, con:

- Slug derivado del nombre (`Auditoría Técnica` → `auditoria-tecnica`), sin pedirle al administrador que sepa qué es un slug
- Duplicados rechazados con **409**, no con un `IntegrityError` crudo
- Catálogos globales protegidos: se ven, no se editan
- Registros de otra organización devuelven **404**, no 403 — no se confirma que existan
- No se borra, se desactiva: un área referenciada por proyectos históricos no puede desaparecer

**Orden de trabajo restante:**
1. `20-P-03` — CRUD de productos
2. `20-P-04` — toggle de `is_active` de productos
3. `20-P-10` / `20-P-11` — decidir si `Area`/`ProjectType` son globales o por tenant, y si `client` debe leer catálogos

---

## ✅ CRUD de catálogos en Configuración — 2026-08-09

`20-P-01` y `20-P-02` quedan cerrados: los endpoints de escritura que existían desde la Tanda 0 ya están conectados desde `/dashboard/settings`.

**Pantalla creada:**

| Pestaña | Acciones | Endpoints |
|---|---|---|
| **Áreas** | Listar, crear, editar y desactivar | `GET /areas`, `POST /areas`, `PUT /areas/{id}`, `GET /areas/{id}/usage` |
| **Tipos de proyecto** | Listar, crear, editar y desactivar | `GET /project-types`, `POST /project-types`, `PUT /project-types/{id}`, `GET /project-types/{id}/usage` |

La UI mantiene el patrón de Configuración: pestañas dentro de `/dashboard/settings`, formularios compactos, validación en el cliente, acciones restringidas a `admin` y `super_admin`, y uso de las alertas existentes en lugar de `alert()` o `window.confirm`.

**Flujo de desactivación con uso:**

1. El administrador pulsa desactivar sobre un área o tipo de proyecto.
2. La pantalla consulta el endpoint `/usage` correspondiente.
3. Si `in_use_by` es mayor que cero, se muestra el conteo antes de continuar.
4. Al confirmar, la UI envía `PUT` con `is_active: false` y `confirm_deactivation: true`.
5. El backend rechaza con `409` cualquier desactivación usada que no incluya confirmación; con confirmación conserva las referencias históricas y solo cambia `is_active`.

**Evidencia de pruebas:**

```bash
docker run --rm -v /home/m4rk/workspace/worktrees/issue-9-backend/PY-MK/backend:/app -w /app python:3.12-slim sh -c 'pip install -q -r requirements.txt && PYTHONPATH=. pytest -q tests/test_catalogs_write.py'
```

**Resultado:** `14 passed, 52 warnings`.

---

## ✅ Umbrales operativos por organización — 2026-08-09

`20-P-05` queda cerrado por la implementación backend registrada en `a1ac5e8`.

**Cambios verificables:**

- Nueva tabla `organization_alert_thresholds` con clave primaria `organization_id`, `overdue_days` y `no_review_days`
- Modelo `db/models/organization_alert_threshold.py` relacionado con `Organization`
- Servicio `modules/alerts/services/threshold_service.py` con fallback explícito a `7` días para tickets vencidos y `30` días para dispositivos sin revisión
- Endpoints `GET /alerts/thresholds` y `PUT /alerts/thresholds`, restringidos a `super_admin` y `admin`
- Auditoría `alerts.thresholds.update` al guardar cambios

**Comportamiento por organización:**

| Caso | Resultado |
|---|---|
| Organización sin configuración propia | Usa defaults `overdue_days = 7` y `no_review_days = 30` |
| Organización con configuración propia | El motor de alertas lee los valores persistidos sin reiniciar el servicio |
| Otra organización tiene umbrales distintos | No se leen ni se mezclan; cada tenant consulta por su `organization_id` |
| Colaborador intenta leer o cambiar umbrales | Respuesta 403 |

**Prueba ejecutada:**

```bash
docker run --rm -v /home/m4rk/workspace/worktrees/issue-8-backend/PY-MK/backend:/app -w /app python:3.12-slim sh -c 'pip install -q -r requirements.txt && PYTHONPATH=. pytest -q tests/test_alert_thresholds.py'
```

**Resultado:** `6 passed, 28 warnings`.
