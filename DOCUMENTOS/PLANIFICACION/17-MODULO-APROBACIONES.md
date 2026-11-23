# Módulo: Aprobaciones

**Ruta:** `/dashboard/approvals`
**Acceso:** `super_admin` (verificar) · `admin` (consultar)
**Backend:** transversal — `modules/skills`, `modules/certifications`, `modules/docs`

---

## ¿Qué es?

Bandeja única de verificación. Centraliza todo lo que un colaborador **declara** sobre sí mismo o sobre un proyecto y que necesita el visto bueno de la organización antes de considerarse cierto.

Resuelve un problema concreto de confianza: si cualquiera puede escribir "tengo CCNA" en su perfil, el directorio de colaboradores deja de servir para asignar trabajo o para mostrárselo a un cliente.

---

## Qué se aprueba aquí

| Objeto | Tabla | Quién lo declara | Quién lo verifica |
|---|---|---|---|
| Habilidades | `user_skills` | El propio colaborador | `super_admin` |
| Certificaciones | `user_certifications` | El propio colaborador | `super_admin` |
| Documentos de proyecto | `project_docs` | Colaborador o admin | `super_admin` |
| Tipos de documento | `doc_types` | — (catálogo) | `super_admin` |

---

## Estados de verificación

Skills y certificaciones comparten el mismo ciclo:

| Estado | Descripción |
|---|---|
| `pending` | Declarado, esperando verificación — **no se muestra como válido** |
| `approved` | Verificado; queda sellado con `verified_by` + `verified_at` |
| `rejected` | Rechazado por el verificador |

Documentos de proyecto (`project_docs`) usan su propio ciclo: `draft` → `active` → `archived`, más `verified_by` / `verified_at` y un flag `enabled` para ocultarlos sin borrarlos.

---

## Funcionalidades

### Vista consolidada
Una sola pantalla carga en paralelo skills, certificaciones, tipos de documento, documentos y proyectos, evitando que el super_admin recorra cuatro módulos distintos.

### Sello de verificación
Al aprobar, se graban `verified_by` (quién) y `verified_at` (cuándo). Ese par es la evidencia auditable y viaja al audit log.

### Filtro por proyecto
Los documentos se filtran por proyecto para revisar por lotes.

### Alta de tipos de documento
Desde la misma bandeja se pueden crear tipos de documento con su `scope` (`public` / `private` / `both`).

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver bandeja de aprobaciones | ✅ | ✅ | ❌ | ❌ |
| Verificar habilidad | ✅ | ❌ | ❌ | ❌ |
| Verificar certificación | ✅ | ❌ | ❌ | ❌ |
| Verificar documento | ✅ | ❌ | ❌ | ❌ |
| Activar / desactivar documento | ✅ | ❌ | ❌ | ❌ |
| Crear tipo de documento | ✅ | ❌ | ❌ | ❌ |
| Declarar habilidad o certificación propia | ✅ | ✅ | ✅ | ❌ |

---

## Reglas de negocio

1. **Nadie se auto-verifica.** La verificación es exclusiva de `super_admin`, aunque el declarante también lo sea, la acción queda registrada con autor.
2. Una skill o certificación en `pending` **no cuenta** para el directorio de colaboradores ni para lo que ve el cliente.
3. `verified_by` y `verified_at` son inseparables — se graban juntos o no se graban.
4. Los documentos se **desactivan** (`enabled = false`), no se borran: el histórico del proyecto se conserva.
5. Toda verificación deja huella en el audit log ([[16-MODULO-AUDITORIA]]).
6. Una certificación con `expires_at` vencida debería dejar de contar como válida — regla pendiente de automatizar.

---

## Conexión con otros módulos

- **10 — Colaboradores:** consume las skills y certificaciones ya aprobadas
- **12 — Proyectos:** los documentos aprobados cuelgan de un proyecto
- **19 — Documentos y Recursos:** publica al cliente solo lo verificado y activo
- **16 — Auditoría:** recibe la evidencia de cada verificación
