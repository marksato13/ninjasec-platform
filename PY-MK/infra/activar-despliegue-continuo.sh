#!/usr/bin/env bash
# Activa el despliegue continuo en una VM que ya tiene NinjaSec funcionando.
#
# Para cuando el codigo llego a la maquina de otra forma (un tar.gz subido a
# mano) y ahora quieres que lo que entre en `main` se despliegue solo.
#
#   sudo bash activar-despliegue-continuo.sh
#
# Es repetible: si ya esta activo, no rompe nada.
#
# Que hace, en orden:
#   1. Prepara una clave de despliegue de SOLO LECTURA y comprueba que GitHub
#      la acepta. Si no, te la muestra y se detiene: autorizarla es cosa tuya.
#   2. Si /opt/ninjasec no es un clon git, lo sustituye por uno, conservando
#      el .env y los respaldos. El anterior se guarda, no se borra.
#   3. Recrea los contenedores para que usen los archivos del clon.
#   4. Instala y enciende el temporizador de systemd.
#
# Lo que NO toca: la base de datos ni los volumenes. Los datos viven en
# volumenes de Docker con nombre, y la carpeta es solo codigo y configuracion.

set -euo pipefail

REPO="${NINJASEC_REPO:-git@github.com:marksato13/ninjasec-platform.git}"
DESTINO="${NINJASEC_DESTINO:-/opt/ninjasec}"
RAMA="${NINJASEC_RAMA:-main}"
CLAVE="/root/.ssh/ninjasec_deploy"

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta con sudo."; exit 1; }

echo "== 1. clave de despliegue (solo lectura)"
mkdir -p /root/.ssh && chmod 700 /root/.ssh
if [ ! -f "$CLAVE" ]; then
    ssh-keygen -t ed25519 -N "" -C "ninjasec-vm-despliegue" -f "$CLAVE" >/dev/null
fi
grep -q "ninjasec_deploy" /root/.ssh/config 2>/dev/null || cat >> /root/.ssh/config <<EOF
Host github.com
  IdentityFile $CLAVE
  IdentitiesOnly yes
EOF
chmod 600 /root/.ssh/config
ssh-keygen -F github.com >/dev/null 2>&1 || ssh-keyscan -t ed25519 github.com >> /root/.ssh/known_hosts 2>/dev/null

if ! ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo
    echo "GitHub todavia no acepta la clave. Autorizala como clave de despliegue"
    echo "SIN permiso de escritura (Settings > Deploy keys):"
    echo
    cat "$CLAVE.pub"
    echo
    exit 2
fi
echo "   GitHub acepta la clave."

echo "== 2. clon de $RAMA en $DESTINO"
if [ -d "$DESTINO/.git" ]; then
    echo "   ya es un clon git; no se toca."
else
    NUEVO="$DESTINO.nuevo"
    rm -rf "$NUEVO"
    git clone --branch "$RAMA" --depth 1 "$REPO" "$NUEVO"
    [ -f "$DESTINO/PY-MK/infra/.env" ] || { echo "No encuentro $DESTINO/PY-MK/infra/.env"; exit 1; }
    cp -p "$DESTINO/PY-MK/infra/.env" "$NUEVO/PY-MK/infra/.env"
    mkdir -p "$NUEVO/PY-MK/infra/backups"
    if [ -d "$DESTINO/PY-MK/infra/backups" ]; then
        cp -a "$DESTINO/PY-MK/infra/backups/." "$NUEVO/PY-MK/infra/backups/"
    fi
    ANTERIOR="$DESTINO.anterior-$(date +%Y%m%d%H%M%S)"
    mv "$DESTINO" "$ANTERIOR"
    mv "$NUEVO" "$DESTINO"
    echo "   el anterior queda en $ANTERIOR (borralo cuando todo funcione)."
fi

echo "== 3. recrear contenedores sobre el clon"
cd "$DESTINO/PY-MK/infra"
docker compose -p ninjasec -f docker-compose.prod.yml up -d --build --force-recreate

echo -n "   esperando"
for _ in $(seq 1 60); do
    if curl -fsS -o /dev/null --max-time 3 http://localhost/health 2>/dev/null \
       || curl -fsSk -o /dev/null --max-time 3 https://localhost/health 2>/dev/null; then
        echo " ok"; break
    fi
    echo -n "."; sleep 5
done

echo "== 4. temporizador"
chmod +x "$DESTINO/PY-MK/infra/actualizar.sh"
install -m 0644 "$DESTINO/PY-MK/infra/ninjasec-actualizar.service" /etc/systemd/system/
install -m 0644 "$DESTINO/PY-MK/infra/ninjasec-actualizar.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ninjasec-actualizar.timer
systemctl list-timers ninjasec-actualizar.timer --no-pager | head -n 3

echo
echo "Listo. Lo que entre en $RAMA se despliega solo en unos 5 minutos."
echo "Ver lo que hizo:   journalctl -u ninjasec-actualizar -n 40 --no-pager"
