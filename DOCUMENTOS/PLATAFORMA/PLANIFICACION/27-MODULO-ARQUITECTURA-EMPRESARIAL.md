# Módulo: Arquitectura Empresarial (TOGAF / ArchiMate)

**Ruta prevista:** `/dashboard/architecture`
**Acceso:** `super_admin`, `admin` · `collaborator` (consulta) · `client` (vista de su arquitectura)
**Backend previsto:** `modules/architecture`

---

## ¿Qué es?

Repositorio de arquitectura empresarial siguiendo el ciclo ADM de TOGAF 10 y notación ArchiMate 3.2. Modela las cuatro capas (Negocio, Datos, Aplicación, Tecnología) y el trayecto desde la arquitectura actual (*as-is*) hasta la objetivo (*to-be*), con su plan de migración.

**El diferencial:** la capa de Tecnología **no se dibuja a mano** — se alimenta del inventario real de dispositivos y de la topología. Es el problema crónico de toda herramienta de AE: el modelo nace desactualizado. Aquí la infraestructura ya está en la base de datos.

---

## Fases del ciclo ADM cubiertas

| Fase TOGAF | Cobertura | Fuente |
|---|---|---|
| **Preliminar** | Principios de arquitectura | Manual |
| **A. Visión** | Alcance, stakeholders, motivación | Manual |
| **B. Negocio** | Procesos, actores, servicios de negocio | Manual |
| **C. Datos** | Entidades y flujos de información | Semi-derivada del esquema |
| **C. Aplicación** | Componentes y sus relaciones | Manual + catálogo |
| **D. Tecnología** | Nodos, dispositivos, redes | **Derivada** de [[05 Dispositivos]] y [[23-MODULO-TOPOLOGIA]] |
| **E. Oportunidades** | Brechas entre as-is y to-be | Derivada del gap analysis |
| **F. Migración** | Plan priorizado por valor y riesgo | Semi-derivada de [[25-MODULO-RIESGOS]] |
| **G / H** | Gobierno y gestión del cambio | Vía [[26-MODULO-AUDITORIAS-COBIT]] |

---

## Entidades

### `architecture_models`
| Campo | Descripción |
|---|---|
| `client_id` | Organización modelada |
| `name` / `version` | Identificación del modelo |
| `state` | `baseline` (as-is) · `target` (to-be) · `transition` |
| `adm_phase` | Fase del ciclo en que se encuentra |
| `status` | `draft` · `approved` · `superseded` |

### `architecture_elements`
Elementos ArchiMate. Un solo modelo de datos para las cuatro capas.

| Campo | Descripción |
|---|---|
| `model_id` | Modelo al que pertenece |
| `layer` | `motivation` · `business` · `application` · `technology` · `implementation` |
| `element_type` | Tipo ArchiMate: `BusinessProcess`, `ApplicationComponent`, `Node`, `Device`, `Driver`, `Goal`... |
| `name` / `description` | Identificación |
| `source_module` / `source_id` | **Trazabilidad al dato real** (ej. `devices` / `42`) |
| `properties_json` | Atributos libres del elemento |

### `architecture_relationships`
| Campo | Descripción |
|---|---|
| `source_element_id` / `target_element_id` | Extremos |
| `relationship_type` | `serving` · `assignment` · `realization` · `composition` · `flow` · `triggering` · `association` |
| `label` | Etiqueta opcional |

### `architecture_gaps`
| Campo | Descripción |
|---|---|
| `baseline_model_id` / `target_model_id` | Modelos comparados |
| `gap_type` | `new` · `modified` · `eliminated` |
| `element_ref` / `description` | Qué cambia |
| `priority` / `effort_estimate` / `business_value` | Insumo de priorización |
| `work_package` | Paquete de trabajo del plan de migración (Fase F) |

---

## Derivación de la capa de Tecnología

| Dato NinjaSec | Elemento ArchiMate generado |
|---|---|
| `Device` tipo `server` | `Node` |
| `Device` tipo `firewall` / `router` / `switch` | `Device` + `CommunicationNetwork` |
| `DeviceConnection` | `Association` / `Flow` según `link_type` |
| `ClientSite` | `Location` |
| `Integration` (pfSense/FortiGate/Wazuh) | `SystemSoftware` |
| `Service` del catálogo | `TechnologyService` |

**Un botón "Sincronizar capa tecnológica" y la Fase D se dibuja sola.** Ese es el argumento del módulo entero.

---

## Funcionalidades previstas

### Editor de modelo
Lienzo con paleta ArchiMate por capa, arrastrar y soltar, relaciones tipadas. Validación de relaciones permitidas según la especificación (ArchiMate no admite cualquier relación entre cualquier par de elementos).

### Vistas por capa
Filtro que muestra una capa a la vez, o vistas cruzadas (ej. "qué aplicaciones soportan este proceso de negocio"). Vista de **impacto**: seleccionar un nodo y ver qué se cae si falla.

### Comparación as-is / to-be
Modelos lado a lado con las diferencias resaltadas. Genera automáticamente `architecture_gaps`.

### Catálogos, matrices y diagramas
Los tres artefactos que exige TOGAF: catálogo de elementos, matriz de relaciones (ej. proceso × aplicación), y diagramas por vista. Exportables.

### Plan de migración
Paquetes de trabajo priorizados por valor de negocio y riesgo, con cronograma. Corresponde a la Fase F del ADM.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver modelos | ✅ | ✅ | ✅ | ✅¹ |
| Crear modelo | ✅ | ✅ | ❌ | ❌ |
| Editar elementos y relaciones | ✅ | ✅ | ✅² | ❌ |
| Sincronizar capa tecnológica | ✅ | ✅ | ❌ | ❌ |
| **Aprobar modelo** | ✅ | ❌ | ❌ | ❌ |
| Generar gap analysis | ✅ | ✅ | ❌ | ❌ |
| Exportar (imagen / XML / PDF) | ✅ | ✅ | ✅ | ✅¹ |

¹ Solo modelos `approved` de su propia organización.
² Solo modelos en estado `draft`.

---

## Reglas de negocio

1. **Un modelo `approved` es inmutable.** Modificarlo exige crear una versión nueva y marcar la anterior como `superseded` — es control de configuración básico.
2. Un elemento con `source_module` se sincroniza desde su origen; editarlo a mano rompe la trazabilidad y debe advertirse.
3. Las relaciones se validan contra la especificación ArchiMate 3.2 — no toda relación es legal entre cualquier par de tipos.
4. Solo se comparan modelos del mismo cliente.
5. Un modelo `target` sin `baseline` asociado no permite gap analysis.
6. Eliminar un elemento con relaciones exige confirmación con el conteo de dependencias afectadas.

---

## Alcance por fases

| Fase | Alcance | Entregable académico |
|---|---|---|
| **P1** | Entidades + CRUD de elementos y relaciones + vista por capa | U1 modelo base (25%) |
| **P2** | Sincronización de la capa tecnológica desde dispositivos | — |
| **P3** | Editor visual con paleta ArchiMate y validación de relaciones | — |
| **P4** | Comparación as-is / to-be + gap analysis | U2 modelo TOGAF completo (45%) |
| **P5** | Plan de migración (Fase F) + export a formato ArchiMate | — |

---

## Decisión técnica pendiente

| Opción | A favor | En contra |
|---|---|---|
| **React Flow** | Ya sería dependencia del módulo 23 — una sola librería para topología y AE | Hay que construir la paleta ArchiMate a mano |
| **Archi + import/export** | Herramienta estándar, gratuita, la usa la academia | Modelado fuera de la plataforma; solo se importa |
| **Mermaid** | Cero dependencias | No sirve para modelado interactivo |

**Recomendación: React Flow**, compartiendo componentes con el módulo 23, más importador del formato Open Exchange de ArchiMate para no obligar a modelar todo dentro de la plataforma.

---

## Valor académico

Producto final del curso **Arquitectura Empresarial**: U1 modelo base (25%) y U2 modelo TOGAF completo (45%) = **70% de la nota**. Aplicado al caso Franco's SAC, cuya Fase D ya está implementada en el proyecto ITI y cuyo `PLAN_MIGRACION_ORGANIZACION.md` cubre la Fase F.
