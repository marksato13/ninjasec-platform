# Módulo: Gestión de Riesgos (ISO 27005)

**Ruta prevista:** `/dashboard/risks`
**Acceso:** `super_admin`, `admin` (gestión) · `collaborator` (identificación) · `client` (mapa de calor)
**Backend previsto:** `modules/risks`

---

## ¿Qué es?

Registro de riesgos de seguridad de la información según ISO/IEC 27005. Modela la cadena completa **activo → amenaza → vulnerabilidad → riesgo → tratamiento → riesgo residual**, con valoración cuantificada y mapa de calor.

Es el módulo que le da **sentido causal** al resto: sin riesgos, el SGSI es una lista de controles sin criterio de prioridad, y las revisiones de seguridad son hallazgos sin contexto de negocio.

---

## Entidades

### `risk_assets`
Activo bajo análisis. **No duplica el inventario** — referencia a `devices`, o describe activos intangibles (procesos, información, personas, proveedores).

| Campo | Descripción |
|---|---|
| `client_id` | Dueño del activo |
| `device_id` | FK opcional a `devices` para activos técnicos |
| `name` / `asset_type` | `hardware` · `software` · `information` · `service` · `people` · `facility` |
| `confidentiality` / `integrity` / `availability` | Valoración CIA 1-5 |
| `business_value` | Derivado: máximo de las tres dimensiones |
| `owner_user_id` | Propietario del riesgo |

### `threats` y `vulnerabilities`
Catálogos reutilizables basados en los anexos de ISO 27005 y en MAGERIT.

| Campo | Descripción |
|---|---|
| `code` / `name` / `description` | Identificación |
| `category` | Deliberada · Accidental · Ambiental · Fallo técnico |
| `is_global` | Catálogo del sistema vs. propio de la organización |

### `risks` — el registro
| Campo | Descripción |
|---|---|
| `client_id` / `asset_id` / `threat_id` / `vulnerability_id` | La cadena causal |
| `likelihood` | Probabilidad 1-5 |
| `impact` | Impacto 1-5 |
| `inherent_score` | `likelihood × impact` (1-25) antes de controles |
| `treatment` | `mitigate` · `transfer` · `avoid` · `accept` |
| `residual_likelihood` / `residual_impact` / `residual_score` | Tras aplicar controles |
| `status` | `identified` · `assessed` · `treated` · `accepted` · `closed` |
| `owner_user_id` / `review_date` | Responsable y próxima revisión |

### `risk_controls`
Relación N:N entre riesgos y controles de [[24-MODULO-CUMPLIMIENTO-SGSI]] — qué control mitiga qué riesgo y cuánto reduce el score.

---

## Escala de valoración

| Score inherente | Nivel | Color | Acción requerida |
|---|---|---|---|
| 20-25 | Crítico | 🔴 | Tratamiento inmediato, escala a dirección |
| 12-19 | Alto | 🟠 | Plan de tratamiento con fecha comprometida |
| 6-11 | Medio | 🟡 | Tratamiento planificado |
| 3-5 | Bajo | 🟢 | Aceptable con monitoreo |
| 1-2 | Muy bajo | ⚪ | Aceptable |

El umbral de aceptación es **configurable por cliente** — no todas las organizaciones toleran lo mismo.

---

## Alimentación automática desde otros módulos

| Origen | Qué genera |
|---|---|
| **06 Revisiones** — hallazgo `critical` | Riesgo candidato precargado con impacto alto |
| **05 Dispositivos** — `criticality = critical` | Activo con `business_value` alto sugerido |
| **05 Dispositivos** — `data_classification = restricted` | Confidencialidad 5 sugerida |
| **18 Alertas** — licencia vencida | Vulnerabilidad "software sin soporte" |
| **23 Topología** — puerto de gestión sin ACL | Vulnerabilidad de exposición |

**El hallazgo técnico se convierte en riesgo de negocio automáticamente.** Ese salto es lo que un consultor cobra caro y lo que las PYMEs nunca hacen.

---

## Funcionalidades previstas

### Mapa de calor
Matriz 5×5 probabilidad × impacto con los riesgos posicionados. Clic en celda → listado de riesgos de esa combinación. Vista inherente vs. residual lado a lado.

### Registro de riesgos
Tabla filtrable por cliente, activo, nivel, tratamiento y responsable. Exportable a XLSX — formato estándar de entrega en consultoría.

### Plan de tratamiento
Por cada riesgo con `treatment = mitigate`, los controles asociados con responsable, fecha y estado. Alimenta el plan de implementación del SGSI.

### Informe de riesgos
PDF ejecutivo: top 10 riesgos, distribución por nivel, evolución del riesgo residual, riesgos vencidos sin revisar.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver registro de riesgos | ✅ | ✅ | ✅ | ✅¹ |
| Identificar riesgo | ✅ | ✅ | ✅ | ❌ |
| Valorar (probabilidad × impacto) | ✅ | ✅ | ✅ | ❌ |
| **Aceptar un riesgo** | ✅ | ✅ | ❌ | ❌ |
| Asignar tratamiento y responsable | ✅ | ✅ | ❌ | ❌ |
| Administrar catálogos de amenazas | ✅ | ❌ | ❌ | ❌ |
| Exportar informe | ✅ | ✅ | ✅ | ✅¹ |

¹ Solo sus propios riesgos, en vista ejecutiva.

---

## Reglas de negocio

1. **Aceptar un riesgo es una decisión de dirección.** Requiere rol admin o superior, justificación obligatoria y queda en el audit log con autor y fecha.
2. Un riesgo con score residual mayor al inherente es un error de datos — el sistema lo bloquea.
3. Un riesgo `treated` sin controles asociados es inconsistente: se marca en rojo.
4. Los riesgos tienen `review_date`; vencido sin revisar, genera alerta ([[18-MODULO-ALERTAS]]).
5. El score inherente **nunca se edita a mano**: se deriva de probabilidad × impacto.
6. Cerrar un riesgo exige evidencia del control implementado.

---

## Alcance por fases

| Fase | Alcance |
|---|---|
| **P1** | Entidades + registro CRUD + cálculo de scores + mapa de calor |
| **P2** | Catálogos de amenazas y vulnerabilidades (seed ISO 27005 / MAGERIT) |
| **P3** | Vínculo con controles del SGSI + riesgo residual |
| **P4** | Generación automática de riesgos desde hallazgos críticos |
| **P5** | Informe PDF ejecutivo + export XLSX |

---

## Valor académico

Insumo directo de tres frentes:
- **Curso Seguridad de la Información** — la evaluación de riesgos es el núcleo del SGSI (U2)
- **Curso Auditoría de Sistemas** — la auditoría verifica que el tratamiento se ejecutó
- **Entregable E5** (CE032) del perfil de egreso
