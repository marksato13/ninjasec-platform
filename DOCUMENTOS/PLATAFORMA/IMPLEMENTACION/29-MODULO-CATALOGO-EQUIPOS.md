# Implementación — Módulo Catálogo de Equipos de Red

> Basado en: `PLANIFICACION/29-MODULO-CATALOGO-EQUIPOS.md`
> Creado: 2026-08-05 · **Estado: P1 backend hecho 2026-08-09, falta UI**

---

## 🟡 P1 — Catálogo con filtros facetados (backend hecho, falta UI)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `CatalogDevice` con specs completas | ✅ | `db/models/catalog_device.py` — sin `organization_id`, catálogo global (mismo criterio que `Skill`/`DocType`/`Role`) |
| 2 | Migración Alembic | ✅ | `20260809_03_catalog_devices.py` |
| 3 | `slug` único e inmutable | ✅ | `UniqueConstraint`; `CatalogDeviceUpdate` ni siquiera expone el campo `slug` — no hay forma de mandarlo por `PUT` |
| 4 | `GET /catalog/devices` con filtros combinables | ✅ | `modules/device_catalog/routers/router.py` — brand, category, subcategory, osi_layer, segment, lifecycle_status, poe, stackable, rack_mountable, managed, `q` (búsqueda libre por marca/modelo/tags) |
| 5 | CRUD restringido a admin y super_admin | ✅ | Lectura: super_admin/admin/collaborator. Escritura: super_admin/admin |
| 6 | Carga inicial de prueba | 🟡 **Parcial** | 4 modelos de ejemplo (Cisco, MikroTik, Ubiquiti — incluye uno `eol` para poder probar ese filtro), no los 20-30 reales que pide el doc de planificación — issue #18 solo pedía "seed mínimo para poder probar los filtros", no un catálogo real completo |
| 7 | Página `/dashboard/catalog/devices` | ⏳ | Fuera del alcance de #18 (backend-only) |
| 8 | Filtros facetados con conteo por faceta | ⏳ | Requiere la UI (#7) |
| 9 | Búsqueda difusa por marca, modelo y tags | ⏳ | El backend ya soporta `q` (`ilike`, no difusa de verdad); falta la UI |
| 10 | Cards con badge de `lifecycle_status` | ⏳ | Requiere la UI (#7) |

Validado con `tests/test_catalog_devices.py`: filtros combinados, filtro por `lifecycle_status`, slug duplicado rechazado (400), slug no cambia aunque se mande en el `PUT`, colaborador consulta pero no crea (403).

Los 3 agentes de la flota no generaron ningún commit para este issue; se completó manualmente.

## ⏳ P2 — Ficha y enlaces

| # | Requisito | Estado |
|---|-----------|--------|
| 11 | Modelo `CatalogDeviceLink` con 5 tipos de enlace | ⏳ |
| 12 | Campo `archive_url` (respaldo Wayback) | ⏳ |
| 13 | Modelo `CatalogDeviceSummary` — resumen propio | ⏳ |
| 14 | Página de ficha con specs, enlaces y resumen | ⏳ |
| 15 | **Verificar que NO se alojan PDFs de fabricantes** | ⏳ 🔴 |
| 16 | Cita de la fuente en cada resumen | ⏳ 🔴 |

## ⏳ P3 — Cruce con inventario ← mayor retorno

| # | Requisito | Estado |
|---|-----------|--------|
| 17 | Campo `catalog_device_id` en `devices` (nullable) | ⏳ |
| 18 | Vinculación automática por marca + modelo | ⏳ |
| 19 | "N instancias en el parque" en la ficha del modelo | ⏳ |
| 20 | **Alerta de EOL sobre el inventario del cliente** | ⏳ 🔥 |
| 21 | Alerta anticipada 6 meses antes del EOL | ⏳ |
| 22 | Informe de renovación por cliente | ⏳ |

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
