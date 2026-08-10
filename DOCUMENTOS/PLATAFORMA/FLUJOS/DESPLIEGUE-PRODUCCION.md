# Despliegue a producción — infraestructura gratuita

> Creado: 2026-08-10 (issue #87) · Documento de decisión + runbook, no requiere cambios de código.

---

## Resumen

**El camino a producción ya está construido.** `infra/docker-compose.prod.yml` + `infra/Caddyfile` + los `Dockerfile` de `backend/` y `frontend/` ya arman un stack completo: Postgres, backend FastAPI (corre las migraciones de Alembic automáticamente al arrancar — ver `app/db/migrate.py`), frontend Next.js, y Caddy como reverse proxy con HTTPS automático gratis vía Let's Encrypt.

**No costo recurrente si ya tenés dónde correrlo** (servidor propio, VPS que ya pagás por otra razón, home lab). El único requisito externo gratuito es un nombre de dominio dinámico vía [DuckDNS](https://www.duckdns.org/) (gratis) o un dominio comprado (no gratis, pero opcional — DuckDNS alcanza).

Lo que faltaba no era el stack — era **este documento**: nadie había escrito el runbook de "cómo se enciende esto en un servidor real por primera vez", y no había una comparación honesta contra alternativas de nube gratuita para quien no tiene un servidor propio.

---

## Restricciones reales que cualquier opción debe cumplir

Verificadas contra el código, no supuestas:

1. **WebSocket persistente** (`GET /api/v1/alerts/ws`, issue #41) — descarta cualquier hosting serverless puro (funciones que no sostienen conexiones abiertas). Caddy y cualquier VPS/contenedor de larga duración lo cumplen sin configuración especial.
2. **Postgres con persistencia real** — no un free tier que borre la base por inactividad sin aviso. El volumen `postgres_data` en `docker-compose.prod.yml` ya lo resuelve si Postgres corre en el mismo host; si se usa un Postgres gestionado externo, hay que verificar la política de inactividad del proveedor.
3. **`NEXT_PUBLIC_API_URL` relativo + rewrites de Next.js** (ver `CLAUDE.md` § Decisiones técnicas 1 y 2) — el frontend y el backend deben quedar detrás del mismo dominio (recomendado, ya resuelto por Caddy) o el CORS debe configurarse explícitamente si van en dominios distintos.
4. **Rate limiter** (`app/common/rate_limit.py`, issue #84) — con `REDIS_URL` sin configurar usa el limitador en memoria de un solo proceso. El stack actual corre un único proceso backend, así que esto no es un problema hoy; solo importa si se escala a múltiples réplicas.

---

## Opción recomendada: self-hosted con el stack ya construido

### Qué se necesita

- Un servidor Linux con Docker y Docker Compose (VPS propio, servidor físico, home lab — cualquier cosa con IP pública o accesible vía DuckDNS).
- Un subdominio DuckDNS (gratis, `algo.duckdns.org`) o un dominio propio.
- Los puertos 80 y 443 abiertos hacia ese servidor.

### Runbook de primer arranque

```bash
# 1. En el servidor, clonar el repo y entrar a infra/
git clone <repo> && cd ninjasec-platform/PY-MK/infra

# 2. Copiar y completar el .env real (nunca commitear este archivo)
cp ../.env.example .env
# Editar .env:
#   - POSTGRES_PASSWORD: openssl rand -base64 24
#   - JWT_SECRET_KEY:    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
#   - DOMAIN:            tu-subdominio.duckdns.org (o tu dominio)
#   - ACME_EMAIL:        tu email (Let's Encrypt manda avisos de expiración ahí)
#   - CORS_ORIGINS:      https://tu-subdominio.duckdns.org
#   - IS_PRODUCTION:     true
#   - SEED_ON_STARTUP:   false   ← IMPORTANTE, ver advertencia abajo

# 3. Levantar el stack
docker compose -f docker-compose.prod.yml --env-file .env up -d --build

# 4. Verificar que las migraciones corrieron limpio (backend/Dockerfile las
#    corre automáticamente antes de arrancar uvicorn)
docker compose -f docker-compose.prod.yml logs backend | grep -i alembic

# 5. Verificar salud de los tres servicios
curl https://tu-subdominio.duckdns.org/health          # Caddy
docker compose -f docker-compose.prod.yml ps            # healthy en los 4
```

⚠️ **`SEED_ON_STARTUP=true` en producción sembraría los 17 clientes demo, usuarios con contraseñas conocidas (`admin@ninjasec.local` / `change-me`, etc.) y datos ficticios en la base real.** Verificar que quede en `false` antes del primer arranque en el servidor real — es la variable más fácil de olvidar cambiar porque en dev siempre está en `true`.

### Primer usuario real

Con `SEED_ON_STARTUP=false` la base arranca vacía (solo el esquema). Crear el primer `super_admin` real requiere un insert directo (no hay endpoint público de "crear el primer admin" — correcto, sería un agujero de seguridad):

```bash
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User
from app.db.models.enums import RoleCode, UserStatus
from app.core.security import hash_password

db = SessionLocal()
org = Organization(name='Tu Empresa', slug='tu-empresa')
db.add(org); db.flush()
role = Role(code=RoleCode.SUPER_ADMIN.value, name='Super Admin')
db.add(role); db.flush()
db.add(User(
    organization_id=org.id, role_id=role.id, role_code=RoleCode.SUPER_ADMIN,
    full_name='Tu Nombre', email='tu-email-real@dominio.com',
    password_hash=hash_password('CAMBIA-ESTO-INMEDIATAMENTE'),
    status=UserStatus.ACTIVE, is_active=True,
))
db.commit()
"
```

Cambiar la contraseña inmediatamente después del primer login.

### Backups

`docker-compose.prod.yml` ya monta `./backups:/backups` en el contenedor de Postgres, pero **no hay ningún job automático que escriba ahí todavía** — es un punto de montaje, no una funcionalidad. Backup manual mientras no se automatice:

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > backups/ninjasec_$(date +%Y%m%d).sql.gz
```

Automatizar esto con un cron simple en el host (o un contenedor sidecar) es trabajo de código, no de este documento — queda como pendiente explícito, no implícito.

### Actualizar a una versión nueva

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
# El backend corre las migraciones nuevas automáticamente al reiniciar.
```

### Límites reales de esta opción

- **Disponibilidad = disponibilidad del servidor.** Sin proveedor gestionado, un corte de luz/internet en el sitio tumba el servicio. Aceptable para un MVP o una PYME; no para un SLA de alta disponibilidad.
- **El operador es responsable de parches del SO, Docker y renovación de DNS dinámico** (DuckDNS requiere refrescar el registro periódicamente — automatizable con un cron de una línea, no incluido en el stack todavía).
- **Sin backups automáticos** (ver arriba) hasta que se implemente.

---

## Alternativa: si no hay servidor propio disponible

Comparación honesta para alguien que necesita desplegar sin tener ya un servidor — por ejemplo, para una demo académica sin acceso a infraestructura propia. **No es la opción recomendada si ya existe un servidor disponible** — el stack self-hosted ya está construido, probado y sin las limitaciones de free tier que siguen.

| Opción | Costo | Limitación real | Cumple WebSocket persistente | Cumple Postgres persistente |
|---|---|---|---|---|
| **Oracle Cloud Free Tier** (VM ARM Ampere, 4 OCPU/24GB gratis *siempre*, no es trial) | Gratis indefinido | Cuenta requiere tarjeta de crédito para verificación (no cobra si te mantenés en el free tier); disponibilidad de instancias ARM varía por región | ✅ (es una VM real, mismo Docker Compose de arriba) | ✅ |
| **Fly.io free allowance** | Gratis hasta cierto uso, luego cobra | Pensado para apps pequeñas; Postgres gestionado de Fly no es gratis más allá de una instancia mínima; puede dormir procesos con poco tráfico según el plan | 🟡 depende del plan | 🟡 con matices |
| **Render free tier** | Gratis con límites | Los servicios web free **se duermen tras 15 min sin tráfico entrante** (incluye WebSocket sin mensajes nuevos) y tardan ~1 minuto en reactivarse — inaceptable para el WebSocket de alertas, que necesita la conexión viva. Verificado en la documentación oficial de Render (2026-08-10). Postgres free se borra a los 90 días | ❌ | ❌ (borrado a los 90 días) |
| **Railway** | Solo trial, no free tier permanente | Ya no ofrece un plan gratuito indefinido (cambió su modelo) — se descarta para "gratuito" | — | — |

**Recomendación dentro de esta alternativa: Oracle Cloud Free Tier**, porque es la única que es (a) gratis de forma permanente, no un trial, y (b) una VM real donde corre el mismo `docker-compose.prod.yml` sin adaptarlo — no hay que rediseñar nada del stack, solo apuntar el mismo runbook de arriba a esa VM en vez de un servidor propio.

---

## Qué falta para considerar esto "listo para producción" (más allá del despliegue en sí)

Explícitamente fuera del alcance de este documento — son decisiones o acciones humanas, no código que se pueda escribir sin esas decisiones:

- **#19** (rotar secretos de producción comprometidos) — acción humana, no asignable a la flota.
- **Registrar el dominio/subdominio real** y las cuentas del proveedor elegido (Oracle Cloud, DuckDNS) — requiere que el usuario decida y ejecute, no algo que este documento pueda hacer por él.
- **Automatizar backups** — trabajo de código real (cron o sidecar), no de este documento.
- **Renovación automática de DuckDNS** — un cron de una línea, mismo caso.

---

## Referencias en el repo

- `PY-MK/infra/docker-compose.prod.yml` — stack completo
- `PY-MK/infra/Caddyfile` — reverse proxy + HTTPS + cabeceras de seguridad OWASP
- `PY-MK/.env.example` — todas las variables, con instrucciones de generación de secretos
- `PY-MK/backend/app/db/migrate.py` — migraciones automáticas al arrancar (issue #2 / G-01, G-02)
- `PY-MK/backend/Dockerfile`, `PY-MK/frontend/Dockerfile` — build de producción
