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
| 5 | Unicidad de `name` y `slug` | ⚠️ | `unique=True` **global**, no compuesta con `organization_id` — ver `20-P-09` |

### Endpoints

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 6 | `GET /areas` | ✅ | `modules/catalogs/routers/router.py:15` |
| 7 | `GET /project-types` | ✅ | `router.py:25` |
| 8 | `GET /products` | ⚠️ | `router.py:37` — existe pero **sin filtro de organización**, ver `20-P-08` |
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
| 20-P-06 | Endpoints `POST`/`PUT` para areas y project-types | 🔴 Alta | Bloquea `20-P-01` y `20-P-02` — el backend ni siquiera los expone |
| 20-P-07 | Aviso de uso antes de desactivar | 🟡 Media | Desactivar un área usada por 12 proyectos debería advertirlo |
| 20-P-08 | **`GET /products` no filtra por organización** | 🔴 **Crítica** | `catalogs/routers/router.py:37` devuelve los productos de **todas** las organizaciones. `Product.organization_id` es `nullable=False`, o sea es dato por tenant. Cualquier autenticado —**incluido un `client`**— lo lee |
| 20-P-09 | **`unique` global en catálogos multi-tenant** | 🔴 Alta | `Area.name`, `Area.slug`, `ProjectType.name`, `ProjectType.slug` son `unique=True` sin incluir `organization_id`. Dos organizaciones no pueden tener ambas un área "Redes" |
| 20-P-10 | `organization_id` nullable en `Area` y `ProjectType` | 🟡 Media | Un registro con `organization_id = NULL` es visible para todos sin que ninguna regla lo declare. Decidir: o es catálogo global explícito, o es `NOT NULL` |
| 20-P-11 | Los catálogos los lee el rol `client` | 🟡 Media | `catalogs/routers/router.py` solo exige `get_current_user`. Un cliente no debería enumerar las áreas internas ni los productos de la consultora |

---

## 🔴 Riesgo de aislamiento entre organizaciones

`20-P-08` es el pendiente más grave de los módulos 15-22 y no estaba detectado en la primera pasada.

**Verificado en el código:** `list_products()` ejecuta `select(Product).where(Product.is_active == True)` sin cláusula de organización, mientras que sus vecinos —`collection`, `organizations`, `devices`— sí filtran por `current_user.organization_id`. Es una omisión puntual, no un criterio de diseño.

**Hoy el impacto es nulo** porque solo existe una organización en la base. **Deja de serlo el día que entre la segunda**, y para entonces el endpoint ya estará en producción.

**Fix:** una línea — `.where(Product.organization_id == current_user.organization_id)`. El coste de arreglarlo ahora es trivial; el de arreglarlo después incluye avisar a los clientes afectados.

`20-P-09` es el complemento: sin unicidad compuesta, el segundo tenant no puede ni dar de alta sus propios catálogos.

---

## Estado real del módulo

Es el módulo **menos completo** de los ya construidos: hoy funciona como *visor* de catálogos, no como panel de administración. De 3 catálogos, solo `doc_types` tiene escritura.

**Orden de trabajo recomendado:**
1. `20-P-08` — filtro por organización en `GET /products` *(va primero: es una línea y es el único con consecuencia externa)*
2. `20-P-06` — exponer `POST`/`PUT` de areas y project-types en el backend
3. `20-P-09` — unicidad compuesta con `organization_id` *(requiere migración; hacerlo antes de que haya datos que colisionen)*
4. `20-P-01` y `20-P-02` — conectar la UI
5. `20-P-04` — toggle de `is_active` con el aviso de `20-P-07`
6. `20-P-05` — pestaña de umbrales (desbloquea `18-P-02`)

Estimación: 1 sesión de trabajo. Es scope contenido y desbloquea pendientes de otros dos módulos.
