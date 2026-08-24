# Staging privado con Docker Compose

Este overlay ejecuta NinjaSec únicamente como staging interno. No habilita
producción, publicación WAN, runners, túneles, CD, backups automáticos ni
restauraciones.

## Controles del overlay

- El proyecto obligatorio es `ninjasec-staging`.
- Caddy publica solo HTTPS TCP en la dirección privada indicada por
  `STAGING_BIND_ADDRESS`; no publica HTTP ni HTTP/3.
- PostgreSQL no publica ningún puerto en el host.
- Los cuatro contenedores usan nombres con sufijo `staging`.
- La red y los volúmenes tienen nombres exclusivos de staging.
- Caddy usa certificados locales; `ACME_EMAIL` queda vacío.
- El backend desactiva seed, Redis, Google y las tres fuentes externas de
  reputación. Los conectores de infraestructura existentes son simulados.
- `APP_ENV=production` mantiene activas las validaciones estrictas de JWT y
  CORS también en staging.

Docker puede insertar reglas de red al publicar puertos. Antes del arranque se
debe verificar en el host que HTTPS siga limitado al CIDR interno aprobado; no
se debe confiar únicamente en UFW para filtrar un puerto publicado por Docker.

## Variables locales obligatorias

El archivo `/etc/ninjasec-staging/staging.env` se crea exclusivamente en la VM
con permisos `600`. Nunca se copia un `.env` existente ni se muestran sus
valores. Debe declarar como mínimo:

- `STAGING_BIND_ADDRESS`: dirección privada de la VM.
- `STAGING_HOSTNAME`: hostname interno aprobado.
- `STAGING_CORS_ORIGINS`: origen HTTPS exacto del hostname interno.
- `STAGING_BACKUP_PATH`: `/var/lib/ninjasec-staging/backups`.
- `DOMAIN`: el mismo valor que `STAGING_HOSTNAME`, requerido por la base de
  producción antes de fusionar el overlay.
- `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`: exclusivos de staging.
- `JWT_SECRET_KEY`: secreto nuevo y exclusivo de staging.
- `SEED_ON_STARTUP=false`.

`ACME_EMAIL`, `REDIS_URL`, `GOOGLE_CLIENT_ID`, `ABUSEIPDB_API_KEY`,
`VIRUSTOTAL_API_KEY` y `GREYNOISE_API_KEY` permanecen vacíos. No se configuran
integraciones reales ni datos de clientes.

## Validación estática segura

La validación no debe cargar ni imprimir el archivo de entorno real. Se usan
valores sintéticos solo en el entorno del proceso y se inspecciona una lista
permitida de propiedades del modelo resultante:

```bash
# Definir antes valores sintéticos en la sesión actual, sin usar un archivo .env.
docker compose --project-name ninjasec-staging \
  -f docker-compose.prod.yml \
  -f docker-compose.staging.yml \
  config --quiet
```

El arranque queda prohibido hasta aprobar las fases de firewall, configuración
local y SHA validado por CI. Su forma futura será:

```bash
sudo docker compose --project-name ninjasec-staging \
  --env-file /etc/ninjasec-staging/staging.env \
  -f docker-compose.prod.yml \
  -f docker-compose.staging.yml \
  up -d
```

No ejecutar `docker compose down -v`, restauraciones ni migraciones sobre bases
existentes.
