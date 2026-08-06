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

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| 20-P-01 | **CRUD de áreas desde la UI** | 🔴 Alta | Solo lectura. Crear un área exige SQL directo o modificar el seed |
| 20-P-02 | **CRUD de tipos de proyecto desde la UI** | 🔴 Alta | Mismo caso que `20-P-01` |
| 20-P-03 | CRUD de productos | 🟡 Media | El endpoint `GET` existe; no hay pestaña ni escritura |
| 20-P-04 | Toggle `is_active` desde la UI | 🟡 Media | El campo existe en los tres catálogos y no se puede accionar |
| 20-P-05 | **Pestaña de umbrales operativos** | 🔴 Alta | Los valores de alertas (`_OVERDUE_DAYS`, `_NO_REVIEW_DAYS`) están hardcodeados. Ver `18-P-02` |
| ~~20-P-06~~ | ~~Endpoints `POST`/`PUT` para areas y project-types~~ | — | ✅ **Resuelto 2026-08-06**: `catalogs/routers/router.py`. Slug derivado del nombre, unicidad validada con 409, catálogos globales protegidos. Tests en `tests/test_catalogs_write.py` (12) |
| ~~20-P-07~~ | ~~Aviso de uso antes de desactivar~~ | — | ✅ **Resuelto 2026-08-06**: `GET /areas/{id}/usage` y `/project-types/{id}/usage` devuelven cuántos proyectos, servicios y productos dependen. El conteo queda también en el audit log al desactivar |
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
1. `20-P-01` y `20-P-02` — conectar la UI a los endpoints que ya existen
2. `20-P-04` — toggle de `is_active` usando el endpoint `/usage` para el aviso
3. `20-P-03` — CRUD de productos
4. `20-P-05` — pestaña de umbrales (desbloquea `18-P-02`)
5. `20-P-10` / `20-P-11` — decidir si `Area`/`ProjectType` son globales o por tenant, y si `client` debe leer catálogos
