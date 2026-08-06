# Implementación — Módulo Habilidades y Certificaciones

> Basado en: `PLANIFICACION/21-MODULO-SKILLS-CERTIFICACIONES.md`
> Documentado retroactivamente: 2026-08-05 (módulo ya construido)

---

## Checklist de implementación

### Entidades

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `Skill` (catálogo global con categoría) | ✅ | `db/models/skill.py` |
| 2 | Modelo `UserSkill` con nivel y estado | ✅ | `db/models/user_skill.py` |
| 3 | Modelo `UserCertification` con emisor y credencial | ✅ | `db/models/user_certification.py` |
| 4 | `issued_at` / `expires_at` para vigencia | ✅ | `user_certification.py` |
| 5 | Enums `SkillStatus` y `CertificationStatus` | ✅ | `db/models/enums.py` |
| 6 | `verified_by` + `verified_at` en ambas tablas | ✅ | ambos modelos |

### Endpoints — Skills

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 7 | `GET /skills/` catálogo abierto | ✅ | `modules/skills/routers/router.py:30` |
| 8 | `POST /skills/` alta en catálogo | ✅ | `router.py:38` |
| 9 | `GET /skills/user-skills` | ✅ | `router.py:62` |
| 10 | `POST /skills/user-skills` (autodeclaración) | ✅ | `router.py:94` |
| 11 | `PUT /skills/user-skills/{id}` | ✅ | `router.py:168` |
| 12 | `POST /skills/user-skills/{id}/verify` solo super_admin | ✅ | `router.py:220` |

### Endpoints — Certificaciones

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 13 | `GET /user-certifications/` | ✅ | `modules/certifications/routers/router.py:26` |
| 14 | `POST /user-certifications/` | ✅ | `router.py:38` |
| 15 | `PUT /user-certifications/{id}` | ✅ | `router.py:84` |
| 16 | `POST /user-certifications/{id}/verify` solo super_admin | ✅ | `router.py:125` |

### Integración con otros módulos

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 17 | Certificaciones visibles en el directorio de colaboradores | ✅ | `(admin)/dashboard/collaborators/page.tsx` |
| 18 | Verificación centralizada en la bandeja de aprobaciones | ✅ | `(admin)/dashboard/approvals/page.tsx` |
| 19 | Registro en audit log de cada verificación | ✅ | vía `AuditService` |

---

## Pendientes detectados

| # | Pendiente | Prioridad | Detalle |
|---|-----------|-----------|---------|
| ~~21-P-01~~ | ~~**Re-verificación al editar**~~ | — | ✅ **Resuelto 2026-08-06**: `app/common/verification.py` → `revoke_verification_if_changed()`. Editar `level` de una skill aprobada la devuelve a `pending` y limpia `verified_by`/`verified_at`. Reenviar el mismo valor no revoca. Tests en `tests/test_reverification_on_edit.py` (6) |
| ~~21-P-02~~ | ~~**Expiración automática**~~ | — | ✅ **Resuelto 2026-08-06**: campos derivados `is_expired`, `days_until_expiry` y `effective_status` en `UserCertificationRead`. No muta el `status` almacenado: se recalcula en cada lectura. UI en gris con "vencida" + aviso a 30 días. Tests en `tests/test_certifications_expiry.py` (5) |
| 21-P-03 | Filtro de colaboradores por skill | 🟡 Media | "Muéstrame quién sabe FortiGate" no se puede responder desde la UI |
| 21-P-04 | Certificaciones del equipo en el portal cliente | 🟡 Media | Argumento comercial desaprovechado: el cliente no ve que su auditor está certificado |
| 21-P-05 | Adjuntar el certificado (PDF) | 🟡 Media | Hay `url` de validación pero no archivo. Depende del storage de `19-P-01` |
| 21-P-06 | Niveles normalizados | 🟢 Baja | `level` es texto libre → "avanzado", "Avanzado", "senior" conviven sin criterio |
| 21-P-07 | Matriz de capacidades del equipo | 🟢 Baja | Vista skill × colaborador para detectar puntos únicos de falla |

---

## ✅ Riesgo cerrado — 2026-08-06

**`21-P-02` tenía consecuencia externa.** Si el directorio mostraba "CCNA — verificado" con una certificación caducada en 2024, se presentaba información falsa a un cliente.

**Cerrado** con campos derivados en `UserCertificationRead`:

| Campo | Qué resuelve |
|---|---|
| `is_expired` | `expires_at < ahora`. Sin fecha = no caduca |
| `days_until_expiry` | Negativo si ya venció. Habilita el aviso previo de `18-P-03` |
| `effective_status` | Lo que debe pintar la UI. `approved` + vencida → `expired` |

**Por qué derivado y no un job que mute `status`:** no requiere migración ni tarea programada, no puede desincronizarse porque se recalcula en cada respuesta, y preserva el hecho histórico de que sí fue aprobada.

**Un caso que no era obvio:** una certificación `rejected` y vencida sigue siendo `rejected`. La expiración no puede pisar un estado que ya era negativo — está cubierto por test.

**En la UI:** el directorio de colaboradores cuenta solo las vigentes, ordena las válidas primero y pinta las vencidas en gris tachado. El perfil del propio colaborador avisa a 30 días del vencimiento.
