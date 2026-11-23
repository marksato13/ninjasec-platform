# Implementación — Módulo Auditoría

> Basado en: `PLANIFICACION/16-MODULO-AUDITORIA.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Persistencia

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `AuditLog` con 7 campos | ✅ | `db/models/audit_log.py` |
| 2 | `organization_id` obligatorio (aislamiento multi-tenant) | ✅ | `audit_log.py` |
| 3 | `user_id` nullable para acciones del sistema | ✅ | `audit_log.py` |
| 4 | `metadata_json` para contexto adicional | ✅ | `audit_log.py` (máx. 1000 chars) |

### Servicio

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 5 | `AuditService.record(org, action, entity_type, entity_id, user_id)` | ✅ | `modules/audit/services/audit_service.py` |
| 6 | Se invoca **después** del commit de la mutación | ✅ | Convención aplicada en todos los módulos |
| 7 | Convención `<dominio>.<verbo>` para `action` | ✅ | ej. `alerts.refresh` |

### Endpoint

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 8 | `GET /audit-logs/` restringido a super_admin y admin | ✅ | `modules/audit/routers/router.py:15` |
| 9 | **Sin endpoint de escritura ni borrado** | ✅ | Verificado: el router solo expone `GET` |
| 10 | Filtro por `entity_type` / `entity_id` | ✅ | `router.py` query params |
| 10.1 | Export PDF/XLSX del audit log | ✅ | `GET /audit-logs/export?format=pdf|xlsx` |
| 10.2 | Export aplica filtros activos | ✅ | `action`, `entity_type`, `entity_id` |
| 10.3 | Política de volumen definida | ✅ | Límite server-side de 5.000 eventos más recientes; header `X-Export-Limit: 5000` |

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 11 | Página `/dashboard/audit` con listado cronológico | ✅ | `(admin)/dashboard/audit/page.tsx` |
| 12 | Enlace profundo desde Usuarios (`?entity_id=`) | ✅ | `(admin)/dashboard/users/page.tsx` → "Ver auditoría" |
| 13 | Oculto en el sidebar para collaborator y client | ✅ | `components/dashboard/sidebar.tsx` |
| 13.1 | Botones de exportación PDF/XLSX | ✅ | `(admin)/dashboard/audit/page.tsx` llama `exportAuditLogs()` con filtros actuales |

### Módulos que alimentan el log

| # | Módulo emisor | Estado |
|---|---------------|--------|
| 14 | Usuarios (alta, cambio de rol, baja) | ✅ |
| 15 | Clientes (alta, edición, eliminación) | ✅ |
| 16 | Revisiones de seguridad (cierre, hallazgos) | ✅ |
| 17 | Alertas (`alerts.refresh`) | ✅ |
| 18 | Aprobaciones (verificación de skills/certs/docs) | ✅ |
| 19 | Postulaciones (cambios de estado y asignaciones) | ✅ |
| 20 | Dispositivos (alta, edición, retiro) | ✅ |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~16-P-01~~ | ~~Exportar a PDF/XLSX~~ | ✅ **Implementado** | Export disponible en PDF y XLSX, con filtros aplicados, límite documentado de 5.000 eventos y pruebas reproducibles de archivos válidos, filtros, volumen alto y cero resultados |
| 16-P-02 | Filtro por rango de fechas en la UI | 🟡 Media | Un auditor pide "todo lo del trimestre", no "todo" |
| 16-P-03 | Filtro por usuario autor | 🟡 Media | Clave para investigar una cuenta concreta |
| 16-P-04 | Paginación server-side | 🟡 Media | Con 86 registros seed va bien; a 50.000 la página se cae |
| 16-P-05 | Sello de integridad (hash encadenado) | 🟢 Baja | Un `previous_hash` por fila haría detectable cualquier manipulación directa en DB. Valor alto para ISO 27001 A.8.15 |
| 16-P-06 | Registro de IP y user-agent | 🟡 Media | Hoy se sabe quién y qué, no desde dónde |

---

## Cierre de 16-P-01 — Export PDF/XLSX

### Comportamiento implementado

| Aspecto | Trazabilidad |
|---|---|
| Endpoint | `GET /api/v1/audit-logs/export` |
| Autorización | Mismo guard del listado: `super_admin` y `admin` mediante `require_roles(RoleCode.SUPER_ADMIN, RoleCode.ADMIN)` |
| Formato solicitado | Query param obligatorio `format=pdf` o `format=xlsx` |
| Orden | Cronológico descendente por `created_at` y desempate por `id` descendente |
| Multi-tenant | Todas las consultas filtran `AuditLog.organization_id == current_user.organization_id` |
| Nombre de archivo | `auditoria_YYYYMMDD_HHMMSS.pdf` o `auditoria_YYYYMMDD_HHMMSS.xlsx` |
| Resultado vacío | Devuelve archivo válido con encabezados y sin filas de datos; no responde 404 |

### Formatos y columnas

Ambos formatos exportan las mismas 4 columnas para que PDF y XLSX sean comparables:

| Columna | Origen |
|---|---|
| Fecha | `AuditLog.created_at`, formateado como `YYYY-MM-DD HH:MM:SS` |
| Usuario | `User.full_name`; si no hay usuario enlazado usa `Usuario #<id>` o `Sistema` |
| Acción | `AuditLog.action` |
| Entidad afectada | `AuditLog.entity_type` + `#<entity_id>` cuando existe ID |

El XLSX usa una hoja llamada `Auditoría`, encabezado corporativo, anchos fijos, `freeze_panes = "A2"` y autofiltro `A1:D1`.

El PDF usa orientación horizontal A4, título `Registro de auditoría`, tabla con encabezado repetible y filas alternadas para lectura en evidencias impresas.

### Filtros aplicados

Los exports aceptan y aplican los mismos filtros que la UI mantiene activos:

| Filtro | Query param | Semántica |
|---|---|---|
| Acción | `action` | Coincidencia exacta contra `AuditLog.action` |
| Tipo de entidad | `entity_type` | Coincidencia exacta contra `AuditLog.entity_type` |
| ID de entidad | `entity_id` | Coincidencia exacta contra `AuditLog.entity_id` |

La UI envía solo filtros no vacíos desde `exportAuditLogs(format, filters)`. Los botones `Exportar PDF` y `Exportar XLSX` quedan deshabilitados mientras se genera el archivo para evitar descargas duplicadas.

### Límite y paginación

No se incorporó paginación completa en `16-P-01`; esa necesidad sigue registrada como `16-P-04`.

Para evitar respuestas enormes y consumo excesivo de memoria, el export aplica una política explícita de límite:

- `EXPORT_LIMIT = 5_000`
- se exportan los 5.000 eventos más recientes que cumplen los filtros
- la respuesta incluye `X-Export-Limit: 5000`
- el listado `GET /audit-logs/` valida `limit` entre 1 y 5.000 cuando se solicita

Esta política cubre el entregable E5 sin introducir un flujo de jobs ni almacenamiento temporal.

### Dependencias elegidas

| Dependencia | Uso | Estado |
|---|---|---|
| `openpyxl==3.1.5` | Generación XLSX | Ya existía en `backend/requirements.txt`; se reutiliza |
| `reportlab==4.4.2` | Generación PDF | Ya existía en `backend/requirements.txt`; se reutiliza |

No se agregó motor PDF nuevo. Se reutilizó ReportLab, que ya estaba en la plataforma para reportes consolidados y PDFs de revisiones.

### Evidencia verificable

Pruebas backend agregadas: `PY-MK/backend/tests/test_audit_exports.py`.

Comando reproducible:

```bash
cd PY-MK/backend
PYTHONPATH=. pytest -q tests/test_audit_exports.py
```

Evidencia cubierta por las pruebas:

| Criterio | Validación reproducible |
|---|---|
| PDF válido | `GET /api/v1/audit-logs/export?format=pdf` responde 200, bytes inician con `%PDF-`, terminan en `%%EOF` y pesan más de 1 KB |
| XLSX válido | `openpyxl.load_workbook(BytesIO(response.content), read_only=True)` abre el archivo y verifica encabezados |
| Filtros aplicados | Se insertan dos eventos (`client.created` y `device.updated`), se exporta con `action=client.created&entity_type=client&entity_id=audit-export-match` y solo aparece la fila esperada |
| Grandes volúmenes | La respuesta expone `X-Export-Limit: 5000`; el query de export usa `.limit(EXPORT_LIMIT)` antes de materializar filas |
| Cero resultados | Con `entity_id=does-not-exist`, XLSX conserva solo encabezados y PDF sigue siendo un archivo válido |

Validación esperada en la suite completa:

```bash
cd PY-MK/backend
PYTHONPATH=. pytest -q
```

La validación de frontend queda cubierta por build estándar:

```bash
cd PY-MK/frontend
npm ci
NEXT_PUBLIC_API_URL=/api/v1 npm run build
```

---

## Verificación de inmutabilidad

Confirmado por lectura de `modules/audit/routers/router.py`: el router expone solo endpoints `GET` (`/` y `/export`). No hay `POST`, `PUT`, `PATCH` ni `DELETE`. La única vía de inserción es `AuditService`, invocado desde el propio backend.

⚠️ La inmutabilidad se sostiene a nivel de aplicación, no de base de datos. Alguien con acceso directo a PostgreSQL puede alterar la tabla. `16-P-05` cerraría ese hueco.
