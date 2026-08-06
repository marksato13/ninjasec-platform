# Módulo: Habilidades y Certificaciones

**Ruta:** `/portal/profile` (declaración) · `/dashboard/approvals` (verificación) · `/dashboard/collaborators` (consumo)
**Acceso:** todos los roles internos declaran lo suyo · `super_admin` verifica
**Backend:** `modules/skills` (`/skills`) y `modules/certifications` (`/user-certifications`)

---

## ¿Qué es?

Inventario de capacidades del equipo. Registra qué sabe hacer cada colaborador y qué certificaciones acredita, **con verificación explícita** para que el dato sea confiable frente a un cliente.

Responde a dos preguntas operativas reales:
- ¿A quién asigno esta revisión de FortiGate?
- ¿Puedo demostrarle al cliente que quien audita su red está certificado?

---

## Entidades

### `skills` — catálogo global

| Campo | Descripción |
|---|---|
| `name` | Nombre único de la habilidad |
| `category` | Agrupador (redes, seguridad, desarrollo, cloud...) |
| `is_active` | Retiro lógico del catálogo |

### `user_skills` — la declaración

| Campo | Descripción |
|---|---|
| `user_id` / `skill_id` | Quién declara qué |
| `level` | Nivel autodeclarado (texto libre) |
| `status` | `pending` · `approved` · `rejected` |
| `verified_by` / `verified_at` | Sello de verificación |

### `user_certifications` — la acreditación

| Campo | Descripción |
|---|---|
| `name` | Nombre de la certificación (CCNA, CEH, ISO 27001 LA...) |
| `issuer` | Entidad emisora (Cisco, EC-Council, PECB...) |
| `credential_id` | Código verificable de la credencial |
| `url` | Enlace de validación pública |
| `issued_at` / `expires_at` | Vigencia |
| `status` | `pending` · `approved` · `rejected` |
| `verified_by` / `verified_at` | Sello de verificación |

---

## Ciclo de vida

```
Colaborador declara  →  status = pending  →  super_admin revisa
                                                    │
                                    ┌───────────────┴───────────────┐
                                approved                        rejected
                                    │                               │
                    visible en directorio             no visible, queda el registro
                    y en cara al cliente
```

---

## Funcionalidades

- Catálogo de skills reutilizable con categorías
- Autodeclaración desde el perfil del colaborador
- Certificaciones con `credential_id` y URL de validación — el cliente puede comprobarlas por su cuenta
- Control de vigencia mediante `issued_at` / `expires_at`
- Verificación centralizada en la bandeja de aprobaciones

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver catálogo de skills | ✅ | ✅ | ✅ | ❌ |
| Crear skill en el catálogo | ✅ | ✅ | ❌ | ❌ |
| Declarar skill propia | ✅ | ✅ | ✅ | ❌ |
| Editar skill propia | ✅ | ✅ | ✅ | ❌ |
| **Verificar skill** | ✅ | ❌ | ❌ | ❌ |
| Declarar certificación propia | ✅ | ✅ | ✅ | ❌ |
| **Verificar certificación** | ✅ | ❌ | ❌ | ❌ |
| Ver skills aprobadas del equipo | ✅ | ✅ | ✅ | ⏳ |

⏳ = el portal cliente aún no expone las certificaciones del equipo asignado. Es una oportunidad comercial clara.

---

## Reglas de negocio

1. **Declarar no es acreditar.** Todo nace en `pending` y solo `super_admin` lo mueve a `approved`.
2. Nadie verifica lo propio, ni siquiera el `super_admin` — la acción queda registrada con autor.
3. Una skill o certificación `pending` o `rejected` **no aparece** en el directorio de colaboradores.
4. Editar una skill ya aprobada debería devolverla a `pending` (regla pendiente de implementar).
5. Una certificación con `expires_at` pasada debería marcarse vencida automáticamente (pendiente).
6. `credential_id` y `url` son el respaldo verificable — sin ellos la certificación vale como declaración, no como prueba.

---

## Conexión con otros módulos

- **10 — Colaboradores:** muestra las capacidades aprobadas
- **17 — Aprobaciones:** bandeja donde ocurre la verificación
- **06 — Revisiones:** insumo para asignar el revisor idóneo
- **12 — Proyectos:** insumo para armar el equipo
