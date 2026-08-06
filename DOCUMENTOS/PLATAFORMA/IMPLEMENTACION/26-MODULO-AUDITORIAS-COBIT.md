# Implementación — Módulo Auditorías de Sistemas

> Basado en: `PLANIFICACION/26-MODULO-AUDITORIAS-COBIT.md`
> Creado: 2026-08-05 · **Estado: no iniciado**

---

## ⏳ P1 — Encargo y plan de auditoría

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `Audit` con tipo, marco, cronograma y opinión | ⏳ | |
| 2 | Migración Alembic | ⏳ | |
| 3 | Correlativo automático `AUD-2026-NNN` | ⏳ | |
| 4 | `GET/POST/PUT /audits` con guard por organización | ⏳ | |
| 5 | **Validación de independencia del auditor** | ⏳ 🔴 | No puede auditar donde es responsable operativo |
| 6 | Página `/dashboard/audits` con listado y filtros | ⏳ | |
| 7 | Formulario de alta: objetivo, alcance, criterios, equipo | ⏳ | |
| 8 | **Export del Plan de Auditoría a PDF** | ⏳ | Entregable 25% del curso |

## ⏳ P2 — Programa de trabajo

| # | Requisito | Estado |
|---|-----------|--------|
| 9 | Modelo `AuditProgram` con procedimiento y resultado | ⏳ |
| 10 | Seed del catálogo de objetivos COBIT 2019 | ⏳ |
| 11 | Asignación de pruebas a auditores | ⏳ |
| 12 | Registro de resultado (`effective` a `ineffective`) | ⏳ |
| 13 | Nivel de madurez 0-5 por objetivo | ⏳ |
| 14 | Vista de avance en porcentaje | ⏳ |

## ⏳ P3 — Hallazgos

| # | Requisito | Estado |
|---|-----------|--------|
| 15 | Modelo `AuditFinding` con los **5 atributos ISO 19011** | ⏳ 🔴 |
| 16 | Formulario que **obliga** condición/criterio/causa/efecto/recomendación | ⏳ 🔴 |
| 17 | Respuesta de la dirección auditada | ⏳ |
| 18 | Plan de acción con responsable y fecha | ⏳ |
| 19 | Vínculo `accepted_risk` → riesgo aceptado del módulo 25 | ⏳ |
| 20 | Cierre de hallazgo con evidencia | ⏳ |

## ⏳ P4 — Informe final

| # | Requisito | Estado |
|---|-----------|--------|
| 21 | Modelo `AuditEvidence` (manual + derivada) | ⏳ |
| 22 | **Export del Informe Final a PDF** con estructura normativa | ⏳ | Entregable 30% del curso |
| 23 | Secciones: resumen ejecutivo, alcance, metodología, hallazgos, opinión, plan, anexos | ⏳ |
| 24 | Validación: no se emite si hay pruebas sin resultado | ⏳ 🔴 |
| 25 | Opinión emitida solo por el `lead_auditor` | ⏳ 🔴 |
| 26 | Cliente ve la auditoría solo con `status = closed` | ⏳ 🔴 |

## ⏳ P5 — Evidencia derivada

| # | Requisito | Estado | Origen |
|---|-----------|--------|--------|
| 27 | Extracto del audit log por periodo | ⏳ | Módulo 16 |
| 28 | Hallazgos de revisiones técnicas como evidencia | ⏳ | Módulo 06 |
| 29 | Estado de controles del SGSI | ⏳ | Módulo 24 |
| 30 | Inventario de activos con propietario | ⏳ | Módulo 05 |
| 31 | Papeles de trabajo inmutables tras el cierre | ⏳ 🔴 | — |

## ⏳ P6 — Seguimiento

| # | Requisito | Estado |
|---|-----------|--------|
| 32 | Auditoría tipo `follow_up` enlazada a una previa | ⏳ |
| 33 | Verificación de cierre de hallazgos anteriores | ⏳ |
| 34 | Comparativa de madurez entre auditorías | ⏳ |

---

## Dependencias

| Depende de | Estado | Impacto |
|---|---|---|
| 16 Auditoría (audit log) | ✅ | Evidencia derivada (P5) |
| 06 Revisiones | ✅ | Evidencia técnica (P5) |
| 13 Usuarios | ✅ | Auditores y validación de independencia |
| 24 Cumplimiento | ⏳ | Estado de controles (P5) |
| 25 Riesgos | ⏳ | Riesgos aceptados (P3) |

**P1 a P4 son autónomos.** Solo la evidencia derivada necesita los módulos 24 y 25.

---

## Estimación

| Fase | Esfuerzo |
|---|---|
| P1 | 1.5 sesiones |
| P2 | 1.5 sesiones (el seed COBIT es lo más largo) |
| P3 | 1 sesión |
| P4 | 1.5 sesiones (el PDF normativo tiene mucha estructura) |
| P5 | 1 sesión |
| P6 | 0.5 sesión |

---

## 🎓 Alineación académica — la más directa del roadmap

| Fase | Entregable del curso | Peso |
|---|---|---|
| **P1** | Plan de Auditoría | **25%** |
| **P4** | Informe Final de Auditoría + sustentación | **30%** |

**55% de la nota** del curso Auditoría de Sistemas sale de dos exports de este módulo. Construirlo **produce** el entregable en lugar de duplicar trabajo.

Aplicado sobre la infraestructura de Franco's SAC, además genera evidencia para la rúbrica E5 "Registro y Auditoría" del perfil de egreso.

---

## ⚠️ Nota sobre el nombre

Coexisten dos módulos con nombre parecido y hay que mantenerlos separados en la UI:

| Módulo | Nombre en el sidebar | Qué es |
|---|---|---|
| 16 | **Registro de actividad** | Audit log técnico, inmutable |
| 26 | **Auditorías** | Encargos formales de auditoría |

Usar etiquetas distintas evita confundir al usuario y al equipo.
