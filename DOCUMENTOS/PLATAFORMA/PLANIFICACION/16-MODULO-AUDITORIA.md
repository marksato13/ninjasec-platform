# Módulo: Auditoría (Audit Log)

**Ruta:** `/dashboard/audit`
**Acceso:** `super_admin`, `admin`
**Backend:** `modules/audit` · prefijo `/audit-logs`

---

## ¿Qué es?

Registro inmutable de toda operación crítica ejecutada en la plataforma. Es la evidencia que sostiene la trazabilidad ante un cliente, un auditor externo o una revisión ISO 27001 (control A.8.15 — Registro de eventos).

No es un log técnico: es un **registro de negocio**. Responde "quién cambió qué, cuándo y sobre qué entidad".

---

## Entidad

Tabla `audit_logs`:

| Campo | Descripción |
|---|---|
| `organization_id` | Aísla los logs por organización — nunca se cruzan |
| `user_id` | Autor de la acción (nullable: procesos automáticos del sistema) |
| `action` | Verbo namespaceado: `alerts.refresh`, `client.delete`, `review.close` |
| `entity_type` | Dominio afectado: `client`, `device`, `user`, `review`, `alerts` |
| `entity_id` | Identificador del registro tocado (string, admite claves compuestas) |
| `metadata_json` | Contexto adicional serializado (máx. 1000 chars) |
| `created_at` | Timestamp UTC |

---

## Cómo se alimenta

Los módulos escriben vía el servicio compartido, **después** de confirmar la mutación:

```python
AuditService(db).record(
    org_id,          # organización
    "alerts.refresh",# acción
    "alerts",        # entity_type
    "integrations:3,devices:12",  # entity_id / contexto
    current_user.id, # autor
)
```

Convención de `action`: `<dominio>.<verbo>` en minúsculas e inglés.

---

## Funcionalidades

- Listado cronológico descendente (lo más reciente primero)
- Filtro por `entity_type` y por `entity_id`
- **Enlace profundo desde otros módulos:** el módulo Usuarios enlaza a `/dashboard/audit?entity_id=<id>` para ver el historial de una cuenta puntual
- Aislamiento por organización aplicado en el query, no en la vista

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver registro de auditoría | ✅ | ✅ | ❌ | ❌ |
| Filtrar por entidad | ✅ | ✅ | ❌ | ❌ |
| Editar o borrar un registro | ❌ | ❌ | ❌ | ❌ |

**Nadie puede modificar el audit log.** No existe endpoint de escritura ni de borrado expuesto — la única vía de inserción es `AuditService`. Un log editable no sirve como evidencia.

---

## Reglas de negocio

1. **Inmutabilidad absoluta.** Sin `PUT`, sin `DELETE`, sin excepciones para super_admin.
2. Se registra **después** del commit, nunca antes: si la operación falla, no deja rastro falso.
3. Jamás se escriben contraseñas, tokens ni JWT en `metadata_json`.
4. El `user_id` nulo identifica acciones del sistema (jobs, refresh automático).
5. La retención es indefinida — el purgado requeriría una decisión documentada del negocio.

---

## Conexión con otros módulos

| Módulo | Qué aporta al log |
|---|---|
| Usuarios | altas, cambios de rol, bajas |
| Clientes | alta, edición, eliminación |
| Revisiones | cierre de revisión, cambio de severidad de hallazgos |
| Alertas | ejecución de `refresh` en batch |
| Aprobaciones | verificación de skills, certificaciones y documentos |
| Postulaciones | cambios de estado y asignaciones |

Este módulo es la base probatoria del futuro **26 — Auditorías COBIT / ISO 19011**.
