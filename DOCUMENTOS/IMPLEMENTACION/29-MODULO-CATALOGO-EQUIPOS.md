# Implementación — Módulo Catálogo de Equipos de Red

> Basado en: `PLANIFICACION/29-MODULO-CATALOGO-EQUIPOS.md`
> Creado: 2026-08-05 · **Estado: P1 y P2 cerrados 2026-08-10 (issue #85)**

---

## ✅ P1 — Catálogo con filtros facetados

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `CatalogDevice` con specs completas | ✅ | `db/models/catalog_device.py` — sin `organization_id`, catálogo global (mismo criterio que `Skill`/`DocType`/`Role`) |
| 2 | Migración Alembic | ✅ | `20260809_03_catalog_devices.py` |
| 3 | `slug` único e inmutable | ✅ | `UniqueConstraint`; `CatalogDeviceUpdate` ni siquiera expone el campo `slug` — no hay forma de mandarlo por `PUT` |
| 4 | `GET /catalog/devices` con filtros combinables | ✅ | `modules/device_catalog/routers/router.py` — brand, category, subcategory, osi_layer, segment, lifecycle_status, poe, stackable, rack_mountable, managed, `q` (búsqueda libre por marca/modelo/tags) |
| 5 | CRUD restringido a admin y super_admin | ✅ | Lectura: super_admin/admin/collaborator. Escritura: super_admin/admin |
| 6 | Carga inicial de prueba | ✅ | Ampliado de 4 a 22 modelos (issue #85) — Cisco, MikroTik, Ubiquiti, Fortinet, Juniper, Aruba, Huawei, TP-Link, Synology, APC, Dell — cubre las 8 categorías del doc de planificación y los vendors ya presentes en NetDoctor/integraciones. Sigue sin ser un catálogo real completo (no es el objetivo de este módulo). |
| 7 | Página `/dashboard/catalog-devices` | ✅ | `app/(admin)/dashboard/catalog-devices/page.tsx` — issue #85. Ruta con guion (`catalog-devices`), no `/catalog/devices/...` como decía el doc original, para no chocar con el prefijo `/catalog/devices` de la API. |
| 8 | Filtros facetados con conteo por faceta | 🟡 **Parcial** | Filtros combinables sí (marca, categoría, ciclo de vida, PoE, gestionable); conteo por faceta individual (cuántos resultados tendría cada opción del filtro) no implementado — no lo pide ningún criterio de aceptación concreto, queda como mejora futura si se necesita. |
| 9 | Búsqueda difusa por marca, modelo y tags | 🟡 **Parcial** | El backend usa `ilike` (substring, no difusa de verdad tipo Fuse.js) — suficiente para el volumen actual del catálogo. |
| 10 | Cards con badge de `lifecycle_status` | ✅ | Badge de color por `active`/`eos`/`eol` en cada card del listado. |

Validado con `tests/test_catalog_devices.py`: filtros combinados, filtro por `lifecycle_status`, slug duplicado rechazado (400), slug no cambia aunque se mande en el `PUT`, colaborador consulta pero no crea (403).

Los 3 agentes de la flota no generaron ningún commit para el issue original de P1 (#18); se completó manualmente. P1-UI y P2 completos (#85) también manuales.

## ✅ P2 — Ficha y enlaces (issue #85, 2026-08-10)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 11 | Modelo `CatalogDeviceLink` con 5 tipos de enlace | ✅ | `db/models/catalog_device_link.py` — `datasheet`/`config_manual`/`firmware`/`eol_notice`/`security_advisory` (validación de valor libre en `link_type`, no un `Enum` de Postgres — mismo criterio pragmático que otros campos "tipo" de la plataforma) |
| 12 | Campo `archive_url` (respaldo Wayback) | ✅ | Campo existe y se acepta en `POST /links`; no hay verificación automática de enlaces caídos todavía — eso es P5 |
| 13 | Modelo `CatalogDeviceSummary` — resumen propio | ✅ | `db/models/catalog_device_summary.py`, único por modelo (`UniqueConstraint`), editable por super_admin/admin/collaborator (igual que dice el doc de planificación en § Acciones disponibles — más permisivo que la edición del modelo en sí, que es solo admin) |
| 14 | Página de ficha con specs, enlaces y resumen | ✅ | `app/(admin)/dashboard/catalog-devices/[id]/page.tsx` |
| 15 | **Verificar que NO se alojan PDFs de fabricantes** | ✅ 🔴 | `CatalogDeviceLinkCreate` solo acepta `url`/`archive_url` (texto), no hay ningún endpoint de subida de archivos en este módulo — estructuralmente imposible rehospedar un PDF aquí |
| 16 | Cita de la fuente en cada resumen | ✅ 🔴 | Campo `source_note`, con placeholder en el formulario del frontend recordándolo |

### Adelanto parcial de P3 (fuera del alcance formal de P2, agregado por valor directo)

`GET /catalog/devices/{id}` incluye `instance_count`: cuántos `Device` del parque instalado de la organización actual tienen el mismo `vendor`/`model` (comparación case-insensitive por texto, sin FK). Es lo que el doc de planificación describe en § Funcionalidades previstas → "Ficha del modelo", aunque la tabla de fases lo ubica en P3. **No incluye la alerta automática de EOL** — ver P3 abajo, eso sigue pendiente.

## ⏳ P3 — Cruce con inventario ← mayor retorno

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 17 | Campo `catalog_device_id` en `devices` (nullable) | ⏳ | El cruce actual (#85) es por texto vendor/model, no por FK — más frágil (dos formas de escribir el mismo modelo no matchean) pero cero fricción de datos. Migrar a FK es la mejora real de P3. |
| 18 | Vinculación automática por marca + modelo | 🟡 **Parcial** | El conteo (`instance_count`) ya hace este match por texto (case-insensitive) desde #85; falta la vinculación persistente (escribir el `catalog_device_id` en cada `Device`) |
| 19 | "N instancias en el parque" en la ficha del modelo | ✅ | Adelantado en #85 (ver arriba) — vía match por texto, no FK |
| 20 | **Alerta de EOL sobre el inventario del cliente** | ⏳ 🔥 | Sigue siendo la funcionalidad de mayor retorno del módulo, sin implementar |
| 21 | Alerta anticipada 6 meses antes del EOL | ⏳ | |
| 22 | Informe de renovación por cliente | ⏳ | |

## ⏳ P4 — Comparador

| # | Requisito | Estado |
|---|-----------|--------|
| 23 | Selección de hasta 4 modelos | ⏳ |
| 24 | Tabla comparativa con diferencias resaltadas | ⏳ |
| 25 | Export del comparativo a PDF | ⏳ |

## ⏳ P5 — Mantenimiento de enlaces

| # | Requisito | Estado |
|---|-----------|--------|
| 26 | Job de verificación periódica de URLs | ⏳ |
| 27 | Marca de enlace caído sin eliminarlo | ⏳ |
| 28 | Sugerencia automática del respaldo en archivo web | ⏳ |
| 29 | `last_checked_at` visible en la ficha | ⏳ |

## ⏳ P6 — Vínculo con NetDoctor

| # | Requisito | Estado |
|---|-----------|--------|
| 30 | Comandos aplicables por modelo y firmware | ⏳ |
| 31 | Advertencias conocidas por modelo | ⏳ |

---

## Dependencias

| Depende de | Estado | Para qué |
|---|---|---|
| 05 Dispositivos | ✅ | Cruce con inventario (P3) |
| 18 Alertas | ✅ | Alerta de EOL (P3) |
| 28 NetDoctor | ⏳ | Vínculo comandos-modelo (P6) |

**Sin bloqueos.** P1 puede empezar cuando se decida.

---

## Estimación

| Fase | Esfuerzo | Valor |
|---|---|---|
| P1 | 1.5 sesiones | Medio (la carga de datos es lo más largo) |
| P2 | 1 sesión | Medio |
| **P3** | **1 sesión** | 🔥 **Muy alto** |
| P4 | 0.5 sesión | Medio |
| P5 | 0.5 sesión | Bajo |
| P6 | 0.5 sesión | Medio |

---

## ⚠️ Regla de copyright — verificar en cada fase

**Los datasheets de fabricantes NO se alojan en la plataforma.** Son propiedad de Cisco, Huawei, MikroTik y demás.

Política obligatoria:
1. Enlazar a la URL oficial del fabricante
2. Respaldo al Wayback Machine si la URL cae (los enlaces de Cisco y Huawei se rompen a menudo)
3. Resumen ejecutivo **propio** con cita de la fuente

Misma política que [[19-MODULO-DOCUMENTOS]]: la plataforma aloja punteros, no archivos de terceros.

---

## Justificación de existencia

**P3 es la única razón por la que este módulo pertenece a NinjaSec.** El cruce catálogo × inventario responde una pregunta que ninguna PYME sabe contestar: *"¿qué equipos míos ya no tienen soporte del fabricante?"* — y convierte el catálogo en un motor de oportunidades comerciales de renovación.

Sin P3, esto es una wiki y debería vivir como proyecto estático de portafolio en GitHub Pages, no dentro de la plataforma.

**Recomendación: si se implementa, llegar hasta P3. Si no se va a llegar a P3, no empezar.**
