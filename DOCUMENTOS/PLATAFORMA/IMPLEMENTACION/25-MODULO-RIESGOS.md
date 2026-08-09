# Implementación — Módulo Gestión de Riesgos

> Basado en: `PLANIFICACION/25-MODULO-RIESGOS.md`
> Creado: 2026-08-05 · **Estado: no iniciado**

---

## ⏳ P1 — Registro de riesgos

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `RiskAsset` con valoración CIA | ✅ | `app/db/models/risk.py`; FK opcional `device_id` sin duplicar inventario |
| 2 | Modelo `Risk` con cadena causal completa | ✅ | `app/db/models/risk.py`; amenaza/vulnerabilidad descriptivas en P1 (catálogos quedan en P2) |
| 3 | Migración Alembic | ✅ | `20260809_05_risks.py`; `tests/test_risks_migration.py` verifica FK opcional y constraints; `alembic heads` → `20260809_05 (head)` |
| 4 | Cálculo automático de `inherent_score` | ✅ | Servicio deriva `likelihood × impact`; `tests/test_risks.py` prueba create/update con payload arbitrario y verifica el valor persistido |
| 5 | Cálculo de `business_value` = máx(C,I,A) | ✅ | Recalculado al crear y editar |
| 6 | `GET/POST/PUT /risks` con guard por organización | ✅ | Incluye detalle y DELETE; acceso ajeno responde 404 |
| 7 | Validación: residual ≤ inherente | ✅ | Servicio + constraint DB; `tests/test_risks.py` prueba create y update con respuesta 422 |
| 8 | Umbral de aceptación configurable por cliente | ⏳ | |
| 9 | Página `/dashboard/risks` con tabla filtrable | ✅ | Filtro por cliente; agregado junto con P2 (ver evidencia abajo) — el mapa de calor cumple el rol de "tabla filtrable" visual |
| 10 | Formulario de alta con selección de activo | ✅ | Formulario de alta de activo y de riesgo (con selección de activo por cliente) en la misma página |

## ✅ P2 — Catálogos y mapa de calor

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 11 | Modelos `Threat` y `Vulnerability` | ✅ | `app/db/models/risk.py`; N:N con `Risk` vía `risk_threats`/`risk_vulnerabilities` (no se copia texto, se referencia la fila del catálogo) |
| 12 | Seed de amenazas ISO 27005 / MAGERIT | ✅ | `seed_risk_catalog()` en `app/db/seed.py`: 10 amenazas globales (deliberada/accidental/ambiental) |
| 13 | Seed de vulnerabilidades comunes | ✅ | 10 vulnerabilidades globales (técnica/organizacional/física) en el mismo seed |
| 14 | Distinción catálogo global vs. propio (`is_global`) | ✅ | `organization_id` nulo = global (visible por todos); `UniqueConstraint(organization_id, code)` permite que una organización defina su propio código sin chocar con el catálogo global |
| 15 | **Mapa de calor 5×5** con riesgos posicionados | ✅ | `GET /risks/heatmap` agrupa por `(likelihood, impact)`; página `/dashboard/risks` lo renderiza como grilla 5×5 |
| 16 | Clic en celda → listado de riesgos | ✅ | Cada celda del mapa muestra las tarjetas de los riesgos que caen ahí, con selects para reubicar (`likelihood`/`impact`) sin recargar la página |
| 17 | Vista inherente vs. residual lado a lado | 🟡 | El mapa muestra el score inherente (celda = `likelihood × impact`); el residual ya se calcula y persiste (P1) pero no tiene una segunda grilla dedicada — queda como mejora futura |
| 18 | Colores por nivel según la escala definida | ✅ | 4 bandas de color (`≥20` rojo, `≥12` naranja, `≥6` amarillo, resto verde) |

### Evidencia verificada (2026-08-09)

- Migración `20260809_08_risk_catalogs.py` (encadenada tras `20260809_07`), verificada con `alembic upgrade head` sobre Postgres 16 limpio.
- Suite completa: **166 tests pasan, 1 skip** (incluye `test_risk_catalogs.py` — 7 casos: reutilización de catálogo sin duplicar texto, aislamiento de catálogo propio entre organizaciones, rechazo de código duplicado en la misma org, actualización de asociaciones, referencia inexistente → 404, las 25 celdas del mapa ocupadas, reubicación de un riesgo entre celdas — y `test_risk_catalogs_migration.py`).
- Smoke test manual end-to-end vía `curl`: login → crear cliente → crear activo → crear riesgo con `threat_ids`/`vulnerability_ids` del catálogo global sembrado → `GET /risks/heatmap?client_id=` refleja la celda ocupada → `PUT /risks/{id}/associations` reemplaza amenazas/vulnerabilidades reutilizando filas existentes → crear entrada de catálogo duplicada (`code` ya usado en la misma org) → `409` → referenciar `threat_ids` inexistente → `404`.
- Página `/dashboard/risks` (nueva): formulario de alta de activos y de riesgos con selección de amenazas/vulnerabilidades del catálogo, mapa de calor interactivo y gestión del catálogo (alta rápida de amenaza/vulnerabilidad). Enlazada en el sidebar. `npx tsc --noEmit` sin errores.
- Nota de integración: este issue tenía ramas paralelas (`feat/issue-27-backend`, `test/issue-27`, `docs/issue-27`) generadas por la cola autónoma contra un `main` anterior a que P1 quedara mergeado — reimplementaban `Risk` desde cero sin `RiskAsset`/tratamiento/residual, lo que habría revertido P1. Se descartaron esas ramas y se reconstruyó P2 manualmente **encima** del modelo P1 ya mergeado, conservando ambos.

## ⏳ P3 — Tratamiento y vínculo con controles

| # | Requisito | Estado |
|---|-----------|--------|
| 19 | Modelo `RiskControl` (N:N con controles del SGSI) | ⏳ |
| 20 | Cálculo de riesgo residual tras controles | ⏳ |
| 21 | Plan de tratamiento con responsable y fecha | ⏳ |
| 22 | **Aceptar riesgo: rol admin+, justificación obligatoria, audit log** | ⏳ 🔴 | |
| 23 | Marca de inconsistencia: `treated` sin controles | ⏳ |
| 24 | Alerta de `review_date` vencida | ⏳ |

## ⏳ P4 — Generación automática

| # | Requisito | Estado |
|---|-----------|--------|
| 25 | Hallazgo `critical` → riesgo candidato precargado | ⏳ |
| 26 | `Device.criticality = critical` → activo sugerido | ⏳ |
| 27 | `data_classification = restricted` → confidencialidad 5 | ⏳ |
| 28 | Licencia vencida → vulnerabilidad "sin soporte" | ⏳ |
| 29 | Puerto de gestión sin ACL → vulnerabilidad de exposición | ⏳ |

## ⏳ P5 — Informes

| # | Requisito | Estado |
|---|-----------|--------|
| 30 | Export XLSX del registro de riesgos | ⏳ |
| 31 | PDF ejecutivo: top 10, distribución, evolución | ⏳ |
| 32 | Vista para rol `client` (solo sus riesgos) | ⏳ |

---

## Dependencias

| Depende de | Estado | Para qué |
|---|---|---|
| 05 Dispositivos | ✅ | Activos técnicos y su criticidad |
| 06 Revisiones | ✅ | Generación automática desde hallazgos (P4) |
| 24 Cumplimiento | ⏳ | Vínculo riesgo ↔ control (P3) |
| 18 Alertas | ✅ | Alerta de revisión vencida (P3) |

**P1 y P2 son autónomos.** P3 necesita que exista el catálogo de controles del módulo 24.

---

## Estimación

| Fase | Esfuerzo |
|---|---|
| P1 | 1.5 sesiones |
| P2 | 1.5 sesiones (el seed de catálogos es lo más largo) |
| P3 | 1 sesión |
| P4 | 1 sesión |
| P5 | 1 sesión |

---

## Orden recomendado respecto al módulo 24

Construir **24-P1 → 25-P1 → 25-P2 → 24-P2 → 25-P3**.

Razón: el catálogo de controles debe existir antes de poder asociarlo a riesgos, pero el registro de riesgos aporta valor por sí solo y su mapa de calor es lo más demostrable de los dos módulos en una sustentación.

---

## 🎓 Alineación académica

- **Curso Seguridad de la Información** — la evaluación de riesgos es el núcleo del SGSI (entregable U2)
- **Curso Auditoría de Sistemas** — la auditoría verifica que el tratamiento se ejecutó
- **Entregable E5** (CE032) del perfil de egreso

El mapa de calor es, además, el artefacto que mejor funciona en una sustentación: se entiende en tres segundos sin explicación técnica.
