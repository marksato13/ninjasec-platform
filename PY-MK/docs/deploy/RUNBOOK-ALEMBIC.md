# Runbook operativo de Alembic

Este documento describe cómo crear y actualizar el esquema PostgreSQL de
NinjaSec una vez que Alembic es la fuente de verdad. Está dirigido a quien
opera el entorno, no a quien redacta una migración nueva.

> **Regla de seguridad:** no ejecutes `stamp`, `downgrade` ni una migración
> sobre una base con datos sin un respaldo restaurado y verificado. `stamp`
> solo escribe una versión: no crea, corrige ni valida tablas.

## Alcance y supuestos

- Los comandos se ejecutan desde `PY-MK/`.
- PostgreSQL 16 es el motor soportado para validar migraciones.
- `infra/.env` existe, tiene permisos restrictivos y no se imprime ni se
  incorpora al repositorio.
- Los nombres reales de las revisiones se obtienen con Alembic. Este runbook
  no fija una revisión base en texto para no quedar obsoleto.
- SQLite sigue siendo útil para pruebas rápidas de la aplicación, pero no
  demuestra que una migración PostgreSQL funcione.

## Comprobaciones previas

Antes de cualquier cambio:

```bash
git status --short
docker compose -f infra/docker-compose.yml --env-file infra/.env ps
docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T backend python -m alembic heads
docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T backend python -m alembic history --verbose
```

Debe existir una sola cabeza. Si `heads` devuelve más de una, detén el
procedimiento: primero hay que resolver la bifurcación de migraciones en una
rama de código y mediante PR.

## Instalación limpia

Este flujo corresponde a una base vacía, sin tablas de NinjaSec.

1. Levanta PostgreSQL sin iniciar todavía tráfico hacia el backend.
2. Ejecuta todas las migraciones.
3. Comprueba la revisión y recién después inicia la aplicación.

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d postgres
docker compose -f infra/docker-compose.yml --env-file infra/.env build backend

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic upgrade head

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic current

docker compose -f infra/docker-compose.yml --env-file infra/.env up -d backend frontend
curl --fail --silent --show-error http://127.0.0.1:8024/health
```

El resultado de `current` debe terminar en `(head)` y `/health` debe responder
con estado HTTP 200. Repetir `upgrade head` debe finalizar sin aplicar DDL
adicional ni producir errores.

No cargues datos demo en un entorno real. El seed de arranque solo debe estar
habilitado en un entorno local desechable.

## Actualización normal de una base versionada

Una base versionada contiene la tabla `alembic_version` y su revisión pertenece
al historial del código que se va a desplegar.

1. Crea y verifica el respaldo según la sección siguiente.
2. Detén las escrituras de la aplicación.
3. Consulta `current` y confirma que la revisión aparece en `history`.
4. Ejecuta `upgrade head` una sola vez desde un job o contenedor.
5. Inicia el backend y realiza las verificaciones posteriores.

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env stop backend

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic current

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic upgrade head

docker compose -f infra/docker-compose.yml --env-file infra/.env up -d backend
```

No lances migraciones simultáneamente desde varias réplicas. El despliegue debe
tener un único paso de migración y hacer fallar el arranque si ese paso falla.

## Respaldo y restauración verificable

Guarda el dump fuera del repositorio y limita sus permisos. El ejemplo usa un
nombre explícito para evitar sobrescribir respaldos anteriores.

```bash
install -d -m 700 backups

docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres sh -c \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > backups/ninjasec-pre-alembic.dump

chmod 600 backups/ninjasec-pre-alembic.dump
docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres pg_restore --list \
  < backups/ninjasec-pre-alembic.dump >/dev/null
```

Listar el dump verifica su formato, pero no basta. Hay que restaurarlo en una
base temporal independiente. Los dos comandos que eliminan la base temporal
son intencionalmente destructivos y **solo** pueden apuntar al nombre literal
`ninjasec_restore_verify`.

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --if-exists ninjasec_restore_verify && createdb -U "$POSTGRES_USER" ninjasec_restore_verify'

docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d ninjasec_restore_verify --exit-on-error' \
  < backups/ninjasec-pre-alembic.dump

docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres sh -c \
  'psql -U "$POSTGRES_USER" -d ninjasec_restore_verify -v ON_ERROR_STOP=1 -c "SELECT count(*) AS tablas FROM information_schema.tables WHERE table_schema = '\''public'\'';"'
```

Además del número de tablas, compara conteos de las entidades importantes para
el entorno —por ejemplo organizaciones, usuarios, clientes, dispositivos,
proyectos y auditoría— entre el origen y la restauración. No registres filas ni
campos sensibles como evidencia; registra únicamente los conteos.

Cuando la verificación termine:

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env \
  exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --if-exists ninjasec_restore_verify'
```

## Adopción de una base creada con `create_all`

Las instalaciones antiguas pueden tener todas o parte de las tablas, pero no
`alembic_version`. Ejecutar `upgrade head` directamente sobre ellas intentaría
crear objetos ya existentes. No lo hagas.

### 1. Trabajar sobre la restauración

Haz la clasificación sobre `ninjasec_restore_verify`, nunca sobre el único
ejemplar de la base real. Mantén detenidas las escrituras durante el cambio
final para que el respaldo validado corresponda al estado migrado.

Comprueba primero si la base ya está versionada:

```sql
SELECT to_regclass('public.alembic_version') AS tabla_version;
```

Si existe, consulta su valor con `alembic current` y sigue el flujo de
actualización normal. Si no existe, continúa con la clasificación.

### 2. Clasificar el esquema, no adivinarlo

Obtén las revisiones reales:

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic history --verbose
```

Compara la base restaurada con el esquema que representa cada revisión. Como
mínimo revisa:

- tablas, columnas, tipos y nulabilidad;
- claves primarias y foráneas;
- restricciones `UNIQUE` e índices;
- tipos enum y sus valores en PostgreSQL;
- columnas y tablas introducidas por cada migración incremental.

La revisión elegida debe describir **todo** el esquema encontrado, no solo una
columna conocida. Si no coincide exactamente con ninguna revisión, no uses
`stamp`: documenta el drift y crea una migración de adopción específica.

Casos permitidos:

| Estado comprobado | Acción |
|---|---|
| Equivale exactamente a la revisión base | `stamp` de la revisión base y luego `upgrade head` |
| Equivale exactamente a una revisión incremental | `stamp` de esa revisión y luego `upgrade head` |
| Equivale exactamente al esquema de `head` | `stamp head`; no se repiten migraciones antiguas |
| No coincide o no se puede demostrar | Detenerse; requiere migración de adopción y revisión humana |

### 3. Aplicar `stamp` primero en la restauración

Prepara `infra/.env.restore` como copia local protegida de la configuración que
usa Compose, pero establece `POSTGRES_DB=ninjasec_restore_verify`. Así, la
`DATABASE_URL` que construye el servicio backend apunta exclusivamente a la
restauración. No reutilices este archivo para producción, no lo incorpores a
Git y limita sus permisos con `chmod 600 infra/.env.restore`. Sustituye
`<revision_comprobada>` por el identificador obtenido de `history`:

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env.restore \
  run --rm backend \
  python -m alembic stamp <revision_comprobada>

docker compose -f infra/docker-compose.yml --env-file infra/.env.restore \
  run --rm backend \
  python -m alembic upgrade head
```

La URL debe apuntar inequívocamente a `ninjasec_restore_verify`. No copies la
URL real ni sus credenciales a tickets, commits o logs. Tras el ensayo, repite
los conteos y valida la aplicación contra esa restauración.

Solo después de que el ensayo sea reproducible se aplica la misma clasificación
y secuencia a la base original, con las escrituras detenidas y el respaldo
verificado disponible.

## Verificación posterior

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic current

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic heads

docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm backend \
  python -m alembic check

curl --fail --silent --show-error http://127.0.0.1:8024/health
```

La aceptación requiere:

- `current` y la única revisión de `heads` coinciden;
- `alembic check` no detecta operaciones nuevas;
- el backend está saludable;
- autenticación y una consulta de solo lectura funcionan;
- los conteos de datos críticos no disminuyeron;
- los logs no contienen errores de esquema, restricciones ni enums.

## Rollback

Las migraciones hacia atrás son una herramienta de desarrollo, no el plan de
recuperación de producción. Un downgrade puede fallar por datos que ya usan la
nueva estructura —por ejemplo valores nulos o duplicados permitidos después de
un cambio de restricción— y puede eliminar columnas o tablas.

Ejecuta `downgrade` únicamente en una base desechable creada para la prueba:

```bash
# Solo con DATABASE_URL apuntando a una base temporal verificada.
python -m alembic downgrade -1
python -m alembic upgrade head
```

En producción, ante una migración fallida:

1. impide que arranque la versión nueva del backend;
2. conserva logs y la revisión reportada por `current`;
3. restaura el dump verificado en una base nueva;
4. valida conteos y salud;
5. cambia la aplicación hacia la base restaurada siguiendo el procedimiento
   operativo del entorno.

No ejecutes `downgrade base`, `DROP`, `DELETE` ni restauraciones sobre la única
base productiva.

## Solución de problemas

| Síntoma | Causa probable | Acción segura |
|---|---|---|
| `relation ... already exists` | Base `create_all` sin clasificar | Detener; restaurar el backup y seguir el flujo de adopción |
| `Can't locate revision` | Código e historial de la base no corresponden | Desplegar el commit que contiene la revisión o preparar una reconciliación; no borrar `alembic_version` |
| Más de una cabeza | Ramas de migración divergentes | Crear y revisar una migración de merge; no elegir una cabeza al azar |
| `Target database is not up to date` | Revisión pendiente o `stamp` incorrecto | Comparar `current`, `heads` y `history`; no forzar otro `stamp` |
| Falla una FK o `UNIQUE` | Datos heredados contradicen la nueva restricción | Identificar conteos conflictivos y preparar limpieza auditada; no borrar filas automáticamente |
| Falla el downgrade de `devices.integration_id` | Existen valores `NULL` | No forzar el downgrade; recuperar mediante restore |
| Falla restauración | Dump incompleto, versión incompatible o permisos | No migrar el origen; corregir y repetir la restauración verificable |
| Las pruebas SQLite pasan pero PostgreSQL falla | Diferencias de dialecto | Repetir la prueba en PostgreSQL 16 desechable |
| Backend arranca con revisión pendiente | El arranque no está fallando cerrado | Detenerlo y corregir el paso único de migración antes de aceptar el despliegue |

## Evidencia mínima del cambio

Conserva en el PR o informe operativo, sin secretos:

- commit desplegado;
- salida de `heads` y revisión final de `current`;
- hora de creación y restauración exitosa del respaldo;
- conteos antes y después;
- resultado de `alembic check`;
- estado de `/health`;
- incidencia y recuperación aplicada, si hubo una.

No adjuntes dumps, `.env`, URLs con contraseña ni contenido de tablas.
