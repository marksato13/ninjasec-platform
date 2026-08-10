# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

---

## Project Overview

**NinjaSec** es una plataforma full-stack de infraestructura + ciberseguridad para PYMEs, consultoras y MSPs. Genera reportes automáticos desde pfSense, FortiGate, Suricata IDS y similares, y sirve como portafolio de servicios profesionales.

**Estado:** MVP avanzado (backend v0.2.0). Se ejecutó un seed masivo con data peruana realista (17 clientes, 73 dispositivos, 28 revisiones con 62 hallazgos, 15 proyectos, etc.). Todos los módulos del checklist `IMPLEMENTACION/01–14.md` están cerrados.

**Origen:** consultoría inicial pensada para que estudiantes UPeU de Desarrollo, Infraestructura y Ciberseguridad practiquen y entreguen valor real a SMEs peruanas.

---

## 🚀 Cómo correr el proyecto

Todo el desarrollo local pasa por Docker Compose en `infra/`:

```powershell
# Desde la raíz del repo:
cd infra
docker compose up -d --build           # levantar todo
docker compose up -d --build backend   # rebuild sólo backend
docker compose up -d --build frontend  # rebuild sólo frontend
docker compose down                    # detener (mantiene volumen Postgres)
docker compose down -v                 # destructivo — borra DB
```

**Puertos:**
- Frontend (Next.js): http://localhost:3018
- Backend (FastAPI Swagger): http://localhost:8024/docs
- PostgreSQL: `localhost:5433` (externo) / `5432` (interno Docker)

API base: `http://localhost:8024/api/v1` (en producción Next.js hace proxy desde `/api/v1/*`)

### Credenciales seed
| Rol | Email | Contraseña |
|---|---|---|
| super_admin | `admin@ninjasec.local` | `change-me` |
| admin | `ops@ninjasec.local` | `admin123` |
| collaborator (seed-original) | `collab@ninjasec.local` | `temp123` |
| client | `client@ninjasec.local` | `NinjaSec2024!` |
| collaborators nuevos (12) | `andrea.castillo@ninjasec.local`, `bryan.huaman@ninjasec.local`, `joel.cardenas@ninjasec.local`, etc. | `colab123` |

---

## 🤖 MCP Servers — usar proactivamente

- **Context7** → docs actualizadas de FastAPI, Next.js 15, React 19, SQLAlchemy 2.0, Pydantic v2, TanStack Query, Alembic, Tailwind 3. Trigger: añadir `use context7` en prompts de librerías.
- **GitHub** → PRs, issues, commits, releases.
- **Playwright** → testing manual de flows. Decir explícitamente "playwright mcp". Frontend en `http://localhost:3018`, Swagger en `http://localhost:8024/docs`.
- **PostgreSQL (`postgres-ninjasec`)** → query directo a la DB para debug. **NUNCA** DELETE/DROP sin confirmación explícita del usuario.
- **Sequential Thinking** → planificación de módulos nuevos, migraciones Alembic.
- **Memory** → ya hay archivos en `~/.claude/projects/C--Users-markp/memory/`.
- **Firecrawl + Brave** → buscar CVE, docs de pfSense/FortiGate.
- **Filesystem** → acceso a archivos del proyecto.
- **DrawIO** → para diagramas (importante para el feature de network-map pendiente).

---

## 🏗️ Arquitectura

### Backend — `backend/app/` (Modular monolith en Python 3.12 / FastAPI)

```
backend/app/
├── main.py              # init FastAPI, CORS, lifespan (auto-create tables + seed)
├── api/router.py        # router central — registra todos los módulos
├── core/                # config (pydantic-settings), JWT, security, exceptions
├── db/
│   ├── models/          # 40+ modelos SQLAlchemy 2.0 organizados por dominio
│   ├── session.py       # engine + SessionLocal
│   ├── seed.py          # seed dev base
│   └── migrations/      # Alembic
├── common/
│   ├── deps/            # auth (CurrentUser, require_roles, get_current_user) + database
│   └── schemas/         # ORMModel base (Pydantic v2 con from_attributes=True)
└── modules/             # 18 módulos feature
    └── [module]/
        ├── routers/    # APIRouter + handlers
        ├── schemas/    # Pydantic request/response
        └── services/   # lógica de negocio
```

**Módulos activos:** `auth`, `organizations`, `users`, `clients`, `client_sites`, `client_contacts`, `collaborators`, `devices`, `catalogs`, `skills`, `certifications`, `projects`, `services`, `leads`, `recruitment` (job_applications), `integrations`, `collection`, `reports`, `docs`, `audit`, `support_tickets`, `security_reviews`, `dashboard`, `alerts`.

Para agregar un módulo nuevo: crear carpeta en `modules/`, implementar routers/schemas/services, registrar el router en `api/router.py`.

### Frontend — `frontend/src/` (Next.js 15 App Router + React 19)

```
src/
├── app/
│   ├── (public)/    # marketing, login, contacto
│   ├── (admin)/dashboard/    # backoffice (super_admin, admin, collaborator)
│   └── (portal)/portal/      # portal cliente (rol CLIENT)
├── components/
│   ├── dashboard/   # shell, sidebar, portal-shell, dashboard-shell, dashboard-widgets
│   ├── forms/       # client-form, user-form, project-form, collaborator-form
│   ├── public/      # marketing (lead-form, hero, etc.)
│   └── ui/          # Modal genérico
├── features/        # agenda-demo, colabora, etc.
├── lib/
│   ├── api/         # cliente HTTP modular (un archivo por dominio)
│   ├── alerts.ts    # SweetAlert2 wrappers (confirmDelete, confirmDeleteStrict, etc.)
│   ├── auth.ts      # localStorage helpers + isTokenExpired
│   ├── query-keys.ts # QK.* — clave estable por endpoint
│   └── validation.ts # Zod schemas
```

**State:** TanStack React Query para server state. **Forms:** React Hook Form + Zod.
**Iconos:** Lucide React. **CSS:** Tailwind 3 + globals.css con sistema de tokens (`--primary`, `--success`, etc.) y soporte tema claro/oscuro.

---

## 🔧 Decisiones técnicas importantes (no obvias)

### 1. **Next.js proxy con trailing slash explícito**
`frontend/next.config.ts` tiene **dos** rewrites — uno con slash al final, otro sin él — porque Next.js stripeaba el slash de la URL y FastAPI luego redirigía a `http://backend:8024/...` (DNS interno) generando un loop infinito en el browser. Setting `skipTrailingSlashRedirect: true` también activado.

```ts
async rewrites() {
  return [
    { source: "/api/v1/:path*/", destination: `${BACKEND_URL}/api/v1/:path*/` },
    { source: "/api/v1/:path*",  destination: `${BACKEND_URL}/api/v1/:path*` },
  ];
}
```

**NO QUITAR** estas configuraciones — son el fix de un bug que rompía todos los módulos.

### 2. **API base URL relativa**
`NEXT_PUBLIC_API_URL: /api/v1` (build arg en `infra/docker-compose.yml`). Todas las llamadas usan rutas relativas; Next.js proxy reenvía al backend. Esto permite que la app funcione tras cualquier dominio (Cloudflare tunnel, IP de red, etc.) sin rebuild.

### 3. **JWT expiry chequeado en el cliente**
`lib/auth.ts` tiene `isTokenExpired(token)` que decodifica el payload JWT. Se chequea en (1) `lib/api/client.ts` antes de cada fetch, (2) `dashboard-guard.tsx` al montar y (3) `portal-shell.tsx` al montar. Si expiró → `clearSession()` + redirect a `/login?expired=1`. El login muestra banner amarillo "Tu sesión expiró".

### 4. **`from __future__ import annotations` en servicios con método `list`**
Varios servicios (`clients`, `devices`, `leads`, `support_tickets`) tienen `def list(self) -> list[X]:`. En Python sin `from __future__ import annotations`, el método sombrea al builtin `list` y rompe los annotations subsiguientes con `TypeError: 'function' object is not subscriptable`. **NO QUITAR** los `from __future__` de esos archivos.

### 5. **Mock data fallback en dashboard**
`dashboard-widgets.tsx` exporta constantes `MOCK_*` (top vulns, top collaborators, etc.). Los widgets las usan **solo** cuando el endpoint real está vacío o no existe (sparklines de tendencia 7 días, por ejemplo). KPIs y conteos siempre vienen de queries reales.

### 6. **Dashboard tabbed con 5 vistas + auto-refresh**
`dashboard-shell.tsx` tiene tabs: General, Seguridad, Comercial, Operaciones, Infraestructura. Cada vista consume queries reales (clients, leads, projects, summary). El toggle "Auto ON/OFF" persiste en `localStorage.ninjasec_dashboard_autorefresh` y activa `refetchInterval: 60_000` en TanStack Query.

### 7. **Modales SweetAlert2 estilo "pill"**
`lib/alerts.ts` tiene `confirmDelete` (icono rojo X), `confirmApprove` (icono verde ✓), `confirmDeleteStrict` (requiere tipear el email para confirmar — usado en delete de usuarios) y `notifyError/Success/Warning/Info`. CSS en `globals.css` clase `.swal2-confirm-pill` y `.button-pill`. Los confirmation modals deben **siempre** verse con icono grande centrado y botón cápsula.

### 8. **Backend roles guards** (`require_roles`)
- `super_admin` ve y hace todo
- `admin` ve todo de su org pero **no puede editar a super_admin ni a otros admin** (sólo a sí mismo y a roles inferiores)
- `collaborator` ve sus revisiones asignadas (`reviewer_user_id == current_user.id`) y proyectos asignados (join con `ProjectMember`); sólo puede editar su propio perfil
- `client` ve sólo su empresa, sus tickets, sus revisiones cerradas, sus docs (`visibility=CLIENT`)

### 9. **Convención de fechas / nombres**
Documentación y comentarios en **español**. Identificadores de código en **inglés**. Fechas absolutas en memoria/notas (nunca "el martes" — siempre `2026-05-21`).

---

## 🔑 Configuración (`.env`)

| Variable | Notas |
|---|---|
| `JWT_SECRET_KEY` | Definida en docker-compose.yml para dev. Cambiar en producción |
| `NEXT_PUBLIC_API_URL` | `/api/v1` — inyectada al build del frontend |
| `DATABASE_URL` | `postgresql+psycopg://postgres:123456@postgres:5432/ninjasec` |
| `CORS_ORIGINS` | Lista explícita en docker-compose.yml — incluye IPs LAN |

---

## 🗂️ Convenciones de código

### Backend
- Modelos SQLAlchemy con `Mapped[...]` (estilo 2.0)
- Schemas Pydantic v2 heredan de `ORMModel` (en `common/schemas/base.py`) que tiene `from_attributes=True`
- Endpoints siempre validan rol con `require_roles(...)` y filtran por `current_user.organization_id`
- Audit log via `AuditService(db).record(...)` después de mutaciones

### Frontend
- Toda llamada HTTP usa `request<T>` o `requestPublic<T>` de `lib/api/client.ts`
- Query keys centralizadas en `lib/query-keys.ts` (`QK.users()`, `QK.projects()`, etc.)
- Forms con `useForm` + `zodResolver` + schema en `lib/validation.ts`
- Confirmaciones con `confirmDelete()` / `confirmApprove()` — nunca `window.confirm`
- Notificaciones con `notifySuccess()` / `notifyError()` — nunca `alert()`

---

## 🌎 Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT, psycopg3, openpyxl, ReportLab (PDFs)
- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS 3, Framer Motion, Lucide React, TanStack Query 5, React Hook Form, Zod, SweetAlert2
- **Infra:** Docker Compose (`infra/docker-compose.yml`), PostgreSQL 16

---

## ✅ Estado actual de los módulos

Los checklists `01-14` en `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/` están cerrados (todos los P-XX en ✅ excepto menores documentados como "mejoras futuras"). Los `15-22` se documentaron retroactivamente el 2026-08-05 y **sí tienen pendientes abiertos**. Resumen:

| # | Módulo | Última implementación destacada |
|---|---|---|
| 01 | Roles y accesos | JWT expiry frontend, cross-admin protection, confirmDeleteStrict |
| 02 | Dashboard | Tabbed con 5 vistas, auto-refresh, hallazgos clickeables |
| 03 | Clientes | city/country, badges devices+tickets, export XLSX, findings_count en reviews |
| 04 | Integraciones | Test/Collect para collaborator, banner "sin revisión >90 días" |
| 05 | Dispositivos | Portal sin IPs sensibles, sede en cards |
| 06 | Revisiones | **Export PDF individual** con resumen ejecutivo coloreado + checklist + findings |
| 07 | Tickets | Stats panel KPIs, "Desde hallazgo" en listado |
| 08 | Leads | Convertir a cliente, /contacto cableado, source en modal |
| 09 | Reportes | Card PDF revisión, `lastRun` en localStorage, filtro fecha en pipeline |
| 10 | Colaboradores | `area` + `photo_url`, certificaciones visibles |
| 11 | Servicios | `price_label`, toggles is_public/active |
| 12 | Proyectos | Vista Kanban, budget, equipo en cards, estado inline |
| 13 | Usuarios | Link "Ver auditoría" filtrado por entity_id |
| 14 | Portal Cliente | Cambio de contraseña, KPI servicios reales |

### Módulos construidos y documentados retroactivamente el 2026-08-05

Estaban en producción sin especificación. Auditados contra el código y documentados en `PLANIFICACION/` + `IMPLEMENTACION/`:

| # | Módulo | Ruta | Backend |
|---|---|---|---|
| 15 | Postulaciones (Reclutamiento) | `/dashboard/applications` | `modules/recruitment` |
| 16 | Auditoría (audit log) | `/dashboard/audit` | `modules/audit` |
| 17 | Aprobaciones | `/dashboard/approvals` | transversal (skills/certs/docs) |
| 18 | Alertas y notificaciones | widget en `/dashboard` | `modules/alerts` |
| 19 | Documentos y recursos | `/portal/documents`, `/portal/resources` | `modules/docs` |
| 20 | Configuración del sistema | `/dashboard/settings` | `modules/catalogs` |
| 21 | Habilidades y certificaciones | `/portal/profile`, `/dashboard/approvals` | `modules/skills`, `modules/certifications` |
| 22 | Tareas del portal | `/portal/tasks` | reutiliza `modules/projects` |

### Módulos planificados (23-30)

Especificados el 2026-08-05, sin codear salvo el 23. Ver `DOCUMENTOS/PLATAFORMA/ROADMAP.md` para la priorización:

| # | Módulo | Estado |
|---|---|---|
| 23 | Topología de red / Config Visualizer | 🟡 **Backend completo, falta UI** |
| 24 | Cumplimiento y SGSI (ISO 27001) | ⏳ |
| 25 | Gestión de riesgos (ISO 27005) | ⏳ |
| 26 | Auditorías de sistemas (COBIT / ISO 19011) | ⏳ |
| 27 | Arquitectura empresarial (TOGAF / ArchiMate) | ⏳ |
| 28 | NetDoctor — diagnóstico multi-vendor | ⏳ |
| 29 | Catálogo de equipos de red | ⏳ |
| 30 | Integraciones open source y mini-SOAR | ⏳ |

---

## 🔜 Próximos pasos pendientes — **PRIORITARIO**

📋 **Priorización y estimaciones: `DOCUMENTOS/PLATAFORMA/ROADMAP.md`**
📋 **Inventario completo de pendientes: `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/00-BACKLOG-GLOBAL.md`**

### ✅ Deuda crítica — cerrada el 2026-08-06

Los seis huecos de integridad y aislamiento. **63 tests pasan** (26 previos + 37 nuevos).

| Pendiente | Qué se implementó |
|---|---|
| `20-P-08` | Filtro por `organization_id` en los tres catálogos. `Area`/`ProjectType` admiten globales (`NULL`); `Product` no, porque su FK es `NOT NULL` |
| `21-P-02` / `17-P-05` | `is_expired`, `days_until_expiry`, `effective_status` derivados en `UserCertificationRead` |
| `21-P-01` / `17-P-04` | `app/common/verification.py` → `revoke_verification_if_changed()` |
| `15-P-05` | `app/common/rate_limit.py` → 5 postulaciones/hora por IP |
| `20-P-06` / `20-P-07` | `POST`/`PUT` de areas y project-types + endpoints `/usage` |
| `20-P-09` | `UniqueConstraint(organization_id, …)` + migración `20260806_01` |

**Reglas nuevas que hereda todo el código futuro:**

1. **Verificar es un juicio sobre un contenido concreto.** Si el contenido cambia, la verificación se revoca. Usa `revoke_verification_if_changed()` — no dupliques la lógica.
2. **La vigencia se deriva en lectura, no se mutan estados con un job.** No puede desincronizarse y no necesita tarea programada.
3. **Un registro rechazado no asciende a pendiente** por una edición ni por caducar.
4. **Datos de otra organización devuelven 404, no 403.** No se confirma que existan.
5. **Los catálogos globales (`organization_id = NULL`) se ven pero no se editan** desde una organización.

✅ **G-06 (resuelto 2026-08-10): `app/common/rate_limit.py` ahora soporta un backend Redis** compartido entre workers/replicas, seleccionado automáticamente cuando `REDIS_URL` está configurado y Redis responde al arrancar. Sin `REDIS_URL` (default en dev/CI) sigue usando el limitador en memoria de siempre — mismo comportamiento que antes, cero cambios para el caso sin Redis. Si Redis se cae después de arrancar, el limitador falla abierto (deja pasar) en vez de tumbar el endpoint que protege. Ver el docstring del módulo para el detalle completo.

### 🧱 Deuda de esquema — **bloqueante de FASE 2.8**

**Alembic no es la fuente de verdad del esquema.** Lo construye `Base.metadata.create_all()` en `app/main.py:19`; `migrations/versions/` solo tiene dos parches incrementales.

⚠️ **`create_all` crea las tablas que faltan pero NUNCA altera las existentes.** Toda columna nueva de un modelo se aplica en una base vacía y **se ignora sin error** en una base con datos — justo el escenario de una actualización en producción.

Además, `alembic upgrade head` no levanta una base desde cero: la primera migración hace `add_column` sobre tablas que aún no existen (`down_revision = None` sin `create_table`).

**Fix (~0.5 sesión):** migración base con `--autogenerate` sobre base vacía → encadenarla antes de `20260522_01` → retirar `create_all()` de `main.py`. **Antes** del deploy self-hosted, no después.

### 🔐 Multi-tenancy — regla permanente

24 de los 41 modelos llevan `organization_id`. El rol responde *qué puedo hacer*; el `organization_id` responde *sobre qué datos*. **Ambos controles se aplican siempre.**

- Todo modelo nuevo con datos de negocio lleva `organization_id`
- Toda restricción `unique` sobre un modelo multi-tenant se compone con `organization_id`
- Excepciones globales por diseño: `Skill`, `DocType`, `Role`

Detalle en `PLANIFICACION/01-ROLES-Y-ACCESOS.md` § Aislamiento multi-tenant.

### 🎯 Módulo 23 — Topología de red: **el backend YA ESTÁ HECHO**

Verificado el 2026-08-05. Existe y funciona:

- ✅ Tabla `device_connections` + migración `e1d861bf2ce6`
- ✅ Campos ISO en `Device`: `criticality`, `data_classification`, `responsible_user_id`
- ✅ `GET /devices/topology?client_id=` → nodes + edges + clusters (`services/topology_service.py`)
- ✅ CRUD `/device-connections` (`routers/connections.py`)
- ✅ Cliente API TypeScript completo (`frontend/src/lib/api/topology.ts`)
- ❌ **No existe ningún componente visual que lo consuma**

**Falta solo la UI.** Es la mejor relación valor/esfuerzo del roadmap: 1 sesión sobre trabajo ya pagado.

**Decisión pendiente:** librería de diagramación. Recomendado `@xyflow/react` (React Flow) — se reutiliza en el módulo 27 (ArchiMate), amortizando la dependencia en dos módulos. Mermaid queda descartado porque no soporta "clic en nodo → ficha del activo".

Detalle en `PLANIFICACION/23-MODULO-TOPOLOGIA.md` y su checklist pareado.

### 🎓 Entregables académicos con deadline duro

Los módulos 24, 25, 26 y 27 son a la vez funcionalidad de producto y los entregables de mayor peso del ciclo 10 (SGSI ISO 27001, riesgos ISO 27005, auditoría COBIT/ISO 19011, TOGAF/ArchiMate). Cubren el 70% de Seguridad, el 55% de Auditoría y el 70% de Arquitectura Empresarial.

Secuencia y estimaciones en la **Tanda 2** del ROADMAP.

### ⚠️ Módulos con puerta de seguridad

`28-P3` (NetDoctor por SSH) y `30-P6` (bloqueo automático Wazuh→pfSense) manipulan infraestructura de clientes. **No arrancan** sin credenciales cifradas, lista blanca de comandos, registro por comando, reversión inmediata y autorización escrita del cliente. Si no se garantizan, 28 se queda en P2 y 30 en P5 — ambos siguen aportando casi todo su valor.

### Mejoras menores documentadas

- **02-P-05:** WebSocket real-time para alertas (vs polling 60s actual)
- **05-P-05:** Filtro UI por `site_id` en portal cliente (backend ya lo acepta)
- **06-P-05:** Botón PDF desde listado de revisiones (ya está en el detalle)
- **08-P-02:** Drag & drop real en Kanban de leads (requiere `@dnd-kit`)
- **09-P-05:** Mover `lastRun` de localStorage a server-side
- **10-P-05:** Upload de imagen real para `photo_url` (S3/MinIO/filesystem)
- ~~**10-P-06 / 03-P-06 / 11-P-05 / 12-P-06:** Migraciones Alembic formales~~ → ✅ **resueltos**: `20260522_01_pending_schema_updates.py` ya cubre `city`, `country`, `area`, `photo_url`, `price_label` y `budget_label` (verificado 2026-08-06)

**Estado real del backlog (2026-08-06): 61 pendientes abiertos, 58 resueltos.** Los módulos 01-14 están *operativos*, no *cerrados*: quedan 7 cabos sueltos, todos de baja consecuencia.

---

## 🧪 Comandos útiles

```bash
# Type-check frontend
cd frontend && npx tsc --noEmit 2>&1 | grep -v "^\.next/" | grep -v "Cannot find module '"

# Ejecutar seed manual desde container
docker cp backend/seed_demo.py ninjasec-backend:/app/seed_demo.py
docker exec ninjasec-backend bash -c "python /app/seed_demo.py"

# Ver logs en vivo
docker logs ninjasec-backend -f
docker logs ninjasec-frontend -f

# Conectar a Postgres
docker exec -it ninjasec-postgres psql -U postgres -d ninjasec

# Smoke test de todas las rutas del dashboard
for p in /dashboard /dashboard/projects /dashboard/integrations /dashboard/devices /dashboard/security-reviews /dashboard/support-tickets /dashboard/clients /dashboard/collaborators /dashboard/leads /dashboard/services /dashboard/users /dashboard/applications /dashboard/audit /dashboard/reports; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3018$p"); echo "$p -> $code"
done
```

---

## 🚨 Seguridad y conducta

- NinjaSec es una **plataforma de seguridad** — extra cuidado con endpoints de auth, sesiones, validación de roles
- **JWT tokens** deben validarse en todas las rutas protegidas (backend hace esto via `Depends(require_roles)`)
- **Nunca** loguear passwords, tokens ni datos sensibles
- **CORS** debe ser lista explícita en producción
- **Confirmaciones destructivas** siempre con `confirmDeleteStrict` (escribir email del usuario) o `confirmDelete` con texto descriptivo
- **Audit log** después de toda operación crítica vía `AuditService(db).record(...)`

---

## 📚 Documentación viva del proyecto

Ubicación: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\EMPRESA NINJA-SEC\DOCUMENTOS\PLATAFORMA\` (fuera del repo `PY-MK`).

| Carpeta | Qué es | Cuándo se toca |
|---|---|---|
| `PLANIFICACION/NN-*.md` | El **qué**: especificación por módulo (Source of Truth de requisitos) | Aquí nace todo módulo nuevo |
| `IMPLEMENTACION/NN-*.md` | El **cómo** + diario: checklist `# / Requisito / Estado / Archivos` | Actualizar después de cada feature |
| `FLUJOS/*.md` | Procesos que cruzan 2+ módulos | Al definir un proceso transversal |
| `FIX/*.md` | Ajustes puntuales: problema / cambio / archivos / resultado | Post-mortem de un fix |
| `ROADMAP.md` | Priorización, estimaciones y decisiones pendientes | Al cerrar o reordenar una tanda |

**Regla de acoplamiento:** cada archivo de `PLANIFICACION/` tiene su par con el mismo número y nombre en `IMPLEMENTACION/`. Módulos 01-30 ocupados; **el siguiente número libre es el 31**.

⚠️ `tash/` es brainstorming histórico (36 documentos), **no** es especificación. No tomarlo como fuente de verdad.

---

## 🎓 Convenciones de lenguaje

- **Documentación, comentarios, mensajes de UI:** español
- **Identificadores de código (variables, funciones, archivos):** inglés
- **Commits:** breve en español ("agregar export PDF de revisión")
- **PRs:** título corto, body con summary + test plan
