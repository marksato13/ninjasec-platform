# Ninja Tech

Plataforma para gestionar **clientes, proyectos y colaboradores** de una consultora de
infraestructura, nube, seguridad y desarrollo para pequeñas y medianas empresas.

**Ninja Tech** es la marca general. Tiene dos áreas activas, **Ninja Sec** (ciberseguridad e infraestructura segura)
y **Ninja Dev** (desarrollo de software), y tres futuras que todavía no existen: Ninja Infra, Ninja Cloud y Ninja
Auditoría. La mascota es **Kuro**.

> **Los nombres técnicos no cambian.** El repositorio, los contenedores, el dominio y las claves del navegador se
> siguen llamando `ninjasec-*`: renombrarlos toca producción y es un paso aparte.

🌐 **En línea:** <https://ninjasec-pe.duckdns.org>
*(Dominio gratuito de DuckDNS. Cambiará si se registra un dominio propio.)*

> **Origen:** Ninja Tech nace para que estudiantes de Desarrollo, Infraestructura y
> Ciberseguridad practiquen entregando valor real a PYMEs, con supervisión.

---

## Qué hace hoy

| Área | Qué permite |
|---|---|
| **Clientes y leads** | Captar un interés, convertirlo en cliente, llevar su historial |
| **Proyectos** | Tareas, miembros, estado y presupuesto, con vista Kanban |
| **Colaboradores** | Postulaciones, perfiles, habilidades, certificaciones y aprobaciones |
| **Planes de estudio** | Rutas de preparación para Fortinet NSE 4 y Cisco CCNA |
| **Revisiones y tickets** | Hallazgos de seguridad, riesgos, soporte a clientes |
| **Portal del cliente** | Cada cliente ve solo lo suyo |
| **Menús por rol** | El super admin decide qué ve cada rol en el sitio, el panel y el portal |
| **Auditoría** | Toda operación crítica queda registrada |

Roles: `super_admin`, `admin`, `collaborator` y `client`. Los datos de una organización
**nunca** se ven desde otra: pedir un recurso ajeno devuelve 404, no 403.

## Qué está apagado, y por qué

La **cápsula `telemetria`** agrupa los conectores a equipos de red, el hardening
automatizado, el informe SOC y el índice de salud. **Está apagada a propósito**:
los conectores todavía son simulados y no contactan ningún equipo real, así que
mostrarlos sería enseñar datos que parecen reales y no lo son.

Se enciende con `CAPSULAS_ACTIVAS=telemetria` cuando haya conectores de verdad. El
criterio completo está en [`DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md`](DOCUMENTOS/ESTRATEGIA/10-MODULOS-ACTIVABLES.md).

## Stack

| Capa | Tecnologías |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| Frontend | Next.js 16 · React 19 · TypeScript · Tailwind · TanStack Query |
| Datos | PostgreSQL 16 |
| Infraestructura | Docker Compose · Caddy (HTTPS automático) |

## Levantarlo en local

Requiere **Docker** y **Docker Compose v2**.

```bash
cd PY-MK
cp infra/.env.example infra/.env      # completa con valores propios
cd infra
docker compose -p ninjasec up -d --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3018 |
| API (documentación) | http://localhost:8024/docs |

El `-p ninjasec` **no es opcional**: sin él, Compose crea un stack paralelo con volúmenes vacíos.

⚠️ Los archivos `.env` no están en el repositorio y no deben estarlo.

**Primer usuario.** La base arranca vacía. Para poblar los catálogos en desarrollo,
define `SEED_PASSWORD` en tu `.env` y ejecuta el seed; en producción el seed **se niega
a correr** sin esa variable.

## Cómo se trabaja

```
 rama feature/xyz ──► Pull Request ──► CI ──► merge a main ──► la VM lo despliega sola
```

- **Nunca se trabaja sobre `main`.** Cada cambio va en una rama y un Pull Request.
- **El CI bloquea el merge** si falla alguna de estas verificaciones: pruebas del backend,
  build del frontend, Gitleaks (secretos), Semgrep y Trivy.
- **El despliegue es continuo:** un temporizador revisa `main` cada 5 minutos. Si
  avanzó, reconstruye, comprueba que backend y frontend estén sanos y, si no lo están,
  **vuelve solo a la versión anterior**.
- Los respaldos de PostgreSQL se verifican al crearse.

Detalle: [`DOCUMENTOS/ESTRATEGIA/`](DOCUMENTOS/ESTRATEGIA/) y [`AGENTS.md`](AGENTS.md).

## Dónde está cada cosa

| Carpeta | Contenido |
|---|---|
| [`PY-MK/`](PY-MK/) | La aplicación: backend, frontend e infraestructura |
| [`DOCUMENTOS/PLANIFICACION/`](DOCUMENTOS/PLANIFICACION/) | Requisitos de los módulos |
| [`DOCUMENTOS/IMPLEMENTACION/`](DOCUMENTOS/IMPLEMENTACION/) | Checklists con su evidencia |
| [`DOCUMENTOS/ESTRATEGIA/`](DOCUMENTOS/ESTRATEGIA/) | Despliegue, hosting, cápsulas, menús por rol |
| [`DOCUMENTOS/ROADMAP.md`](DOCUMENTOS/ROADMAP.md) | El orden de trabajo |
| [`qa/`](qa/) | Pruebas de extremo a extremo (Playwright) |

`DOCUMENTOS/HISTORICO/` es material antiguo y **no es fuente de verdad**.

## Seguridad

Si encuentras una vulnerabilidad, **no abras un issue público**: escribe al autor por
LinkedIn o por el formulario de contacto del sitio.

## Convenciones

- **Español** en documentación, interfaz y mensajes de commit; **inglés** en identificadores de código.
- Todo modelo con datos de negocio lleva `organization_id`, y todo `unique` se compone con él.
- Un pendiente resuelto se tacha con evidencia; no se borra.

## Autor

**Rubén Mark Salazar Tocas** — fundador de Ninja Tech.

## Licencia

**Propietaria, con el código visible** ([`LICENSE`](LICENSE)). Puedes leer y auditar el
código; copiarlo, modificarlo, redistribuirlo, ofrecerlo como servicio o usar la marca
Ninja Tech requiere permiso por escrito. Las dependencias conservan sus propias licencias.
