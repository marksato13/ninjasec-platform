# Implementación — Módulo Gestión de Riesgos

> Basado en: `PLANIFICACION/25-MODULO-RIESGOS.md`
> Creado: 2026-08-05 · **Estado: no iniciado**

---

## ⏳ P1 — Registro de riesgos

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `RiskAsset` con valoración CIA | ⏳ | Referencia opcional a `devices` |
| 2 | Modelo `Risk` con cadena causal completa | ⏳ | activo→amenaza→vulnerabilidad |
| 3 | Migración Alembic | ⏳ | |
| 4 | Cálculo automático de `inherent_score` | ⏳ | 🔴 nunca editable a mano |
| 5 | Cálculo de `business_value` = máx(C,I,A) | ⏳ | |
| 6 | `GET/POST/PUT /risks` con guard por organización | ⏳ | |
| 7 | Validación: residual ≤ inherente | ⏳ | 🔴 bloqueo duro |
| 8 | Umbral de aceptación configurable por cliente | ⏳ | |
| 9 | Página `/dashboard/risks` con tabla filtrable | ⏳ | |
| 10 | Formulario de alta con selección de activo | ⏳ | |

## ⏳ P2 — Catálogos y mapa de calor

| # | Requisito | Estado |
|---|-----------|--------|
| 11 | Modelos `Threat` y `Vulnerability` | ⏳ |
| 12 | Seed de amenazas ISO 27005 / MAGERIT | ⏳ |
| 13 | Seed de vulnerabilidades comunes | ⏳ |
| 14 | Distinción catálogo global vs. propio (`is_global`) | ⏳ |
| 15 | **Mapa de calor 5×5** con riesgos posicionados | ⏳ |
| 16 | Clic en celda → listado de riesgos | ⏳ |
| 17 | Vista inherente vs. residual lado a lado | ⏳ |
| 18 | Colores por nivel según la escala definida | ⏳ |

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
