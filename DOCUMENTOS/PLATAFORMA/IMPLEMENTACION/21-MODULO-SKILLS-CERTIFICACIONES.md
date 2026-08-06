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
| 21-P-01 | **Re-verificación al editar** | 🔴 Alta | Editar una skill aprobada no la devuelve a `pending`. Mismo hueco que `17-P-04` |
| 21-P-02 | **Expiración automática** | 🔴 Alta | `expires_at` se guarda y nadie lo evalúa: una cert vencida sigue mostrándose como aprobada |
| 21-P-03 | Filtro de colaboradores por skill | 🟡 Media | "Muéstrame quién sabe FortiGate" no se puede responder desde la UI |
| 21-P-04 | Certificaciones del equipo en el portal cliente | 🟡 Media | Argumento comercial desaprovechado: el cliente no ve que su auditor está certificado |
| 21-P-05 | Adjuntar el certificado (PDF) | 🟡 Media | Hay `url` de validación pero no archivo. Depende del storage de `19-P-01` |
| 21-P-06 | Niveles normalizados | 🟢 Baja | `level` es texto libre → "avanzado", "Avanzado", "senior" conviven sin criterio |
| 21-P-07 | Matriz de capacidades del equipo | 🟢 Baja | Vista skill × colaborador para detectar puntos únicos de falla |

---

## Riesgo abierto

**`21-P-02` tiene consecuencia externa.** Si el directorio muestra "CCNA — verificado" con una certificación caducada en 2024, se está presentando información falsa a un cliente. Es el pendiente más urgente del módulo.

**Fix propuesto:** en el `GET` de certificaciones, derivar un campo calculado `is_expired = expires_at < today` y que la UI muestre el badge "Vencida" en gris, sin tocar el `status` almacenado. Complementar con la alerta `18-P-03` para avisar 30 días antes del vencimiento.
