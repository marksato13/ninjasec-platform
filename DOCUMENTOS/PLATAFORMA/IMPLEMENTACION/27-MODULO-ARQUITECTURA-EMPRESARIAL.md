# Implementación — Módulo Arquitectura Empresarial

> Basado en: `PLANIFICACION/27-MODULO-ARQUITECTURA-EMPRESARIAL.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-09 · **Estado: P1 backend + vista mínima hechos**

---

## 🟡 P1 — Repositorio de arquitectura (backend + vista mínima, falta editor visual)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `ArchitectureModel` (baseline/target/transition) | ✅ | `app/db/models/architecture.py` |
| 2 | Modelo `ArchitectureElement` con 5 capas | ✅ | Validación `Literal` en schemas |
| 3 | Modelo `ArchitectureRelationship` con 7 tipos | ✅ | Validación `Literal` en schemas — persistencia básica, **no** valida legalidad de pares según ArchiMate 3.2 (eso es P3) |
| 4 | Migración Alembic | ✅ | `20260809_06_architecture.py` |
| 5 | Campos `source_module` / `source_id` para trazabilidad | ✅ | Persistidos en elementos |
| 6 | `GET/POST/PUT /architecture/models` | ✅ | Router `/architecture` |
| 7 | CRUD de elementos y relaciones | ✅ | Router `/architecture` |
| 8 | Página `/dashboard/architecture` con listado de modelos | 🟡 | Selector de modelo existe; falta formulario de alta (solo se crea por API por ahora) |
| 9 | Vista de listado por capa (tabla, sin lienzo aún) | ✅ | Selector exclusivo de cinco capas |
| 10 | Versionado: `approved` es inmutable, se crea versión nueva | ✅ | Mutaciones devuelven 409; nueva versión vía POST |

### Evidencia verificada — 2026-08-09

- Migración corregida antes de mergear: colisionaba de ID con `20260809_05_audits.py` (issue #24, mergeado un rato antes) — renombrada a `20260809_06` y re-encadenada.
- `created_at`/`updated_at` de `architecture_models` no tenían `nullable=False` en la migración pese a que el modelo los declara obligatorios — corregido; `alembic check` limpio contra un Postgres vacío.
- Tests de persistencia de la propia flota tenían dos bugs reales: no pasaban `organization_id` al crear `ArchitectureModel` ni `model_id` al crear `ArchitectureRelationship` (ambos NOT NULL) — corregidos. Un tercer test comparaba `source_id` como `int` contra una columna `String` — corregido a `str`.
- Verificado manualmente vía API real: crear modelo → aprobar → intentar mutar un modelo aprobado devuelve 409 (regla de inmutabilidad confirmada end-to-end, no solo a nivel de ORM).
- `tsc --noEmit` limpio. Suite completa: 154 passed.

**Pendiente de una fase posterior (no P1):** el formulario de alta de modelos en la UI (fila 8) y el estilo del componente frontend usa clases Tailwind sueltas (`bg-slate-900`, etc.) en vez del sistema de tokens (`--primary`, `--surface`...) que usa el resto del dashboard — funciona pero no respeta el theming claro/oscuro existente.

**Exclusiones explícitas:**

- La sincronización automática de la capa tecnológica desde dispositivos/topología corresponde a **P2** y no está implementada en P1.
- El editor visual con React Flow, paleta ArchiMate, drag-and-drop y creación visual de relaciones corresponde a **P3** y no está implementado.
- La validación completa de relaciones legales según **ArchiMate 3.2** corresponde a **P3** y no está implementada. En este estado ni siquiera se persiste `relationship_type` porque no existen aún las entidades ni endpoints del módulo. Cuando P1 se implemente, si solo se almacena `relationship_type` como valor tipado/enumerado, deberá documentarse como persistencia básica y no como validación ArchiMate 3.2.

## ⏳ P2 — Sincronización de la capa tecnológica

| # | Requisito | Estado | Mapeo |
|---|-----------|--------|-------|
| 11 | `POST /architecture/models/{id}/sync-technology` | ⏳ | — |
| 12 | `Device` tipo `server` → `Node` | ⏳ | |
| 13 | `Device` red → `Device` + `CommunicationNetwork` | ⏳ | |
| 14 | `DeviceConnection` → `Association` / `Flow` | ⏳ | |
| 15 | `ClientSite` → `Location` | ⏳ | |
| 16 | `Integration` → `SystemSoftware` | ⏳ | |
| 17 | `Service` → `TechnologyService` | ⏳ | |
| 18 | Advertencia al editar a mano un elemento sincronizado | ⏳ | |
| 19 | Re-sincronización sin duplicar elementos | ⏳ | |

## ⏳ P3 — Editor visual

| # | Requisito | Estado |
|---|-----------|--------|
| 20 | Lienzo con React Flow (compartido con módulo 23) | ⏳ |
| 21 | Paleta ArchiMate por capa | ⏳ |
| 22 | Arrastrar y soltar elementos | ⏳ |
| 23 | Creación de relaciones tipadas | ⏳ |
| 24 | **Validación de relaciones legales según ArchiMate 3.2** | ⏳ |
| 25 | Filtro de vista por capa | ⏳ |
| 26 | Vista de impacto (qué depende de este nodo) | ⏳ |
| 27 | Confirmación al borrar con conteo de dependencias | ⏳ |

## ⏳ P4 — Gap analysis

| # | Requisito | Estado |
|---|-----------|--------|
| 28 | Modelo `ArchitectureGap` | ⏳ |
| 29 | Comparación baseline vs. target lado a lado | ⏳ |
| 30 | Generación automática de brechas (`new`/`modified`/`eliminated`) | ⏳ |
| 31 | Priorización por valor de negocio y esfuerzo | ⏳ |
| 32 | Validación: target sin baseline no permite comparar | ⏳ |

## ⏳ P5 — Artefactos TOGAF y export

| # | Requisito | Estado |
|---|-----------|--------|
| 33 | Catálogo de elementos exportable | ⏳ |
| 34 | Matriz de relaciones (proceso × aplicación) | ⏳ |
| 35 | Plan de migración con paquetes de trabajo (Fase F) | ⏳ |
| 36 | Export a imagen (PNG/SVG) | ⏳ |
| 37 | Export a ArchiMate Open Exchange (XML) | ⏳ |
| 38 | Importador desde Archi | ⏳ |
| 39 | Export PDF del modelo completo | ⏳ |

---

## Dependencias

| Depende de | Estado | Para qué |
|---|---|---|
| 05 Dispositivos | ✅ | Capa tecnológica (P2) |
| 23 Topología P1 | ⏳ | **Comparte la librería React Flow** |
| 03 Clientes | ✅ | Eje del modelo |
| 25 Riesgos | ⏳ | Priorización del plan de migración (P5) |

⚠️ **Decidir la librería de diagramación en el módulo 23 antes de empezar P3.** Si 23 elige React Flow, aquí se reutilizan componentes y la inversión se amortiza en dos módulos.

---

## Estimación

| Fase | Esfuerzo |
|---|---|
| P1 | 1.5 sesiones |
| P2 | 1 sesión |
| P3 | 3 sesiones ← **el más caro de todo el roadmap** |
| P4 | 1 sesión |
| P5 | 1.5 sesiones |

---

## ⚠️ Decisión de alcance recomendada

**P3 (editor visual completo con validación ArchiMate) es el ítem más caro del roadmap entero.** Herramientas como Archi llevan años en eso y son gratuitas.

**Alternativa pragmática:** saltarse P3 e implementar solo el **importador** de P5. El modelado se hace en Archi (que la academia ya usa), y NinjaSec aporta lo que Archi no puede: la sincronización con infraestructura real y la trazabilidad al dato vivo.

Camino corto sugerido: **P1 → P2 → P4 → P5 (solo import/export)**, dejando P3 fuera salvo que el editor propio sea requisito explícito.

Eso reduce de ~8 sesiones a ~5 sin perder el diferencial.

---

## 🎓 Alineación académica

| Fase | Entregable del curso | Peso |
|---|---|---|
| P1 | U1 — Modelo base | **25%** |
| P4 | U2 — Modelo TOGAF completo | **45%** |

**70% de la nota** del curso Arquitectura Empresarial.

Caso base: **Franco's SAC**, donde la Fase D del ADM ya está implementada en el proyecto ITI y `PLAN_MIGRACION_ORGANIZACION.md` cubre la Fase F. Buena parte del contenido ya existe — falta modelarlo formalmente.
