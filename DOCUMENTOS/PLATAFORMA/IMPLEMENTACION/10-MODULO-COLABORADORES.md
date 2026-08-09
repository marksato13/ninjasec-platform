# Implementación — Módulo Colaboradores

> Basado en: `DOCUMENTOS/PLATAFORMA/10-MODULO-COLABORADORES.md`  
> Fecha: Mayo 2026

---

## Checklist de implementación

### Vista Cards

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Avatar generado con iniciales y color por nombre | ✅ | `collaborators/page.tsx` → `<CollabAvatar />` |
| 2 | Nombre completo y email | ✅ | `collaborators/page.tsx` |
| 3 | Cargo (position_title) | ✅ | `collaborators/page.tsx` |
| 4 | Dot de disponibilidad en el avatar | ✅ | `collaborators/page.tsx` → dot colorido en la esquina |
| 5 | Borde izquierdo con color de disponibilidad | ✅ | `collaborators/page.tsx` → `borderLeft: 3px solid ${color}` |
| 6 | Skills expandibles con "+N más" | ✅ | `collaborators/page.tsx` → `expandedSkills` state |
| 7 | Badge de rol | ✅ | `collaborators/page.tsx` → `getRoleBadgeClass()` |

### Vista Tabla

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 8 | Columnas: Avatar, Nombre, Cargo, Seniority, Skills, Disponibilidad, Acciones | ✅ | `collaborators/page.tsx` |
| 9 | Skills resumidas (máx 2 + "+N") | ✅ | `collaborators/page.tsx` |

### Estados de disponibilidad (corregidos)

| # | Estado | Color | Implementado |
|---|--------|-------|-------------|
| 10 | `available` | 🟢 Verde | ✅ `var(--success)` |
| 11 | `busy` | 🔴 Rojo | ✅ `var(--danger)` (corregido — antes era warning/amarillo) |
| 12 | `partial` | 🟡 Amarillo | ✅ `var(--warning)` (agregado) |
| 13 | `off` | ⚫ Gris | ✅ `var(--muted)` (agregado) |

### Acciones por rol

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 14 | Ver directorio: todos (admin, collaborator) | ✅ | `sidebar.tsx` → grupo commercial, staffAllowed |
| 15 | Crear colaborador: solo admin/super_admin | ✅ | `collaborators/page.tsx` → `{isAdmin && <button>}` |
| 16 | Editar cualquier colaborador: admin/super_admin | ✅ | `collaborators/page.tsx` → `isAdmin` |
| 17 | Editar **solo el propio** perfil: collaborator | ✅ | `collaborators/page.tsx` → `isCollaborator && profile.user_id === currentUser?.id` |
| 18 | Eliminar: solo super_admin | ✅ | `collaborators/page.tsx` → `isSuperAdmin` |

### Filtros

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 19 | Filtro por disponibilidad (4 estados) | ✅ | `collaborators/page.tsx` → select con available/busy/partial/off |
| 20 | Filtro por seniority (dinámico) | ✅ | `collaborators/page.tsx` → `seniorityOptions` desde los perfiles |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/db/models/collaborator_profile.py` | Columnas nuevas `area: String(60) \| None` y `photo_url: String(500) \| None` |
| `backend/app/modules/collaborators/schemas/collaborator.py` | `CollaboratorRead/Update/Create` con `area`, `photo_url`, `portfolio_url` |
| `frontend/src/lib/api/collaborators.ts` | Tipo `CollaboratorProfile` + payloads de create/update con `area`, `photo_url`, `portfolio_url` |
| `frontend/src/app/(admin)/dashboard/collaborators/page.tsx` | `AVAIL_COLOR`/`AVAIL_LABEL` con 4 estados; `QK.collaborators()` en queryKey y setQueryData; `isCollaborator` constante; botón Editar visible para collaborator propio. **Nuevo:** carga `getUserCertifications()` y construye map `certsByUser[user_id]` — muestra count + 3 tags de certs en cada card. **Nuevo:** filtro por área (dropdown con valores únicos dinámicos). **Nuevo:** select de área en modal de edición (Operaciones/Comercial/Administración/Tecnología/Seguridad). **Nuevo:** input `photo_url`; si está set, `CollabAvatar` renderiza `<img>` en lugar de iniciales (con fallback `onError`) |

---

## Archivos de referencia (sin cambios)

| Archivo | Rol |
|---------|-----|
| `frontend/src/lib/api/collaborators.ts` | `getCollaborators()`, `updateCollaborator()`, `deleteCollaborator()` |
| `backend/app/modules/collaborators/routers/router.py` | `GET /collaborators`, `PATCH /collaborators/{id}`, `DELETE /collaborators/{id}` |

---

## Pendientes

| # | Pendiente | Razón |
|---|-----------|-------|
| ~~10-P-01~~ | ~~Campo "Área" (Operaciones, Administración, Comercial)~~ | ✅ **Implementado**: columna DB `area VARCHAR(60)` + schemas + select en form + filtro dinámico en el listado. Áreas seedeadas para los primeros 4 colaboradores |
| ~~10-P-02~~ | ~~Certificaciones en el perfil~~ | ✅ **Implementado**: `getUserCertifications()` cargado en background y agrupado por `user_id`. Cada card muestra contador en `card-meta` (con icono `Award`) + hasta 3 tags verdes con nombre de cert (+ "más" si hay más) |
| ~~10-P-03~~ | ~~Foto real del colaborador~~ | ✅ **Implementado** (parcial): columna `photo_url VARCHAR(500)` + input URL en el form. `CollabAvatar` renderiza `<img>` si está set, con fallback a iniciales en caso de error de carga. Para upload de archivo (no solo URL), se necesitaría infraestructura de storage adicional (S3, etc.) |
| ~~10-P-04~~ | ~~Collaborator podía editar cualquier perfil~~ | ✅ **Implementado** en sesión anterior |
| ~~10-P-05~~ | ~~Upload de imagen (vs URL externa)~~ | ✅ **Resuelto 2026-08-08**: el endpoint de foto usa el storage local común, valida JPG/PNG/WEBP hasta 5 MB y sirve la imagen con autorización de tenant. `photo_url` externo sigue aceptándose sin migración |
| ~~10-P-06~~ | ~~Migración Alembic para `area` y `photo_url`~~ | ✅ **Resuelto** (verificado 2026-08-06): `20260522_01_pending_schema_updates.py:33-36` agrega ambas columnas a `collaborator_profiles` |
| ~~10-P-07~~ | ~~Sin estado de error visible si falla la carga de colaboradores~~ | ✅ **Resuelto 2026-08-09**: `collaborators/page.tsx` ahora destructura `error` del `useQuery` principal y renderiza `{error && <p className="form-error">Error al cargar colaboradores</p>}`. |
