#!/usr/bin/env bash
# NinjaSec — instalacion en una VM limpia de Ubuntu.
#
# Pensado para una maquina recien creada en Google Cloud, Oracle o cualquier
# VPS con Ubuntu 22.04 o 24.04. Se ejecuta UNA vez.
#
#   curl -fsSL https://raw.githubusercontent.com/.../instalar-en-vm.sh -o instalar.sh
#   less instalar.sh          # leelo antes de ejecutarlo, siempre
#   sudo bash instalar.sh
#
# Que hace, en orden:
#   1. Comprueba que la maquina da la talla (RAM, disco, version)
#   2. Instala Docker y el plugin de compose
#   3. Prepara una clave de despliegue de SOLO LECTURA para clonar el repo
#   4. GENERA LOS SECRETOS, no te los pide
#   5. Cierra el cortafuegos a todo menos SSH, 80 y 443
#   6. Levanta el stack y espera a que responda de verdad
#
# Lo que NO hace, a proposito:
#   - No crea cuentas ni toca tu facturacion.
#   - No siembra datos: en produccion la siembra se niega a correr sin
#     SEED_PASSWORD, y eso lo decides tu.
#   - No abre el puerto de PostgreSQL. Nunca.

set -euo pipefail

REPO="${NINJASEC_REPO:-git@github.com:marksato13/ninjasec-platform.git}"
DESTINO="${NINJASEC_DESTINO:-/opt/ninjasec}"
RAMA="${NINJASEC_RAMA:-main}"

# --------------------------------------------------------------------------

rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }
verde() { printf '\033[32m%s\033[0m\n' "$*"; }
gris()  { printf '\033[90m%s\033[0m\n' "$*"; }
titulo() { printf '\n\033[36m== %s\033[0m\n' "$*"; }

abortar() { rojo "ERROR: $*"; exit 1; }

[ "$(id -u)" -eq 0 ] || abortar "Ejecuta con sudo."

# --------------------------------------------------------- 1. la maquina

titulo "Comprobando la maquina"

if ! grep -qiE 'ubuntu|debian' /etc/os-release 2>/dev/null; then
    rojo "Esto esta probado en Ubuntu/Debian. En otra distribucion puede fallar."
    read -rp "  Seguir igualmente? (s/n) " r
    [ "$r" = "s" ] || exit 1
fi

ram_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
disco_gb=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')

echo "  RAM:   ${ram_mb} MB"
echo "  Disco: ${disco_gb} GB libres"

# El stack mide ~1,5 GB con los tres contenedores. Por debajo de 2 GB el
# build de Next.js muere por falta de memoria, y el error que da -"killed"
# a secas- no dice que fue eso.
if [ "$ram_mb" -lt 1900 ]; then
    rojo "Menos de 2 GB de RAM. El build de Next.js va a morir por OOM,"
    rojo "y el error que veras es solo 'killed', sin explicar la causa."
    gris "Usa una e2-medium (4 GB) o anade swap antes de seguir."
    exit 1
fi
[ "$disco_gb" -lt 15 ] && abortar "Hacen falta al menos 15 GB libres; hay ${disco_gb}."
verde "  La maquina da la talla."

# ------------------------------------------------------------- 2. docker

titulo "Docker"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    verde "  Ya estaba instalado: $(docker --version)"
else
    gris "  Instalando desde el repositorio oficial de Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg git ufw >/dev/null

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin >/dev/null

    systemctl enable --now docker
    verde "  Instalado: $(docker --version)"
fi

# ------------------------------------------------------ 3. clave y clonado

titulo "Codigo"

if [ -d "$DESTINO/.git" ]; then
    verde "  Ya existe $DESTINO; actualizando."
    git -C "$DESTINO" fetch --prune origin
    git -C "$DESTINO" checkout "$RAMA"
    git -C "$DESTINO" pull --ff-only origin "$RAMA"
else
    # El repositorio es privado. Hace falta una clave de despliegue de SOLO
    # LECTURA -- no tus credenciales personales, que darian acceso de
    # escritura a todo lo tuyo desde una maquina expuesta a internet.
    clave="/root/.ssh/ninjasec_deploy"
    if [ ! -f "$clave" ]; then
        mkdir -p /root/.ssh && chmod 700 /root/.ssh
        ssh-keygen -t ed25519 -N "" -C "ninjasec-vm" -f "$clave" >/dev/null
        ssh-keyscan -t ed25519 github.com >> /root/.ssh/known_hosts 2>/dev/null
        cat >> /root/.ssh/config <<EOF
Host github.com
  IdentityFile $clave
  IdentitiesOnly yes
EOF
        chmod 600 /root/.ssh/config
    fi

    if ! ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        rojo "  La clave de despliegue todavia no esta autorizada en GitHub."
        echo
        echo "  Copia esta clave publica:"
        echo
        printf '\033[33m%s\033[0m\n' "$(cat "$clave.pub")"
        echo
        echo "  Y pegala en:"
        echo "    https://github.com/marksato13/ninjasec-platform/settings/keys/new"
        echo
        gris "  Titulo: 'VM de produccion'. NO marques 'Allow write access'."
        gris "  Esta maquina solo necesita leer."
        echo
        read -rp "  Pulsa Enter cuando la hayas anadido... " _
        ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated" \
            || abortar "GitHub sigue rechazando la clave. Revisa que la pegaste entera."
    fi

    verde "  Clave autorizada. Clonando..."
    git clone --branch "$RAMA" --depth 1 "$REPO" "$DESTINO"
fi

# ------------------------------------------------------------ 4. secretos

titulo "Configuracion"

ENV="$DESTINO/PY-MK/infra/.env"

if [ -f "$ENV" ]; then
    verde "  Ya existe $ENV; no se toca."
    gris "  Si quieres regenerar los secretos, borralo y vuelve a ejecutar."
else
    read -rp "  Dominio (ej. ninjasec.com, o la IP de la VM): " DOMINIO
    [ -n "$DOMINIO" ] || abortar "Hace falta un dominio o una IP."
    read -rp "  Correo para el certificado Let's Encrypt: " CORREO
    [ -n "$CORREO" ] || abortar "Let's Encrypt necesita un correo."

    # Los secretos SE GENERAN, no se piden. Dos motivos: una contrasena
    # escrita a mano es peor que 32 bytes aleatorios, y asi la rotacion de
    # los secretos viejos ocurre por construccion en cada instalacion nueva.
    echo
    echo "  Sin sembrar, la base arranca VACIA: no hay usuarios y no se puede"
    echo "  entrar. La siembra crea la organizacion, los roles y las cuentas"
    echo "  de ejemplo, todas con una misma clave que se genera aqui."
    echo
    gris "  Si dices que no, tendras que crear el primer usuario a mano."
    read -rp "  Sembrar datos iniciales? (s/n) " SEMBRAR

    gris "  Generando secretos..."
    JWT=$(openssl rand -hex 32)
    PG=$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)
    if [ "$SEMBRAR" = "s" ]; then
        SEED_PWD=$(openssl rand -base64 18 | tr -d '/+=' | head -c 20)
    else
        SEED_PWD=""
    fi

    umask 077
    cat > "$ENV" <<EOF
# Generado por instalar-en-vm.sh el $(date '+%Y-%m-%d %H:%M:%S')
#
# ESTE ARCHIVO NO SE VERSIONA NI SE COPIA A NINGUN SITIO.
# Los secretos se generaron aqui y no existen en ninguna otra maquina.

DOMAIN=$DOMINIO
ACME_EMAIL=$CORREO

POSTGRES_DB=ninjasec
POSTGRES_USER=ninjasec
POSTGRES_PASSWORD=$PG
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

JWT_SECRET_KEY=$JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

APP_NAME=Ninja Tech
APP_VERSION=0.2.0
API_PREFIX=/api/v1
CORS_ORIGINS=https://$DOMINIO
NEXT_PUBLIC_API_URL=/api/v1

# Sin esta variable la siembra se NIEGA a correr en produccion, y sin
# siembra NO HAY NINGUN USUARIO y no se puede entrar.
SEED_PASSWORD=$SEED_PWD

# Capsulas encendidas. Vacio = ninguna. "telemetria" esta apagada porque
# los conectores son simulados.
CAPSULAS_ACTIVAS=

RESPALDO_RETENCION_DIAS=14
RESPALDO_INTERVALO_HORAS=24
EOF
    chmod 600 "$ENV"
    verde "  Secretos generados. Ni se muestran ni salen de esta maquina."
fi

mkdir -p "$DESTINO/PY-MK/infra/backups"

# --------------------------------------------------------- 5. cortafuegos

titulo "Cortafuegos"

if command -v ufw >/dev/null 2>&1; then
    ufw --force reset >/dev/null 2>&1 || true
    ufw default deny incoming >/dev/null
    ufw default allow outgoing >/dev/null
    ufw allow 22/tcp  >/dev/null  # SSH primero, o te quedas fuera
    ufw allow 80/tcp  >/dev/null  # Let's Encrypt lo necesita para validar
    ufw allow 443/tcp >/dev/null
    ufw --force enable >/dev/null
    verde "  Abierto: 22, 80 y 443. Todo lo demas, cerrado."
    gris "  PostgreSQL (5432) NO se expone: el compose lo ata a 127.0.0.1."
else
    rojo "  ufw no esta disponible. Configura el cortafuegos del proveedor a mano."
fi

# ------------------------------------------------------------ 6. levantar

titulo "Levantando"

cd "$DESTINO/PY-MK/infra"
docker compose -p ninjasec -f docker-compose.prod.yml up -d --build

echo -n "  Esperando a que responda"
listo=0
for _ in $(seq 1 60); do
    if curl -fsS -o /dev/null --max-time 3 http://localhost/health 2>/dev/null; then
        listo=1; break
    fi
    echo -n "."
    sleep 5
done
echo

if [ "$listo" -eq 1 ]; then
    verde "  Arriba."
else
    rojo "  No respondio en 5 minutos."
    gris "  docker compose -p ninjasec -f docker-compose.prod.yml logs --tail 50"
    exit 1
fi

# ------------------------------------------------- 7. despliegue continuo

titulo "Despliegue continuo"

if [ -f "$DESTINO/PY-MK/infra/ninjasec-actualizar.timer" ]; then
    chmod +x "$DESTINO/PY-MK/infra/actualizar.sh"
    cp "$DESTINO/PY-MK/infra/ninjasec-actualizar.service" /etc/systemd/system/
    cp "$DESTINO/PY-MK/infra/ninjasec-actualizar.timer"   /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now ninjasec-actualizar.timer
    verde "  Activado: comprueba main cada 5 minutos."
    gris "  Tira desde aqui en vez de que GitHub empuje: asi no hace falta"
    gris "  guardar una clave privada en los secretos del repositorio."
    gris "  Si la version nueva no levanta, VUELVE a la anterior sola."
else
    rojo "  No encuentro las unidades de systemd; sin despliegue continuo."
fi

# ---------------------------------------------------------------- resumen

titulo "Listo"
echo
echo "  https://$(grep '^DOMAIN=' "$ENV" | cut -d= -f2)"
echo
gris "  El certificado de Let's Encrypt tarda hasta un minuto la primera vez."
gris "  Si el dominio aun no apunta a esta IP, fallara: arregla el DNS y"
gris "  reinicia caddy con 'docker compose -p ninjasec restart caddy'."
echo
echo "  Despliegue continuo:"
gris "    systemctl list-timers ninjasec-actualizar.timer"
gris "    journalctl -u ninjasec-actualizar.service -n 50"
gris "    systemctl start ninjasec-actualizar.service   # forzar ahora"
echo
echo "  Comandos utiles, desde $DESTINO/PY-MK/infra :"
gris "    docker compose -p ninjasec -f docker-compose.prod.yml ps"
gris "    docker compose -p ninjasec -f docker-compose.prod.yml logs -f backend"
gris "    docker logs ninjasec-respaldos --tail 20"
echo
if grep -q '^SEED_PASSWORD=.\+' "$ENV"; then
    echo "  Para entrar: admin@ninjasec.local"
    gris "  La clave esta en $ENV, en SEED_PASSWORD. No se imprime aqui"
    gris "  para que no quede en el historial de la terminal ni en los logs."
    gris "  Leela con:  sudo grep SEED_PASSWORD $ENV"
    echo
    rojo "  CAMBIALA desde la aplicacion en cuanto entres."
else
    rojo "  NO HAY NINGUN USUARIO: dijiste que no a la siembra."
    gris "  Tendras que crear el primero a mano antes de poder entrar."
fi
echo
rojo "  PENDIENTE Y ES TUYO:"
echo "    - Los respaldos estan en esta misma maquina. Si muere, se van con"
echo "      ella. Sacalos fuera: ver PY-MK/infra/respaldos/README.md"
echo
