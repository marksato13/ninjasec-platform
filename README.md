# NinjaSec — Plataforma

Plataforma de infraestructura y ciberseguridad para PYMEs, consultoras y MSPs. Un mismo sistema cubre el ciclo completo de un proveedor de servicios de seguridad: captar clientes (leads → propuesta → alta), operarlos (inventario de dispositivos, integraciones de monitoreo, revisiones de seguridad con hallazgos, tickets de soporte), gestionar al equipo (reclutamiento, colaboradores, skills y certificaciones, portal propio) y sostenerlo con controles internos (auditoría, aprobaciones, alertas, roles y aislamiento por organización). El cumplimiento normativo (ISO 27001 / 27005 / 19011, COBIT, TOGAF) se documenta como subproducto de la operación real, no como papeleo aparte.

> **Origen:** nace como consultoría para que estudiantes de Desarrollo, Infraestructura y Ciberseguridad practiquen entregando valor real a PYMEs. Hoy es un MVP avanzado — 22 de 30 módulos operativos en producción, con una flota de agentes de IA ([self-hosted-ai-devops](https://github.com/marksato13/self-hosted-ai-devops)) avanzando el resto issue por issue.

### 🔗 Vista previa en vivo

**https://compression-solutions-encourages-specify.trycloudflare.com**

Backend, frontend y base de datos reales — no es una demo estática. Un timer systemd reconstruye el stack automáticamente cada vez que `main` avanza (cada 5 min como máximo de retraso), así que este link siempre refleja el último merge. Login con las credenciales del seed (`admin@ninjasec.local` / `change-me` para super_admin; el resto de roles en `PY-MK/CLAUDE.md`).

⚠️ **La URL puede cambiar.** Es un túnel gratuito de Cloudflare sin dominio propio (`trycloudflare.com`), y esos túneles no tienen hostname fijo: si el proceso se reinicia (crash, reboot), Cloudflare asigna una URL nueva al azar. El proceso se auto-reinicia solo (systemd), pero la URL de arriba puede quedar desactualizada — si no carga, avisa y se regenera el link.

---

## Qué hay en este repositorio

| Carpeta | Contenido |
|---|---|
| **`PY-MK/`** | La aplicación: backend FastAPI, frontend Next.js, infra Docker |
| **`DOCUMENTOS/`** | Toda la documentación de plataforma: 30 módulos especificados, checklists de implementación, flujos y roadmap |
| **`tash/`** | Brainstorming y notas sueltas. **No es especificación** — nada de aquí es fuente de verdad |

---

## Por dónde empezar

| Si quieres… | Lee |
|---|---|
| Entender el proyecto y sus reglas técnicas | `PY-MK/CLAUDE.md` |
| Saber qué hacer ahora | `DOCUMENTOS/PLATAFORMA/ROADMAP.md` |
| Ver qué está hecho y qué falta | `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/00-BACKLOG-GLOBAL.md` |
| Entender un módulo concreto | `DOCUMENTOS/PLATAFORMA/PLANIFICACION/NN-*.md` |
| Saber quién puede hacer qué | `DOCUMENTOS/PLATAFORMA/PLANIFICACION/01-ROLES-Y-ACCESOS.md` |
| Instalar o adoptar una base con Alembic | `PY-MK/docs/deploy/RUNBOOK-ALEMBIC.md` |

---

## Stack

**Backend** — Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · PyJWT · PostgreSQL 16
**Frontend** — Next.js 15 (App Router) · React 19 · TypeScript · Tailwind 3 · TanStack Query 5 · React Hook Form + Zod
**Infra** — Docker Compose · Caddy 2

| Servicio | URL local |
|---|---|
| Frontend (backoffice) | http://localhost:3018/dashboard |
| Portal cliente | http://localhost:3018/portal |
| API (Swagger) | http://localhost:8024/docs |

---

## Levantar el entorno

```bash
cd PY-MK
cp infra/.env.example infra/.env      # completar con valores propios
cp backend/.env.example backend/.env
./up.ps1                               # Windows
```

⚠️ **Los archivos `.env` no están en el repositorio y no deben estarlo.** Usa los `.example` como plantilla.

---

## Antes de exponer esto en producción

Está documentado en detalle en `DOCUMENTOS/PLATAFORMA/ROADMAP.md`, pero lo esencial:

1. **Rotar los secretos comprometidos** — `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` y el token DuckDNS. Ver `PY-MK/docs/deploy/HANDOFF-CLAUDE-OPS-UBUNTU.md`
2. **Tanda 0 del roadmap** — seis huecos de integridad, incluido `20-P-08` (fuga de datos entre organizaciones, fix de una línea)
3. **Tanda 0-bis** — Alembic no construye el esquema hoy (`Base.metadata.create_all()` en `main.py`). Bloqueante para cualquier base con datos que haya que actualizar
4. **Eliminar las cuentas de demo** — la contraseña universal de `seed_demo.py` no puede existir en un entorno expuesto

---

## Convenciones

- **Español** para documentación, UI y mensajes de commit · **inglés** para identificadores de código
- Los pendientes se identifican `NN-P-NN` (módulo · número) y son únicos en todo el proyecto
- Un pendiente resuelto se tacha con su evidencia (`archivo:línea`), no se borra
- Todo modelo con datos de negocio lleva `organization_id`, y todo `unique` se compone con él

Detalle completo en `DOCUMENTOS/PLATAFORMA/PLANIFICACION/README.md`.
