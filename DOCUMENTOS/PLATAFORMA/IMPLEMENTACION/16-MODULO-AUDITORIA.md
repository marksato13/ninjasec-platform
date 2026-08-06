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

### Frontend

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 11 | Página `/dashboard/audit` con listado cronológico | ✅ | `(admin)/dashboard/audit/page.tsx` |
| 12 | Enlace profundo desde Usuarios (`?entity_id=`) | ✅ | `(admin)/dashboard/users/page.tsx` → "Ver auditoría" |
| 13 | Oculto en el sidebar para collaborator y client | ✅ | `components/dashboard/sidebar.tsx` |

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
| 16-P-01 | **Exportar a PDF/XLSX** | 🔴 Alta | Requisito directo del curso de Auditoría y del entregable E5. Sin export, la evidencia no sale de la plataforma |
| 16-P-02 | Filtro por rango de fechas en la UI | 🟡 Media | Un auditor pide "todo lo del trimestre", no "todo" |
| 16-P-03 | Filtro por usuario autor | 🟡 Media | Clave para investigar una cuenta concreta |
| 16-P-04 | Paginación server-side | 🟡 Media | Con 86 registros seed va bien; a 50.000 la página se cae |
| 16-P-05 | Sello de integridad (hash encadenado) | 🟢 Baja | Un `previous_hash` por fila haría detectable cualquier manipulación directa en DB. Valor alto para ISO 27001 A.8.15 |
| 16-P-06 | Registro de IP y user-agent | 🟡 Media | Hoy se sabe quién y qué, no desde dónde |

---

## Verificación de inmutabilidad

Confirmado por lectura de `modules/audit/routers/router.py`: el router expone **un solo endpoint `GET`**. No hay `POST`, `PUT`, `PATCH` ni `DELETE`. La única vía de inserción es `AuditService`, invocado desde el propio backend.

⚠️ La inmutabilidad se sostiene a nivel de aplicación, no de base de datos. Alguien con acceso directo a PostgreSQL puede alterar la tabla. `16-P-05` cerraría ese hueco.
