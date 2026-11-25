# Roles y Accesos — Ninja Tech

## Los 4 roles del sistema

### super_admin
- **Quién lo tiene:** Fundador, CTO, dueño del sistema
- **Acceso:** Total — puede hacer todo, incluyendo eliminar usuarios, cambiar roles, ver toda la auditoría
- **Restricciones:** Ninguna
- **Ejemplo:** `admin@ninjasec.local`

### admin
- **Quién lo tiene:** Gerentes de operaciones, líderes de equipo
- **Acceso:** Todo el backoffice excepto cambiar roles de otros admins o del super_admin
- **Restricciones:** No puede eliminar usuarios (solo el super_admin puede)
- **Ejemplo:** `admin2@ninjasec.local`, `lucia.vargas@ninjasec.local`

### collaborator
- **Quién lo tiene:** Técnicos, analistas SOC, ingenieros de seguridad, pen testers
- **Acceso:** Ver y operar tickets, dispositivos, revisiones y proyectos asignados
- **Restricciones:** No accede a módulos comerciales (leads, servicios admin), ni a gestión de usuarios
- **Ejemplo:** `carlos.mendez@ninjasec.local`, `sofia.rios@ninjasec.local`

### client
- **Quién lo tiene:** Personal TI de las empresas clientes
- **Acceso:** Solo el Portal Cliente (inventario, documentos, tickets propios, servicios)
- **Restricciones:** No accede al backoffice ni ve información de otros clientes
- **Ejemplo:** `client@ninjasec.local` (Blue Shield Corp)

---

## Matriz de acceso por módulo

### Módulos 01-14

| Módulo | super_admin | admin | collaborator | client |
|--------|:-----------:|:-----:|:------------:|:------:|
| Dashboard principal | ✅ | ✅ | ❌ | ❌ |
| Clientes (CRUD) | ✅ | ✅ | 👁️ ver | ❌ |
| Integraciones | ✅ | ✅ | 👁️ ver | ❌ |
| Dispositivos | ✅ | ✅ | ✅ | ❌ |
| Revisiones de seguridad | ✅ | ✅ | ✅ asignadas | ❌ |
| Tickets de soporte | ✅ | ✅ | ✅ | ✅ propios |
| Leads / CRM | ✅ | ✅ | ❌ | ❌ |
| Reportes | ✅ | ✅ | ❌ | ❌ |
| Colaboradores | ✅ | ✅ | 👁️ ver | ❌ |
| Servicios (catálogo) | ✅ | ✅ | ❌ | ✅ solicitar |
| Proyectos | ✅ | ✅ | ✅ asignados | ❌ |
| Usuarios | ✅ total | ✅ parcial | ❌ | ❌ |
| **Portal — Inventario** | ❌ | ❌ | ❌ | ✅ |
| **Portal — Documentos** | ❌ | ❌ | ❌ | ✅ |
| **Portal — Perfil** | ❌ | ❌ | ❌ | ✅ |

### Módulos 15-22 (verificado contra el código el 2026-08-06)

| Módulo | super_admin | admin | collaborator | client |
|--------|:-----------:|:-----:|:------------:|:------:|
| 15 Postulaciones — bandeja | ✅ | ✅ | ✅ asignadas | ❌ |
| 15 Postulaciones — decidir | ✅ | ✅ | ❌ | ❌ |
| 15 Postular (`POST /job-applications/`) | 🌐 **público, sin autenticación** ||||
| 16 Auditoría | ✅ | ✅ | ❌ | ❌ |
| 17 Aprobaciones — bandeja | ✅ | ✅ | ❌ | ❌ |
| 17 Aprobaciones — **verificar** | ✅ | ❌ | ❌ | ❌ |
| 18 Alertas — consultar | ✅ | ✅ | ✅ | ❌ |
| 18 Alertas — `POST /refresh` | ✅ | ❌ | ❌ | ❌ |
| 19 Documentos — leer | ✅ | ✅ | ✅ de sus proyectos | ✅ propios |
| 19 Documentos — verificar / tipos | ✅ | ❌ | ❌ | ❌ |
| 20 Configuración — catálogos | 👁️ | 👁️ | 👁️ | 👁️ ⚠️ |
| 21 Skills / certs — autodeclarar | ✅ | ✅ | ✅ | ✅ |
| 21 Skills / certs — **verificar** | ✅ | ❌ | ❌ | ❌ |
| 22 Tareas del portal | ❌ | ❌ | ❌ | ✅ |

> ✅ = acceso completo | 👁️ = solo lectura | ✅ asignadas = solo registros que le fueron asignados | ❌ = sin acceso | 🌐 = sin autenticación

**Tres asimetrías que no son obvias:**

1. **Verificar es exclusivo de `super_admin`.** Skills, certificaciones y documentos: un `admin` puede editar el registro pero no aprobarlo. Es intencional — la verificación es la firma de confianza que se muestra al cliente.
2. **`POST /job-applications/` es el único endpoint sin autenticación de toda la API.** Ver `15-P-05`.
3. **Los catálogos los lee cualquier rol autenticado, incluido `client`.** `catalogs/routers/router.py` solo exige `get_current_user`. Ver el riesgo de aislamiento más abajo.

---

## Aislamiento multi-tenant (`organization_id`)

Ninja Tech es multi-tenant desde el modelo de datos: **24 de los 41 modelos llevan `organization_id`**. No hay un módulo que documente esto, así que vive aquí.

### Cómo funciona

El `organization_id` viaja en `CurrentUser` y cada servicio filtra por él. El JWT **no** lo transporta: se resuelve desde el usuario en cada request.

```
JWT { sub: email, role, exp }
        ↓
get_current_user() → carga el User de la BD
        ↓
CurrentUser { id, email, role, organization_id }
        ↓
cada query filtra .where(X.organization_id == current_user.organization_id)
```

**El rol responde "qué puedo hacer". El `organization_id` responde "sobre qué datos".** Son dos controles independientes y ambos deben aplicarse: un `super_admin` sigue estando confinado a su organización (`GET /organizations/` devuelve solo la suya).

### Catálogos globales por diseño

Estos modelos **no** llevan `organization_id` y se comparten entre todas las organizaciones:

| Modelo | Por qué es global |
|---|---|
| `Skill` | "FortiGate" significa lo mismo en cualquier organización |
| `DocType` | Tipos de documento normalizados |
| `Role` | Los 4 roles son del sistema |

### ⚠️ Tres huecos verificados en el código

| Hueco | Evidencia | Consecuencia |
|---|---|---|
| **`GET /products` no filtra por organización** | `catalogs/routers/router.py:37` — sin `.where(Product.organization_id == ...)`, pese a que `Product.organization_id` es `nullable=False` | Cualquier usuario autenticado, **incluido un `client`**, ve el catálogo de productos de todas las organizaciones |
| **`Area.name` y `ProjectType.name` son `unique=True` globales** | `db/models/area.py:16`, `project_type.py:16` — llevan `organization_id` pero la unicidad no lo incluye | Dos organizaciones no pueden tener ambas un área "Redes". El multi-tenant se rompe al segundo tenant |
| **`Area.organization_id` / `ProjectType.organization_id` son `nullable=True`** | mismos archivos | Un registro sin organización es visible para todos sin que nada lo declare |

Registrados como `20-P-08`, `20-P-09` y `20-P-10` en `IMPLEMENTACION/20-MODULO-CONFIGURACION.md`.

> **Regla:** todo modelo nuevo con datos de negocio lleva `organization_id`, y toda restricción `unique` sobre un modelo multi-tenant debe ser compuesta con `organization_id`.

---

## Reglas importantes

1. **Un usuario solo puede tener un rol.** No hay roles combinados.
2. **Los clientes NO ven el backoffice** (`/dashboard`). Son redirigidos al portal (`/portal`).
3. **El super_admin es el único que puede**: eliminar usuarios, cambiar el rol de cualquier cuenta, ver la auditoría completa.
4. **Los collaborators** ven el backoffice pero con menú reducido (sin Leads, sin Reportes, sin Usuarios, sin Configuración).
5. **Los tokens JWT expiran en 24 horas.** El re-login es obligatorio pasado ese tiempo.
6. **El rol no sustituye al filtro por organización.** Ambos controles se aplican siempre; ver la sección de aislamiento multi-tenant.
7. **Verificar/aprobar es exclusivo de `super_admin`** en skills, certificaciones y documentos. Un `admin` edita, no aprueba.

---

## Roles previstos para los módulos 23-30

Todavía no implementados. Se documentan aquí para que la matriz nazca decidida:

| Módulo | super_admin | admin | collaborator | client |
|--------|:-----------:|:-----:|:------------:|:------:|
| 23 Topología — ver | ✅ | ✅ | ✅ | 👁️ propia |
| 23 Topología — editar conexiones | ✅ | ✅ | ✅ | ❌ |
| 24 Cumplimiento SGSI | ✅ | ✅ | ✅ evidencia | 👁️ su SoA |
| 25 Riesgos — registrar / valorar | ✅ | ✅ | ✅ | ❌ |
| 25 Riesgos — **aceptar** | ✅ | ✅ | ❌ | ❌ |
| 26 Auditorías — ejecutar | ✅ | ✅ | ✅ asignadas | ❌ |
| 26 Auditorías — informe | ✅ | ✅ auditor líder | ❌ | 👁️ si `closed` |
| 27 Arquitectura empresarial | ✅ | ✅ | 👁️ | ❌ |
| 28 NetDoctor — modo guiado | ✅ | ✅ | ✅ | ❌ |
| 28 NetDoctor — **SSH / remediación** | ✅ | ❌ | ❌ | ❌ |
| 29 Catálogo de equipos | ✅ | ✅ | 👁️ | ❌ |
| 30 SOAR — ver eventos | ✅ | ✅ | ✅ | 👁️ los suyos |
| 30 SOAR — **bloqueo automático** | ✅ | ❌ | ❌ | ❌ |

**El patrón se mantiene:** toda acción que modifica infraestructura del cliente o emite un juicio de confianza es exclusiva de `super_admin`.

---

## Flujo de autenticación

```
Usuario ingresa email + contraseña
        ↓
Backend valida credenciales (bcrypt)
        ↓
Genera JWT con { sub: email, role: string, exp: 24h }
        ↓
Frontend lee el rol del token
        ↓
  ┌─────────────────────────────────┐
  │ role = client → redirect /portal│
  │ role = admin/super_admin        │
  │           → redirect /dashboard │
  │ role = collaborator             │
  │           → redirect /dashboard │
  └─────────────────────────────────┘
```
