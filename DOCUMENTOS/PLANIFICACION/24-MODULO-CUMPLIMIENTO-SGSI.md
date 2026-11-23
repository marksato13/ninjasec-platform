# Módulo: Cumplimiento y SGSI (ISO 27001)

**Ruta prevista:** `/dashboard/compliance`
**Acceso:** `super_admin`, `admin` (gestión) · `collaborator` (evidencias) · `client` (informe de estado)
**Backend previsto:** `modules/compliance`

---

## ¿Qué es?

Sistema de Gestión de Seguridad de la Información basado en ISO/IEC 27001:2022. Gestiona el catálogo de controles del Anexo A, la Declaración de Aplicabilidad (SoA), el análisis de brechas y la evidencia que respalda cada control.

**El diferencial frente a llevar el SGSI en Excel:** la evidencia no se adjunta a mano — se **deriva de datos que la plataforma ya tiene**. El control A.8.1 (inventario de activos) se evidencia solo con el módulo Dispositivos; A.8.15 (registro de eventos) con el audit log; A.8.8 (gestión de vulnerabilidades) con los hallazgos de las revisiones.

---

## Doble propósito

| Uso | Detalle |
|---|---|
| **Producto** | Funcionalidad vendible: ninguna PYME peruana tiene SGSI y la certificación se está volviendo requisito para contratar con el Estado y con grandes empresas |
| **Académico** | Producto final del curso **Seguridad de la Información** (ISO 27001/27002/27005) y entregable **E5** del perfil de egreso (CE032) |

---

## Entidades

### `compliance_frameworks`
Marcos soportados: ISO 27001:2022, NIST CSF 2.0, CIS Controls v8, Ley 29733 (Protección de Datos Personales - Perú).

| Campo | Descripción |
|---|---|
| `name` / `version` / `slug` | Identificación del marco |
| `is_active` | Marcos disponibles para la organización |

### `compliance_controls`
El catálogo de controles de cada marco.

| Campo | Descripción |
|---|---|
| `framework_id` | Marco al que pertenece |
| `code` | `A.8.1`, `ID.AM-1`, `CIS-1.1` |
| `title` / `description` | Enunciado del control |
| `category` | Organizacional · Personas · Físico · Tecnológico (las 4 de ISO 27002:2022) |
| `parent_code` | Jerarquía de controles |

### `client_control_status` — la Declaración de Aplicabilidad
Estado de cada control **para un cliente concreto**.

| Campo | Descripción |
|---|---|
| `client_id` / `control_id` | El par que define la fila |
| `applicability` | `applicable` · `not_applicable` (con justificación obligatoria) |
| `implementation_status` | `not_implemented` · `planned` · `partial` · `implemented` |
| `maturity_level` | 0-5 (escala CMMI, compatible con COBIT) |
| `justification` | Obligatoria si `not_applicable` — lo exige la norma |
| `responsible_user_id` | Dueño del control |
| `target_date` | Fecha comprometida de implementación |
| `last_assessed_at` | Última evaluación |

### `control_evidences`
Evidencia que respalda el control.

| Campo | Descripción |
|---|---|
| `control_status_id` | A qué control-cliente respalda |
| `evidence_type` | `manual` · `derived` |
| `source_module` | Para las derivadas: `devices`, `audit`, `reviews`, `tickets` |
| `source_query` | Consulta que la produce (evidencia viva, se recalcula) |
| `document_id` | FK a `project_docs` para las manuales |
| `collected_at` | Cuándo se recogió |

---

## Evidencia derivada — el corazón del módulo

| Control ISO 27001:2022 | Módulo NinjaSec | Evidencia automática |
|---|---|---|
| A.5.9 Inventario de activos | 05 Dispositivos | Listado con propietario y clasificación |
| A.5.10 Uso aceptable de activos | 05 Dispositivos | `data_classification` por activo |
| A.5.12 Clasificación de la información | 05 Dispositivos | Distribución de `data_classification` |
| A.5.15 Control de acceso | 01 Roles | Matriz de roles y permisos vigente |
| A.5.16 Gestión de identidades | 13 Usuarios | Altas, bajas y cambios de rol |
| A.5.24 Gestión de incidentes | 07 Tickets | Tickets de seguridad con tiempos de respuesta |
| A.8.8 Gestión de vulnerabilidades | 06 Revisiones | Hallazgos abiertos por severidad |
| A.8.9 Gestión de configuración | 23 Topología | Configuraciones parseadas y diferencias |
| A.8.15 Registro de eventos | 16 Auditoría | Audit log íntegro del periodo |
| A.8.16 Monitoreo de actividades | 18 Alertas | Alertas generadas y atendidas |

**Ese mapeo es la propuesta de valor completa del módulo.** Es lo que hace que el SGSI se mantenga solo en vez de morir a los tres meses.

---

## Funcionalidades previstas

### Panel de cumplimiento
- Porcentaje global por marco y por categoría
- Semáforo por control con nivel de madurez
- Radar de las 4 categorías ISO 27002
- Evolución temporal del porcentaje de cumplimiento

### Gap analysis
Comparación entre estado actual y objetivo, priorizada por riesgo (consume [[25-MODULO-RIESGOS]]). Salida: lista ordenada de brechas con esfuerzo estimado.

### Declaración de Aplicabilidad (SoA)
Documento normativo obligatorio para certificar. Export a XLSX y PDF con los 93 controles del Anexo A, su aplicabilidad, justificación y estado.

### Plan de implementación
Cronograma de controles pendientes con responsable y fecha, exportable. Es el entregable **U3** del curso de Seguridad.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver panel de cumplimiento | ✅ | ✅ | ✅ | ✅¹ |
| Editar estado de un control | ✅ | ✅ | ❌ | ❌ |
| Declarar no aplicable + justificar | ✅ | ✅ | ❌ | ❌ |
| Adjuntar evidencia manual | ✅ | ✅ | ✅ | ❌ |
| Exportar SoA | ✅ | ✅ | ❌ | ⏳ |
| Administrar catálogo de marcos | ✅ | ❌ | ❌ | ❌ |

¹ Solo su propia organización, con vista ejecutiva simplificada.

---

## Reglas de negocio

1. **Un control `not_applicable` sin justificación es inválido.** La norma lo exige y el sistema debe bloquearlo.
2. La evidencia derivada **se recalcula**, no se congela: si el inventario se degrada, el control baja solo.
3. Un control `implemented` sin evidencia asociada se marca como **no verificado** — declarar no es cumplir (mismo principio que [[21-MODULO-SKILLS-CERTIFICACIONES]]).
4. El porcentaje de cumplimiento solo cuenta controles aplicables.
5. Cambiar el estado de un control queda en el audit log — es evidencia de la propia gestión del SGSI.
6. La madurez usa escala 0-5 para ser directamente comparable con COBIT ([[26-MODULO-AUDITORIAS-COBIT]]).

---

## Alcance por fases

| Fase | Alcance | Entregable académico |
|---|---|---|
| **P1** | Catálogo ISO 27001:2022 (93 controles) + SoA editable + % de cumplimiento | U1 análisis normativo (15%) |
| **P2** | Evidencia derivada de los 10 controles mapeados arriba | U2 diseño preliminar SGSI (25%) |
| **P3** | Gap analysis + plan de implementación + export PDF/XLSX | U3 plan de implementación (30%) |
| **P4** | Segundo marco (NIST CSF) y comparación cruzada | — |

**Nota de carga:** cargar 93 controles es trabajo de datos, no de código. Se resuelve con un seed JSON, no a mano.
