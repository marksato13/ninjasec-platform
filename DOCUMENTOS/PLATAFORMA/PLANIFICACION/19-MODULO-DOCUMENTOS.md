# Módulo: Documentos y Recursos

**Ruta:** `/portal/documents` · `/portal/resources` · gestión desde `/dashboard/approvals`
**Acceso:** `super_admin`, `admin`, `collaborator` (internos) · `client` (solo visibilidad `client`)
**Backend:** `modules/docs` · prefijos `/doc-types` y `/project-docs`

---

## ¿Qué es?

Repositorio documental ligado a proyectos. Cada documento es un **puntero con contexto**, no un archivo alojado: guarda título, resumen, vista previa en Markdown y el enlace real (típicamente GitHub).

Esa decisión es deliberada — evita convertir la plataforma en un file server, elimina el problema de versionado duplicado y mantiene la fuente de verdad donde el equipo ya trabaja.

---

## Entidades

### `doc_types` — catálogo

| Campo | Descripción |
|---|---|
| `name` | Nombre único del tipo (Manual, Runbook, Contrato, SLA, Acta...) |
| `scope` | `public` · `private` · `both` — dónde puede usarse el tipo |
| `is_active` | Permite retirar un tipo sin borrarlo |

### `project_docs` — el documento

| Campo | Descripción |
|---|---|
| `project_id` / `doc_type_id` | A qué proyecto pertenece y de qué tipo es |
| `title` / `summary` | Identificación legible |
| `github_url` | Enlace al archivo real |
| `preview_md` | Vista previa en Markdown (máx. 4000 chars) sin salir de la plataforma |
| `visibility` | `internal` (solo equipo) · `client` (visible en el portal) |
| `status` | `draft` · `active` · `archived` |
| `enabled` | Interruptor rápido de visibilidad sin cambiar el estado |
| `created_by` / `updated_by` / `verified_by` / `verified_at` | Trazabilidad completa |

---

## Las dos vistas del portal

| Vista | Ruta | Qué muestra |
|---|---|---|
| **Documentos** | `/portal/documents` | Entregables del cliente. Iconografía por tipo de archivo (PDF rojo, Excel verde, Word azul) y creación de documentos propios |
| **Recursos** | `/portal/resources` | Material de consulta con `visibility: internal`, filtrable por proyecto y estado, con vista previa en modal |

---

## Funcionalidades

- Filtros por proyecto, estado y visibilidad
- Vista previa Markdown en modal — no obliga a abrir el enlace externo
- Icono y color automáticos según el tipo de documento detectado en el nombre o la URL
- Verificación por `super_admin` desde la bandeja de aprobaciones
- Toggle `enabled` para ocultar sin destruir

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Listar tipos de documento | ✅ | ✅ | ✅ | ✅ |
| Crear / editar tipo de documento | ✅ | ❌ | ❌ | ❌ |
| Listar documentos internos | ✅ | ✅ | ✅ | ❌ |
| Listar documentos con `visibility=client` | ✅ | ✅ | ✅ | ✅ |
| Crear documento | ✅ | ✅ | ✅¹ | ❌ |
| Editar documento | ✅ | ✅ | ✅¹ | ❌ |
| Verificar documento | ✅ | ❌ | ❌ | ❌ |
| Activar / desactivar | ✅ | ❌ | ❌ | ❌ |

¹ Solo en proyectos donde el colaborador figura como miembro (`project_members`).

---

## Reglas de negocio

1. **`visibility` es la frontera de seguridad.** Un documento `internal` jamás llega al portal del cliente; el filtro se aplica en el backend.
2. El cliente solo ve documentos de **sus propios proyectos** — doble filtro: proyecto y visibilidad.
3. Los documentos se archivan o desactivan, **nunca se borran**: el histórico del proyecto es parte del entregable.
4. `preview_md` está limitado a 4000 caracteres — es un resumen, no el documento completo.
5. Un documento en `draft` no se publica al cliente aunque su visibilidad sea `client`.
6. La plataforma **no aloja archivos**: solo enlaces. Cualquier PDF de terceros se enlaza a su fuente oficial.

---

## Conexión con otros módulos

- **12 — Proyectos:** todo documento cuelga de un proyecto
- **17 — Aprobaciones:** verificación y activación
- **14 — Portal Cliente:** consumo final por el cliente
- **20 — Configuración:** administración del catálogo `doc_types`
