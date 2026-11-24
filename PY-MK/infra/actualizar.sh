#!/usr/bin/env bash
# Despliegue continuo: lo que entra en main, sube.
#
# Lo lanza un temporizador de systemd cada pocos minutos. Mira si `main`
# avanzo; si no, no hace nada y termina en un segundo.
#
# POR QUE TIRA Y NO LE EMPUJAN
#
# La alternativa es que GitHub Actions entre por SSH a la maquina. Eso exige
# guardar una clave privada en los secretos del repositorio y abrir SSH a
# los rangos de GitHub. Tirando desde aqui no hace falta ninguna de las dos
# cosas: la VM solo necesita salida a internet, y la clave de despliegue es
# de solo lectura.
#
# LO QUE LO HACE SEGURO
#
# Si la version nueva no levanta, VUELVE A LA ANTERIOR. Un despliegue
# continuo que deja el sitio caido es peor que no tenerlo: te enteras por un
# cliente, no por el log.

set -euo pipefail

DESTINO="${NINJASEC_DESTINO:-/opt/ninjasec}"
RAMA="${NINJASEC_RAMA:-main}"
COMPOSE="docker compose -p ninjasec -f docker-compose.prod.yml"
ESPERA_SEGUNDOS="${NINJASEC_ESPERA:-180}"

cd "$DESTINO"

registro() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ------------------------------------------------------- hay algo nuevo?

git fetch --quiet --prune origin "$RAMA"

ACTUAL=$(git rev-parse HEAD)
NUEVO=$(git rev-parse "origin/$RAMA")

if [ "$ACTUAL" = "$NUEVO" ]; then
    exit 0   # sin novedad; en silencio, que esto corre cada pocos minutos
fi

registro "main avanzo: ${ACTUAL:0:7} -> ${NUEVO:0:7}"
git --no-pager log --oneline "$ACTUAL..$NUEVO" | sed 's/^/    /'

# --------------------------------------------------- red de seguridad

# OJO: `/health` de Caddy lo responde el propio Caddy con "ok", sin mirar el
# backend. Por si solo no prueba nada: una version rota del backend o del
# frontend pasaria la prueba y no se revertiria. Por eso se mira el estado de
# salud de los dos contenedores, que si ejecutan su propio healthcheck.
salud() {
    local c
    for c in ninjasec-backend ninjasec-frontend; do
        [ "$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null)" = "healthy" ] || return 1
    done
    curl -fsS -o /dev/null --max-time 5 http://localhost/health 2>/dev/null
}

volver_atras() {
    registro "REVIRTIENDO a ${ACTUAL:0:7}"
    git reset --hard --quiet "$ACTUAL"
    cd "$DESTINO/PY-MK/infra"
    $COMPOSE up -d --build 2>&1 | sed 's/^/    /'
    for _ in $(seq 1 24); do
        salud && { registro "revertido y de vuelta en linea"; return 0; }
        sleep 5
    done
    registro "CRITICO: ni la version nueva ni la anterior levantan."
    registro "Hace falta mirarlo a mano:"
    registro "  cd $DESTINO/PY-MK/infra && $COMPOSE logs --tail 80"
    return 1
}

# ------------------------------------------------------------ desplegar

git merge --ff-only --quiet "origin/$RAMA" || {
    registro "ERROR: no se puede avanzar sin fusionar. Hay cambios locales en la VM."
    registro "Esta maquina no debe tener cambios propios: revisalo con git status."
    exit 1
}

cd "$DESTINO/PY-MK/infra"

# --build porque casi cualquier cambio toca una imagen. Compose reutiliza
# las capas que no cambiaron, asi que lo habitual son segundos, no minutos.
if ! $COMPOSE up -d --build 2>&1 | sed 's/^/    /'; then
    registro "la construccion fallo"
    volver_atras
    exit 1
fi

registro "esperando a que responda..."
intentos=$(( ESPERA_SEGUNDOS / 5 ))
for _ in $(seq 1 "$intentos"); do
    if salud; then
        registro "OK: desplegado ${NUEVO:0:7}"
        # Las imagenes viejas se acumulan y llenan el disco de 30 GB en
        # pocas semanas de despliegues.
        docker image prune -af --filter "until=168h" >/dev/null 2>&1 || true
        exit 0
    fi
    sleep 5
done

registro "no respondio en ${ESPERA_SEGUNDOS}s"
$COMPOSE logs --tail 40 2>&1 | sed 's/^/    /'
volver_atras
exit 1
