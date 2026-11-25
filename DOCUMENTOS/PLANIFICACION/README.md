# Ninja Tech — Documentación de Plataforma

> Versión: v0.2.0 MVP | Última actualización: **2026-08-06** (verificación contra código)

## ¿Qué es Ninja Tech?

Ninja Tech es una plataforma SaaS de monitoreo de infraestructura y seguridad para empresas, MSPs y consultoras de TI. Genera reportes automáticos desde plataformas como pfSense, FortiGate y Wazuh, gestiona dispositivos, tickets de soporte, revisiones de seguridad y el ciclo comercial completo.

---

## Cómo se organiza la documentación

| Carpeta | Qué contiene | Cuándo se toca |
|---|---|---|
| **`PLANIFICACION/`** | El **qué**: especificación por módulo (ruta, roles, entidades, funcionalidades, reglas de negocio) | Aquí nace todo módulo nuevo |
| **`IMPLEMENTACION/`** | El **cómo** + diario: checklist `# / Requisito / Estado / Archivos` | Al empezar a codear y tras cada feature |
| **`FLUJOS/`** | Procesos que cruzan varios módulos | Cuando el proceso toca 2+ módulos |
| **`FIX/`** | Ajustes puntuales: problema / cambio / archivos / resultado | Post-mortem de un fix |
| **`ESTRATEGIA/`** | Decisiones transversales de operación, entrega y automatización | Cuando afecta varios módulos o el ciclo de entrega |
| **`HISTORICO/`** | Planes reemplazados y material de contexto | Nunca como fuente de requisitos u operación |

**Regla de acoplamiento:** cada archivo de `PLANIFICACION/` tiene su par con el mismo número y nombre en `IMPLEMENTACION/`.

### Los tres documentos transversales

| Archivo | Responde |
|---|---|
| `../ROADMAP.md` | **¿Qué hago ahora?** — tandas, esfuerzo, decisiones bloqueantes |
| `../IMPLEMENTACION/00-BACKLOG-GLOBAL.md` | **¿Qué falta en total?** — los 61 pendientes abiertos en una sola tabla |
| `01-ROLES-Y-ACCESOS.md` | **¿Quién puede qué?** — matriz de roles y aislamiento multi-tenant |

---

## Índice de módulos

**Leyenda:** ✅ operativo · ⚠️ parcial · 🟡 backend sin UI · ⏳ no iniciado

> *"Operativo" no es "cerrado"*: significa que funciona, y puede tener pendientes abiertos.

### Módulos 01-14 — base de la plataforma

| # | Módulo | Ruta | Estado | Abiertos |
|---|---|---|:---:|:---:|
| 01 | Roles y accesos | transversal | ✅ | 0 |
| 02 | Dashboard | `/dashboard` | ✅ | 2 |
| 03 | Clientes | `/dashboard/clients` | ✅ | 0 |
| 04 | Integraciones | `/dashboard/integrations` | ✅ | 0 |
| 05 | Dispositivos | `/dashboard/devices` | ✅ | 1 |
| 06 | Revisiones de seguridad | `/dashboard/security-reviews` | ✅ | 1 |
| 07 | Tickets de soporte | `/dashboard/support-tickets` | ✅ | 0 |
| 08 | Leads | `/dashboard/leads` | ✅ | 1 |
| 09 | Reportes | `/dashboard/reports` | ✅ | 1 |
| 10 | Colaboradores | `/dashboard/collaborators` | ✅ | 1 |
| 11 | Servicios | `/dashboard/services` | ✅ | 0 |
| 12 | Proyectos | `/dashboard/projects` | ✅ | 0 |
| 13 | Usuarios | `/dashboard/users` | ✅ | 0 |
| 14 | Portal cliente | `/portal` | ✅ | 0 |

### Módulos 15-22 — construidos antes de documentarse

Documentados retroactivamente el 2026-08-05 tras auditar el código.

| # | Módulo | Ruta | Estado | Abiertos |
|---|---|---|:---:|:---:|
| 15 | Postulaciones (Reclutamiento) | `/dashboard/applications` | ✅ | 6 |
| 16 | Auditoría (audit log) | `/dashboard/audit` | ✅ | 6 |
| 17 | Aprobaciones | `/dashboard/approvals` | ✅ | 6 |
| 18 | Alertas y notificaciones | widget transversal | ✅ | 7 |
| 19 | Documentos y recursos | `/portal/documents` · `/portal/resources` | ✅ | 6 |
| 20 | Configuración del sistema | `/dashboard/settings` | ⚠️ | **11** |
| 21 | Habilidades y certificaciones | `/portal/profile` · `/dashboard/approvals` | ✅ | 7 |
| 22 | Tareas del portal | `/portal/tasks` | ⚠️ | 5 |

### Módulos 23-33 — producto y plataforma

| # | Módulo | Estado | Naturaleza |
|---|---|---|---|
| 23 | **Topología de red / Config Visualizer** | 🟡 **Backend hecho, falta UI** | Producto |
| 24 | Cumplimiento y SGSI (ISO 27001) | ⏳ | 🎓 Académico + producto |
| 25 | Gestión de riesgos (ISO 27005) | ⏳ | 🎓 Académico + producto |
| 26 | Auditorías de sistemas (COBIT / ISO 19011) | ⏳ | 🎓 Académico + producto |
| 27 | Arquitectura empresarial (TOGAF / ArchiMate) | ⏳ | 🎓 Académico + producto |
| 28 | NetDoctor — diagnóstico multi-vendor | ⏳ | Producto · ⚠️ P3 con puerta de seguridad |
| 29 | Catálogo de equipos de red | ⏳ | Producto |
| 30 | Integraciones open source y mini-SOAR | ⏳ | Producto · ⚠️ P6 con puerta de seguridad |
| 31 | Hardening técnico automatizado | ✅ P1 | Producto · evaluación técnica basada en evidencia |
| 32 | Inventario de vulnerabilidades | 🟡 P1 cerrado; P2 pendiente | Producto · CVE/EPSS y exposición pasiva |
| 33 | Plataforma de entrega y automatización | ⏳ | Transversal · CI/CD, supply chain y agentes |

📋 Priorización y secuencia: **`../ROADMAP.md`** · Pendientes en detalle: **`../IMPLEMENTACION/00-BACKLOG-GLOBAL.md`**

---

## Módulos backend sin ficha propia

Registrados en `api/router.py` pero demasiado pequeños para justificar un documento:

| Módulo backend | Qué expone | Dónde se documenta |
|---|---|---|
| `organizations/` | `GET /organizations/` — devuelve solo la organización propia | **01** § multi-tenant |
| `collection/` | `GET /collection/snapshots` | **04** Integraciones |
| `catalogs/` | `GET /areas`, `/project-types`, `/products` | **20** Configuración |
| `docs/` | `doc-types` + `project-docs` | **19** Documentos |
| `client_sites/` · `client_contacts/` · `client_services/` | Sub-recursos de cliente | **03** Clientes |

---

## Flujos documentados

| Flujo | Módulos que cruza |
|---|---|
| `FLUJO-ONBOARDING-CLIENTE.md` | Leads → Clientes → Integraciones → Dispositivos |
| `FLUJO-LEAD-A-CLIENTE.md` | Pipeline comercial completo |
| `FLUJO-TICKET-SOPORTE.md` | Ciclo de vida de un ticket |
| `FLUJO-REVISION-SEGURIDAD.md` | Revisión técnica hasta el PDF |
| `FLUJO-DIAGNOSTICO-NETDOCTOR.md` | Tickets → Topología → NetDoctor → Auditoría ⏳ |
| `FLUJO-CUMPLIMIENTO-SGSI.md` | Dispositivos → Riesgos → Cumplimiento → Auditorías ⏳ |
| `FLUJO-ENTREGA-SEGURA.md` | Pull request → CI → release → staging → producción protegida |

---

## Resumen rápido de roles

| Rol | Acceso | Descripción |
|-----|--------|-------------|
| `super_admin` | Total | Fundador / CTO — acceso completo al sistema |
| `admin` | Amplio | Gerentes / líderes — gestión operativa |
| `collaborator` | Parcial | Técnicos, analistas, ingenieros del equipo |
| `client` | Portal | Usuarios de las empresas clientes |

---

## URLs del sistema

| Servicio | URL |
|----------|-----|
| Frontend (backoffice) | http://localhost:3018/dashboard |
| Portal cliente | http://localhost:3018/portal |
| API Backend (Swagger) | http://localhost:8024/docs |

---

## Credenciales de demo

⚠️ **Solo para el entorno local con datos sembrados.** Estas cuentas no deben existir en ningún entorno expuesto. Ver la rotación de secretos pendiente en `docs/deploy/HANDOFF-CLAUDE-OPS-UBUNTU.md` antes de FASE 2.8.

Contraseña: la del seed local (`PY-MK/backend/app/db/seed.py`) o la de `SEED_PASSWORD` si la pusiste. No se escribe aquí.

| Rol | Email |
|-----|-------|
| super_admin | admin@ninjasec.local |
| admin | admin2@ninjasec.local |
| collaborator | carlos.mendez@ninjasec.local |
| client (Blue Shield) | client@ninjasec.local |
| client (LogiGroup) | ti@logigroup.ninjasec.local |
| client (MediSalud) | ti@medisalud.ninjasec.local |

---

## Cómo agregar un módulo nuevo

1. Crear `PLANIFICACION/NN-MODULO-NOMBRE.md` — qué es, entidades, funcionalidades, matriz de roles, reglas de negocio
2. Crear `IMPLEMENTACION/NN-MODULO-NOMBRE.md` — checklist por fases con todo en ⏳
3. Agregar la fila en el índice de este README y en `IMPLEMENTACION/00-BACKLOG-GLOBAL.md` §1
4. Añadir las filas de roles en `01-ROLES-Y-ACCESOS.md` — la matriz se decide antes de codear, no después
5. Si el módulo introduce un proceso que cruza otros, documentar el flujo en `FLUJOS/`
6. Al codear: crear la carpeta en `backend/app/modules/`, registrar el router en `api/router.py`, y marcar ✅ en el checklist

**El siguiente número libre es el 34.**

### Convenciones que no se negocian

| Regla | Por qué |
|---|---|
| Los pendientes se identifican `NN-P-NN` (módulo · número) | Único en todo el proyecto; `20-P-08` se referencia desde cualquier documento sin ambigüedad |
| Un pendiente resuelto **se tacha con su evidencia**, no se borra | El historial de por qué algo estaba mal vale más que la tabla limpia |
| Todo `✅` lleva `archivo:línea` | Un checklist sin referencia verificable es una opinión |
| Todo modelo nuevo lleva `organization_id`, y todo `unique` se compone con él | Ver `01-ROLES-Y-ACCESOS.md` § multi-tenant |
| Nunca rehospedar datasheets de fabricante | Enlace oficial + respaldo Wayback + resumen propio citando la fuente |
