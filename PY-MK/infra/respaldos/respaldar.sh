#!/bin/sh
# Respaldo de PostgreSQL para NinjaSec.
#
# Hasta ahora `./backups` era un punto de montaje vacio: estaba declarado en
# el compose y no habia nada que escribiera dentro. Esto es lo que escribe.
#
# Corre dentro de un contenedor propio, en bucle, no como cron del anfitrion:
# asi viaja con el compose y funciona igual en cualquier maquina, sin que
# nadie tenga que acordarse de configurar nada en el servidor.
#
# Tres decisiones que hacen que esto sirva de algo:
#
#  1. LA CONTRASENA NUNCA VA EN LA LINEA DE COMANDOS. Se pasa por PGPASSWORD,
#     porque los argumentos de un proceso se leen con `ps` desde cualquier
#     otra sesion del servidor.
#
#  2. CADA RESPALDO SE VERIFICA. Un pg_dump que falla a medias deja un
#     archivo que PARECE correcto: tiene tamano y se abre. Aqui se comprueba
#     que el gzip esta integro y que el volcado termina con la linea que
#     PostgreSQL escribe al acabar. Un respaldo que nadie verifico no es un
#     respaldo, es un archivo.
#
#  3. SI FALLA, GRITA Y NO BORRA NADA. La limpieza de antiguos solo corre
#     despues de un respaldo nuevo verificado. Asi un fallo repetido nunca
#     te deja sin ninguno.

set -eu

DESTINO="${RESPALDO_DESTINO:-/respaldos}"
RETENCION_DIAS="${RESPALDO_RETENCION_DIAS:-14}"
INTERVALO_HORAS="${RESPALDO_INTERVALO_HORAS:-24}"

# El tamano minimo que se considera plausible. Un volcado de NinjaSec vacio
# ronda los 30 KB comprimido; por debajo de 10 KB algo fue mal.
MINIMO_BYTES="${RESPALDO_MINIMO_BYTES:-10240}"

registro() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

fallo() {
    registro "ERROR: $*"
    return 1
}

verificar() {
    # Devuelve 0 solo si el archivo es un respaldo utilizable.
    #
    # La variable se llama _ruta y no `archivo` a proposito: POSIX sh no
    # tiene `local`, asi que una asignacion aqui dentro PISA la del
    # llamador. La primera version usaba `archivo` y por eso el `mv`
    # renombraba el archivo sobre si mismo: el .parcial nunca se quitaba y
    # el respaldo quedaba invisible para la limpieza. Lo caza la prueba de
    # abajo, no la lectura.
    _ruta="$1"

    [ -f "$_ruta" ] || { fallo "no se creo $_ruta"; return 1; }

    _tamano=$(wc -c < "$_ruta")
    if [ "$_tamano" -lt "$MINIMO_BYTES" ]; then
        fallo "$_ruta pesa $_tamano bytes, menos del minimo $MINIMO_BYTES"
        return 1
    fi

    if ! gzip -t "$_ruta" 2>/dev/null; then
        fallo "$_ruta esta corrupto: gzip no lo puede leer"
        return 1
    fi

    # pg_dump escribe esta linea al terminar. Si no esta, el volcado se
    # corto a mitad -- y ese es el caso que pasa desapercibido, porque el
    # archivo existe y pesa.
    if ! gzip -dc "$_ruta" | tail -5 | grep -q 'PostgreSQL database dump complete'; then
        fallo "$_ruta esta truncado: le falta la marca de cierre de pg_dump"
        return 1
    fi

    registro "verificado: $(basename "$_ruta") ($_tamano bytes)"
    return 0
}

respaldar() {
    marca=$(date '+%Y%m%d-%H%M%S')
    archivo="$DESTINO/ninjasec-$marca.sql.gz"
    parcial="$archivo.parcial"

    registro "respaldando $POSTGRES_DB desde $PGHOST..."

    # Se escribe con extension .parcial y se renombra al final. Si el
    # proceso muere a mitad, queda un .parcial que la verificacion ignora,
    # en vez de un .sql.gz roto que parece bueno.
    if ! PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
            --host="$PGHOST" \
            --username="$POSTGRES_USER" \
            --dbname="$POSTGRES_DB" \
            --no-owner --no-privileges --clean --if-exists \
            2>/tmp/pg_dump.err | gzip -9 > "$parcial"; then
        registro "ERROR: pg_dump fallo"
        sed 's/^/    /' /tmp/pg_dump.err || true
        rm -f "$parcial"
        return 1
    fi

    if ! verificar "$parcial"; then
        rm -f "$parcial"
        return 1
    fi

    mv "$parcial" "$archivo"
    registro "OK: $archivo"

    # La limpieza solo despues de un respaldo nuevo y verificado.
    borrados=$(find "$DESTINO" -name 'ninjasec-*.sql.gz' -type f \
                 -mtime "+$RETENCION_DIAS" -print -delete | wc -l)
    [ "$borrados" -gt 0 ] && registro "borrados $borrados respaldos de mas de $RETENCION_DIAS dias"

    total=$(find "$DESTINO" -name 'ninjasec-*.sql.gz' -type f | wc -l)
    registro "hay $total respaldos en $DESTINO"
    return 0
}

# ---------------------------------------------------------------------------

mkdir -p "$DESTINO"

registro "respaldos de NinjaSec en marcha"
registro "  destino:   $DESTINO"
registro "  retencion: $RETENCION_DIAS dias"
registro "  intervalo: $INTERVALO_HORAS horas"

# Una vez al arrancar: si el contenedor se reinicia, no esperas 24 horas al
# primer respaldo. Y si la configuracion esta mal, te enteras ahora.
if ! respaldar; then
    registro "el primer respaldo fallo. Revisa la configuracion."
fi

while true; do
    sleep $((INTERVALO_HORAS * 3600))
    respaldar || registro "respaldo fallido; se reintenta en $INTERVALO_HORAS horas"
done
