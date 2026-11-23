# Implementación — Módulo Documentos y Recursos

> Basado en: `PLANIFICACION/19-MODULO-DOCUMENTOS.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Entidades

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `DocType` con `scope` (public/private/both) | ✅ | `db/models/doc_type.py` |
| 2 | Modelo `ProjectDoc` con visibility, status y enabled | ✅ | `db/models/project_doc.py` |
| 3 | Trazabilidad `created_by` / `updated_by` / `verified_by` | ✅ | `project_doc.py` |
| 4 | `preview_md` para vista previa sin salir de la app | ✅ | `project_doc.py` (máx. 4000 chars) |
| 5 | Enums `DocScope`, `DocVisibility`, `DocStatus` | ✅ | `db/models/enums.py` |

### Endpoints

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 6 | `GET /doc-types` abierto a roles autenticados | ✅ | `modules/docs/routers/router.py:55` |
| 7 | `POST` / `PUT /doc-types` solo super_admin | ✅ | `router.py:65` / `:90` |
| 8 | `GET /project-docs` con filtros project/status/visibility | ✅ | `router.py:114` |
| 9 | `POST` / `PUT /project-docs` con guard por membresía | ✅ | `router.py:160` / `:223` |
| 10 | `POST /project-docs/{id}/verify` solo super_admin | ✅ | `router.py:276` |
| 11 | `POST /project-docs/{id}/toggle` | ✅ | `router.py:324` |

### Filtrado de seguridad

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 12 | Cliente ve solo `visibility = client` | ✅ | `router.py` → `_get_client_profile` |
| 13 | Cliente ve solo documentos de sus proyectos | ✅ | doble filtro proyecto + visibilidad |
| 14 | Colaborador acota por `project_members` | ✅ | `router.py` → `_get_project_member` |

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 15 | `/portal/documents` con iconografía por tipo de archivo | ✅ | `(portal)/portal/documents/page.tsx` → `fileIcon()` |
| 16 | `/portal/resources` con filtros y modal de vista previa | ✅ | `(portal)/portal/resources/page.tsx` |
| 17 | Solo documentos `enabled` en el portal | ✅ | `resources/page.tsx` → `docs.filter(d => d.enabled)` |
| 18 | Fechas en formato `es-PE` | ✅ | ambas páginas → `toLocaleDateString("es-PE")` |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~19-P-01~~ | ~~**Upload real de archivos**~~ | — | ✅ **Resuelto 2026-08-08**: filesystem local persistente (`STORAGE_PATH`, volumen `uploads_data`) con descarga autenticada por FastAPI, aislamiento por organización, validación MIME y límite de 10 MB. `github_url` permanece sin cambios como alternativa válida. Tests E2E en `tests/test_file_storage.py` |
| 19-P-02 | Versionado de documentos | 🟡 Media | Editar pisa el contenido anterior; no hay historial de versiones |
| 19-P-03 | Búsqueda de texto completo | 🟡 Media | Solo se filtra por proyecto y estado, no por contenido |
| 19-P-04 | Render real de Markdown | 🟡 Media | `preview_md` se muestra como texto plano, sin formatear |
| 19-P-05 | Descarga masiva del dossier del cliente | 🟢 Baja | Un ZIP con todos los documentos `client` sería un buen entregable de cierre |
| 19-P-06 | Fecha de caducidad documental | 🟢 Baja | Contratos y SLA vencen; nada lo vigila |

---

## Decisión de arquitectura a preservar

### Backend elegido (2026-08-08)

Se eligió **filesystem local persistente** en lugar de MinIO: el despliegue actual es de un solo nodo y no justifica otro servicio ni credenciales. Los archivos viven en el volumen Docker `uploads_data`; FastAPI autoriza cada descarga (rol, proyecto y tenant), por lo que Caddy conserva el proxy `/api/*` y no expone el volumen como directorio público. Si se escala a varios nodos, la interfaz `LocalStorage` es el punto de sustitución por almacenamiento de objetos.

**La plataforma no aloja archivos, aloja punteros.** Es una decisión correcta y consistente con el criterio del proyecto: evita duplicar versionado, no convierte a NinjaSec en un file server y mantiene la fuente de verdad donde el equipo ya trabaja.

`19-P-01` **no debe romper esa decisión.** Lo correcto es agregar el upload como *una opción más* (`file_url` propio) manteniendo `github_url` como camino preferente, no sustituirla.

⚠️ Aplica también a documentación de terceros: los datasheets de fabricantes se **enlazan a su URL oficial**, nunca se rehospedan. Ver [[29-MODULO-CATALOGO-EQUIPOS]].
