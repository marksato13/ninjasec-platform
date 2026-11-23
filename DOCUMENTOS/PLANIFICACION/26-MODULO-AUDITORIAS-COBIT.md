# Módulo: Auditorías de Sistemas (COBIT 2019 / ISO 19011)

**Ruta prevista:** `/dashboard/audits`
**Acceso:** `super_admin`, `admin` (gestión) · `collaborator` (auditor asignado) · `client` (informe final)
**Backend previsto:** `modules/audits`

---

## ¿Qué es?

Gestión del ciclo completo de una auditoría de sistemas siguiendo ISO 19011:2018 (directrices para auditar) y COBIT 2019 (objetivos de gobierno y gestión de TI): **planificación → programa → ejecución → hallazgos → informe → seguimiento**.

⚠️ **No confundir con el módulo [[16-MODULO-AUDITORIA]]**, que es el audit log técnico. Aquel registra eventos; este gestiona auditorías formales como servicio profesional. El log es *insumo probatorio* de estas auditorías.

---

## Diferencia con el módulo 06 — Revisiones de Seguridad

| Aspecto | 06 Revisiones | 26 Auditorías |
|---|---|---|
| Enfoque | Técnico: configuración de dispositivos | Gobierno: procesos y controles |
| Marco | Checklist propio | COBIT 2019 / ISO 19011 |
| Salida | Hallazgos técnicos | Informe formal con opinión de auditoría |
| Duración | Horas | Semanas |
| Quién lo pide | El equipo técnico | Dirección, cliente, ente regulador |

Son complementarios: una revisión técnica **es evidencia** dentro de una auditoría.

---

## Entidades

### `audits` — el encargo
| Campo | Descripción |
|---|---|
| `client_id` | Auditado |
| `code` | Correlativo (`AUD-2026-001`) |
| `title` / `objective` / `scope` | Definición del encargo |
| `framework` | `cobit_2019` · `iso_27001` · `iso_19011` · `custom` |
| `audit_type` | `internal` · `external` · `certification` · `follow_up` |
| `lead_auditor_id` | Auditor líder |
| `planned_start` / `planned_end` / `actual_end` | Cronograma |
| `status` | `planned` · `in_progress` · `reporting` · `closed` |
| `opinion` | `satisfactory` · `with_observations` · `unsatisfactory` |

### `audit_programs` — pruebas planificadas
| Campo | Descripción |
|---|---|
| `audit_id` | Auditoría a la que pertenece |
| `objective_code` | Objetivo COBIT (`APO13`, `DSS05`) o control ISO |
| `test_procedure` | Procedimiento de prueba a ejecutar |
| `evidence_required` | Qué evidencia hay que obtener |
| `assigned_to` | Auditor responsable |
| `result` | `effective` · `partially_effective` · `ineffective` · `not_tested` |
| `maturity_assessed` | Nivel 0-5, comparable con [[24-MODULO-CUMPLIMIENTO-SGSI]] |

### `audit_findings` — hallazgos
| Campo | Descripción |
|---|---|
| `audit_id` / `program_id` | Origen |
| `severity` | `critical` · `high` · `medium` · `low` · `observation` |
| `condition` / `criteria` / `cause` / `effect` / `recommendation` | **Los 5 atributos del hallazgo según ISO 19011** |
| `management_response` | Respuesta de la dirección auditada |
| `action_plan` / `responsible` / `due_date` | Compromiso de remediación |
| `status` | `open` · `in_progress` · `closed` · `accepted_risk` |

### `audit_evidences`
Evidencia recolectada, con soporte para **evidencia derivada** — igual que en el módulo de cumplimiento: un extracto del audit log, un listado de dispositivos o un hallazgo de revisión se referencian, no se copian.

---

## Los 5 atributos del hallazgo (ISO 19011)

Este es el corazón metodológico del módulo. Un hallazgo sin los cinco atributos no es auditable:

| Atributo | Pregunta que responde |
|---|---|
| **Condición** | ¿Qué se encontró? |
| **Criterio** | ¿Contra qué norma se compara? |
| **Causa** | ¿Por qué ocurrió? |
| **Efecto** | ¿Qué consecuencia tiene? |
| **Recomendación** | ¿Qué debe hacerse? |

El formulario debe forzar los cinco. Es lo que distingue un informe profesional de una lista de quejas.

---

## Funcionalidades previstas

### Plan de auditoría
Documento formal con objetivo, alcance, criterios, equipo, cronograma y recursos. Exportable a PDF. **Es el entregable del 25% del curso de Auditoría de Sistemas.**

### Programa de trabajo
Matriz de objetivos COBIT con procedimientos, responsable, estado y resultado. Vista de avance en porcentaje.

### Papeles de trabajo
Evidencia por prueba, con enlace al módulo origen cuando es derivada. Trazabilidad completa desde el hallazgo hasta el dato que lo sustenta.

### Informe final
Estructura normativa: resumen ejecutivo, alcance, metodología, hallazgos por severidad con los 5 atributos, opinión de auditoría, plan de acción acordado y anexos. **Entregable del 30% del curso, con sustentación.**

### Seguimiento
Auditoría de tipo `follow_up` que verifica el cierre de los hallazgos de una auditoría previa.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver auditorías | ✅ | ✅ | ✅¹ | ✅² |
| Crear auditoría | ✅ | ✅ | ❌ | ❌ |
| Definir programa de trabajo | ✅ | ✅ | ✅¹ | ❌ |
| Registrar resultado de prueba | ✅ | ✅ | ✅¹ | ❌ |
| Registrar hallazgo | ✅ | ✅ | ✅¹ | ❌ |
| **Emitir opinión de auditoría** | ✅ | ✅³ | ❌ | ❌ |
| Responder a un hallazgo | ❌ | ❌ | ❌ | ✅² |
| Cerrar hallazgo | ✅ | ✅ | ❌ | ❌ |
| Exportar informe | ✅ | ✅ | ✅¹ | ✅² |

¹ Solo auditorías donde figura como auditor asignado.
² Solo sus propias auditorías, y solo cuando `status = closed`.
³ Solo si es el `lead_auditor` del encargo.

---

## Reglas de negocio

1. **Independencia del auditor.** Un auditor no puede auditar un cliente donde figura como responsable operativo. El sistema debe bloquearlo — es principio básico de ISO 19011.
2. Un hallazgo sin los 5 atributos completos no puede incluirse en el informe final.
3. El informe solo se emite si todas las pruebas del programa tienen resultado.
4. La opinión la emite exclusivamente el auditor líder.
5. El cliente ve la auditoría **solo cuando está cerrada** — nunca durante la ejecución.
6. Un hallazgo `accepted_risk` debe enlazar al riesgo aceptado en [[25-MODULO-RIESGOS]].
7. Los papeles de trabajo son inmutables una vez cerrada la auditoría.

---

## Alcance por fases

| Fase | Alcance | Entregable académico |
|---|---|---|
| **P1** | Entidades + CRUD de auditoría + plan exportable a PDF | Plan de Auditoría (25%) |
| **P2** | Programa de trabajo + catálogo de objetivos COBIT 2019 | — |
| **P3** | Hallazgos con los 5 atributos + respuesta de la dirección | — |
| **P4** | Informe final PDF con estructura normativa | Informe Final (30%) + sustentación |
| **P5** | Evidencia derivada de audit log, revisiones y cumplimiento | — |
| **P6** | Auditorías de seguimiento | — |

---

## Valor académico

Es el módulo con **encaje más directo** de todo el roadmap: los dos entregables del curso de Auditoría de Sistemas (25% + 30% = 55% de la nota) son exactamente las dos salidas principales de este módulo. Construirlo produce el entregable en lugar de duplicar el trabajo.
