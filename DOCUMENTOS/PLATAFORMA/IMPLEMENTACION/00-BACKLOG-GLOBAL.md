# Backlog global — qué está implementado y qué falta

> Vista única de los 30 módulos. Verificado contra el código el **2026-08-06**.
> Los detalles de cada pendiente viven en el archivo del módulo; aquí solo está el índice.

**Convención de ID:** `NN-P-NN` = módulo · pendiente. Es único en todo el proyecto.
Un pendiente resuelto se tacha en su archivo y se anota la evidencia — nunca se borra.

---

## 1. Estado por módulo

| # | Módulo | Estado | Abiertos | 🔴 | Nota |
|---|--------|--------|:--------:|:--:|------|
| 01 | Roles y accesos | ✅ Operativo | 0 | – | Multi-tenancy documentado aquí |
| 02 | Dashboard | ✅ Operativo | 2 | 0 | Ambos son mejoras de UX |
| 03 | Clientes | ✅ Operativo | 0 | – | `03-P-06` cerrado el 2026-08-06 |
| 04 | Integraciones | ✅ Operativo | 0 | – | |
| 05 | Dispositivos | ✅ Operativo | 1 | 0 | |
| 06 | Revisiones de seguridad | ✅ Operativo | 1 | 0 | |
| 07 | Tickets de soporte | ✅ Operativo | 0 | – | |
| 08 | Leads | ✅ Operativo | 1 | 0 | Requiere dependencia nueva |
| 09 | Reportes | ✅ Operativo | 1 | 0 | |
| 10 | Colaboradores | ✅ Operativo | 1 | 0 | `10-P-06` cerrado el 2026-08-06 |
| 11 | Servicios | ✅ Operativo | 0 | – | `11-P-05` cerrado el 2026-08-06 |
| 12 | Proyectos | ✅ Operativo | 0 | – | `12-P-06` cerrado el 2026-08-06 |
| 13 | Usuarios | ✅ Operativo | 0 | – | |
| 14 | Portal cliente | ✅ Operativo | 0 | – | |
| 15 | Postulaciones | ✅ Operativo | 6 | 2 | Único endpoint público de la API |
| 16 | Auditoría | ✅ Operativo | 6 | 1 | |
| 17 | Aprobaciones | ✅ Operativo | 6 | 3 | 2 son duplicados del 21 |
| 18 | Alertas | ✅ Operativo | 7 | 2 | Umbrales hardcodeados |
| 19 | Documentos | ✅ Operativo | 6 | 1 | Bloqueado por el storage |
| 20 | Configuración | ⚠️ **Parcial** | 11 | 6 | El menos completo · **1 crítico** |
| 21 | Skills y certificaciones | ✅ Operativo | 7 | 2 | |
| 22 | Tareas del portal | ⚠️ **Parcial** | 5 | 1 | No hay entidad `Task` real |
| 23 | Topología | 🟡 **Backend hecho, sin UI** | – | – | El endpoint existe y nadie lo consume |
| 24 | Cumplimiento SGSI | ⏳ No iniciado | – | – | Académico |
| 25 | Riesgos | ⏳ No iniciado | – | – | Académico |
| 26 | Auditorías COBIT | ⏳ No iniciado | – | – | Académico |
| 27 | Arquitectura empresarial | ⏳ No iniciado | – | – | Académico |
| 28 | NetDoctor | ⏳ No iniciado | – | – | P3 con puerta de seguridad |
| 29 | Catálogo de equipos | ⏳ No iniciado | – | – | |
| 30 | Integraciones open source | ⏳ No iniciado | – | – | P6 con puerta de seguridad |

**Totales:** 22 módulos construidos · **61 pendientes abiertos** · **58 resueltos y documentados** · 8 módulos por empezar.

---

## 2. Lo que hay que arreglar antes de seguir construyendo

Ordenado por consecuencia, no por esfuerzo.

### 🔴 Crítico — tiene consecuencia fuera del sistema

| ID | Pendiente | Por qué no puede esperar |
|---|---|---|
| `20-P-08` | `GET /products` no filtra por organización | Fuga de datos entre tenants. Hoy inocuo porque solo hay una organización; deja de serlo con la segunda, y para entonces ya estará en producción. **El fix es una línea** |
| `21-P-02` = `17-P-05` | Expiración de certificaciones no evaluada | El directorio muestra "verificado" sobre certificaciones caducadas. **Es información falsa entregada a un cliente** |
| `21-P-01` = `17-P-04` | Editar no revierte la aprobación | Se aprueba "Cisco básico", se edita a "CCIE" y queda verificado sin nueva revisión |
| `15-P-05` | Sin rate limiting en el endpoint público | `POST /job-applications/` es el único sin autenticación. Bloqueante antes de exponer en FASE 2.8 |

### 🟠 Estructural — bloquea el crecimiento

| ID | Pendiente | Qué bloquea |
|---|---|---|
| `20-P-09` | `unique` global en catálogos multi-tenant | El segundo tenant no puede dar de alta sus propios catálogos. **Más barato antes de tener datos que colisionen** |
| `20-P-06` | Sin `POST`/`PUT` de areas y project-types | Toda la administración de catálogos → bloquea `20-P-01`, `20-P-02` |
| `19-P-01` | Sin storage de archivos | Bloquea `10-P-05`, `15-P-02`, `19-P-01`, `21-P-05` — **4 pendientes, una sola decisión** |
| `20-P-05` | Umbrales hardcodeados | Bloquea `18-P-02` |
| — | Alembic no es la fuente de verdad del esquema | Ver sección 4 |

**Sumadas, las dos tablas son ~1 sesión.** Es la Tanda 0 del `ROADMAP.md`.

---

## 3. Pendientes abiertos por módulo

### Módulos 01-14 — 7 abiertos, ninguno crítico

| ID | Pendiente | Naturaleza |
|---|---|---|
| `02-P-04` | Deep-link `?severity=X` en revisiones | UX menor |
| `02-P-05` | WebSocket en vez de polling 60s | Sin caso de uso todavía |
| `05-P-05` | Filtro por sede en el portal | Backend listo, falta UI |
| `06-P-05` | PDF desde el listado | UX menor |
| `08-P-02` | Drag & drop real en el Kanban | **Requiere dependencia nueva** (`@dnd-kit`) |
| `09-P-05` | `lastRun` server-side | Hoy en `localStorage`, o sea por dispositivo |
| `10-P-05` | Upload de imagen | **Bloqueado por el storage** (`19-P-01`) |

> El README llamaba a estos módulos "cerrados". Están **operativos**, que no es lo mismo: quedan 7 cabos sueltos, todos de baja consecuencia.

### Módulos 15-22 — 54 abiertos, 17 de prioridad alta

| Módulo | 🔴 Alta | 🟡 Media | 🟢 Baja |
|---|:---:|:---:|:---:|
| 15 Postulaciones | `15-P-01` `15-P-05` | `15-P-02` `15-P-03` `15-P-06` | `15-P-04` |
| 16 Auditoría | `16-P-01` | `16-P-02` `16-P-03` `16-P-04` `16-P-06` | `16-P-05` |
| 17 Aprobaciones | `17-P-01` `17-P-02` `17-P-04` `17-P-05` | `17-P-03` | `17-P-06` |
| 18 Alertas | `18-P-02` `18-P-04` | `18-P-01` `18-P-03` `18-P-06` `18-P-07` | `18-P-05` |
| 19 Documentos | `19-P-01` | `19-P-02` `19-P-03` `19-P-04` | `19-P-05` `19-P-06` |
| 20 Configuración | `20-P-08` `20-P-09` `20-P-01` `20-P-02` `20-P-05` `20-P-06` | `20-P-03` `20-P-04` `20-P-07` `20-P-10` `20-P-11` | — |
| 21 Skills / certs | `21-P-01` `21-P-02` | `21-P-03` `21-P-04` `21-P-05` | `21-P-06` `21-P-07` |
| 22 Tareas portal | `22-P-01` | `22-P-02` `22-P-04` | `22-P-03` `22-P-05` |

---

## 4. Deuda que no está en ninguna tabla de módulo

Cosas que no pertenecen a un módulo pero condicionan a todos.

| # | Deuda | Evidencia | Consecuencia |
|---|---|---|---|
| G-01 | **Alembic no es la fuente de verdad del esquema** | `app/main.py:19` llama `Base.metadata.create_all()`; `migrations/versions/` solo tiene 2 archivos y el primero tiene `down_revision = None` sin crear tablas | `create_all` crea lo que falta pero **nunca altera lo existente**. Todo cambio futuro de modelo se aplica en una base vacía y se ignora en silencio en una con datos |
| G-02 | Sin migración base | misma evidencia | `alembic upgrade head` sobre una base vacía falla: intenta `add_column` sobre tablas que no existen |
| G-03 | Secretos comprometidos sin rotar | `docs/deploy/HANDOFF-CLAUDE-OPS-UBUNTU.md` | `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` y el token DuckDNS deben rotarse **antes** de cualquier exposición pública |
| G-04 | Logs de desarrollo en el repo | 10 archivos `backend-*.log` en `backend/` | Ruido; revisar que no lleven datos sensibles antes de decidir |
| G-05 | `FIX-INVENTARIO-PRIMERO-SIN-INTEGRACION.ml` | `FIX/` | Extensión mal escrita (`.ml`), stub de 7 líneas cuyo contenido ya está completo en el `.md` gemelo. No renderiza |
| G-06 | Módulos backend sin ficha | `organizations/`, `collection/` | Registrados en `api/router.py` y sin documento propio. Son thin (1 endpoint cada uno) — se cubren en 01 y 04 |

**G-01 y G-02 son bloqueantes de FASE 2.8** (deploy self-hosted). Ver `ROADMAP.md`.

---

## 5. Decisiones que desbloquean varios pendientes a la vez

| Decisión | Desbloquea | Recomendación |
|---|---|---|
| Storage de archivos | `10-P-05` · `15-P-02` · `19-P-01` · `21-P-05` | Una sola decisión, 4 pendientes |
| Librería de diagramación | `23-P1` · `27-P3` | **React Flow** (`@xyflow/react`) — se amortiza en dos módulos |
| Editor ArchiMate propio vs. importar de Archi | `27-P3` | **Importar** — ahorra ~3 sesiones |
| ¿Se retoma FASE 2.6 del lab? | `30-P7` | El lab es el mejor entorno de pruebas del módulo 30 |
| Estrategia Alembic | G-01 · G-02 | Generar la migración base con `--autogenerate` y quitar `create_all` de `main.py` |

---

## Cómo mantener este archivo

Se actualiza **al cerrar un pendiente o al detectar uno nuevo**, no en cada commit.

1. Tachar el pendiente en el archivo de su módulo con la evidencia (`archivo:línea`)
2. Ajustar el contador de la tabla de la sección 1
3. Sacarlo de las tablas de las secciones 2 y 3

Si un pendiente aparece en dos módulos, se marca el duplicado y **se arregla una sola vez** — como `17-P-04` / `21-P-01`.
