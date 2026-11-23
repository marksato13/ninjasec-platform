# Implementación — Módulo Cumplimiento y SGSI

> Basado en: `PLANIFICACION/24-MODULO-CUMPLIMIENTO-SGSI.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-09 · **Estado: P1 backend hecho, falta UI**

---

## 🟡 P1 — Catálogo y Declaración de Aplicabilidad (backend hecho, falta UI)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `ComplianceFramework` | ✅ | `db/models/compliance.py` — global, sin `organization_id` (catálogo, no dato de negocio) |
| 2 | Modelo `ComplianceControl` con jerarquía | ✅ | `parent_code` derivado del código (`A.5.1` → `A.5`) |
| 3 | Modelo `ClientControlStatus` | ✅ | El núcleo de la SoA, `UniqueConstraint(client_id, control_id)` |
| 4 | Migración Alembic | ✅ | `20260809_04_compliance.py` |
| 5 | **Seed ISO 27001:2022 — 93 controles del Anexo A** | ✅ | `modules/compliance/iso27001_2022.py` — 37 Organizacional + 8 Personas + 14 Físico + 34 Tecnológico. ⚠️ Cargado de memoria del modelo (no del texto oficial, que es de pago) — **verificar códigos y títulos contra el estándar comprado antes de un compromiso de auditoría real con un cliente**, la advertencia queda en el propio archivo |
| 6 | Categorización ISO 27002:2022 (4 categorías) | ✅ | `category` en cada control: Organizational/People/Physical/Technological |
| 7 | `GET/PUT /compliance/controls` | ✅ | `GET` lista con estado efectivo; `PUT /compliance/controls/{id}?client_id=` crea o actualiza la fila de la SoA |
| 8 | `GET /compliance/soa?client_id=` | ✅ | Resumen + arreglo completo de controles con estado |
| 9 | Validación: `not_applicable` exige justificación | ✅ | 422 si falta — validado ANTES de tocar la sesión de BD (ver nota de bug abajo) |
| 10 | Cálculo de % sobre controles aplicables | ✅ | Excluye `not_applicable` del denominador |
| 11 | Página `/dashboard/compliance` con listado y filtros | ⏳ | Fuera del alcance del issue de esta ronda (backend-only, mismo criterio que 29-P1) |
| 12 | Edición inline de estado y madurez | ⏳ | Requiere la UI (#11) |

Validado con `tests/test_compliance_soa.py`: seed carga exactamente 93 controles (vía la función real de seed, no datos insertados a mano en el test), defaults sin fila previa, persistencia de campos, `not_applicable` sin justificación → 422, cálculo de % excluyendo no aplicables, aislamiento cross-tenant, colaborador consulta pero no edita.

**Bug encontrado y corregido en el camino:** la validación de `not_applicable`/`justification` originalmente ocurría *después* de mutar el objeto SQLAlchemy y hacer `db.add()`, así que un rechazo (422) dejaba la sesión con un registro pendiente sin commit — el siguiente request sobre esa misma sesión fallaba con 500. Se reordenó para validar antes de tocar la sesión.

Los 3 agentes de la flota corrieron sobre este issue: backend y tests no generaron ningún commit, y docs generó documentación extremadamente detallada (migración, seed, 8 endpoints con ejemplos curl, tabla de tablas) que describía el módulo como completamente implementado — pero el diff real solo tocaba este .md y un archivo de test que se salta a sí mismo si el módulo no existe. Se cerró ese PR sin fusionar y se completó manualmente.

## ⏳ P2 — Evidencia derivada

| # | Requisito | Estado | Control ISO |
|---|-----------|--------|-------------|
| 13 | Modelo `ControlEvidence` (manual + derivada) | ⏳ | — |
| 14 | Motor de evidencia derivada por `source_query` | ⏳ | — |
| 15 | Evidencia A.5.9 desde Dispositivos | ⏳ | Inventario de activos |
| 16 | Evidencia A.5.10 / A.5.12 desde `data_classification` | ⏳ | Clasificación |
| 17 | Evidencia A.5.15 desde matriz de roles | ⏳ | Control de acceso |
| 18 | Evidencia A.5.16 desde Usuarios | ⏳ | Gestión de identidades |
| 19 | Evidencia A.5.24 desde Tickets | ⏳ | Gestión de incidentes |
| 20 | Evidencia A.8.8 desde Revisiones | ⏳ | Vulnerabilidades |
| 21 | Evidencia A.8.9 desde Topología | ⏳ | Configuración — depende de `23-P3` |
| 22 | Evidencia A.8.15 desde Audit Log | ⏳ | Registro de eventos |
| 23 | Evidencia A.8.16 desde Alertas | ⏳ | Monitoreo |
| 24 | Marca "no verificado" si `implemented` sin evidencia | ⏳ | 🔴 regla clave |

## ⏳ P3 — Gap analysis y export

| # | Requisito | Estado |
|---|-----------|--------|
| 25 | Comparación estado actual vs. objetivo | ⏳ |
| 26 | Priorización por riesgo (consume módulo 25) | ⏳ |
| 27 | Plan de implementación con responsable y fecha | ⏳ |
| 28 | **Export SoA a XLSX** | ⏳ |
| 29 | **Export SoA a PDF** | ⏳ |
| 30 | Panel: % global, radar de 4 categorías, evolución | ⏳ |
| 31 | Vista ejecutiva para el rol `client` | ⏳ |

## ⏳ P4 — Segundo marco

| # | Requisito | Estado |
|---|-----------|--------|
| 32 | Seed NIST CSF 2.0 | ⏳ |
| 33 | Mapeo cruzado ISO 27001 ↔ NIST CSF | ⏳ |
| 34 | Seed Ley 29733 (Protección de Datos - Perú) | ⏳ |

---

## Dependencias

| Depende de | Estado | Impacto |
|---|---|---|
| 05 Dispositivos | ✅ | Evidencia A.5.9 / A.5.10 / A.5.12 |
| 16 Auditoría | ✅ | Evidencia A.8.15 |
| 06 Revisiones | ✅ | Evidencia A.8.8 |
| 07 Tickets | ✅ | Evidencia A.5.24 |
| 18 Alertas | ✅ | Evidencia A.8.16 |
| 23 Topología P3 | ⏳ | Evidencia A.8.9 — **la única bloqueada** |
| 25 Riesgos | ⏳ | Priorización del gap analysis (P3) |

**P1 y P2 pueden empezar sin esperar nada** salvo la evidencia A.8.9.

---

## Estimación

| Fase | Esfuerzo | Nota |
|---|---|---|
| P1 | 2 sesiones | El seed de 93 controles es carga de datos, no código |
| P2 | 2 sesiones | Donde está el diferencial real |
| P3 | 1.5 sesiones | |
| P4 | 1 sesión | |

---

## 🎓 Alineación académica

| Fase | Entregable | Peso |
|---|---|---|
| P1 | U1 — Análisis de normativas | 15% |
| P2 | U2 — Diseño preliminar del SGSI | 25% |
| P3 | U3 — Plan de implementación | 30% |

Curso **Seguridad de la Información** + entregable **E5** (CE032) del perfil de egreso. Los tres productos suman el 70% de la nota del curso.

⚠️ Los entregables de mayor peso caen en la última semana del semestre. **Empezar P1 con margen.**
