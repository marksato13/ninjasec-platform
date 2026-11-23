# PLAN-DEPLOY — Continuacion Fase 2.8 y 2.9

> Continuacion del plan principal de despliegue de NinjaSec.
> Estado: historico (2026-05-24). No usar para habilitar CD ni despliegues.
> Fuente de verdad vigente: `DOCUMENTOS/PLANIFICACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md` y `DOCUMENTOS/FLUJOS/DESPLIEGUE-PRODUCCION.md`.
> Esta version deja cerrada la estrategia elegida: **GitHub Actions + self-hosted runner en VLAN20**.
> Fecha: 2026-05-24

---

# FASE 2.8 — CI/CD con Self-Hosted Runner

## Decision ya tomada

Se usara **self-hosted runner dentro de la red** en vez de exponer SSH publico hacia la VM web.

### Motivo

- No exponer puerto SSH al exterior para GitHub Actions.
- El runner hace polling HTTPS saliente a GitHub.
- El deploy ocurre dentro de la red: `runner -> ninjasec-web`.

### Topologia resumida

```text
GitHub Actions
    |
    | HTTPS saliente (long polling)
    v
VM ninjasec-runner (192.168.10.6, VLAN20)
    |
    | SSH local dentro de VLAN20
    v
VM ninjasec-web (192.168.10.4, VLAN20)
```

---

## 2.8.2 Crear workflow `.github/workflows/deploy.yml`

El workflow correcto para esta estrategia **NO** debe usar `ubuntu-latest` con `DEPLOY_HOST` publico.
Debe correr en el runner interno.

### Workflow recomendado

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Ensure SSH known hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan 192.168.10.4 >> ~/.ssh/known_hosts

      - name: Deploy via local SSH to web VM
        run: |
          ssh -i ~/.ssh/web_deploy -o StrictHostKeyChecking=accept-new \
            ninjadeploy@192.168.10.4 <<'EOF'
            set -e
            cd /opt/ninjasec
            git fetch origin main
            git reset --hard origin/main
            cd infra
            docker compose -f docker-compose.prod.yml --env-file .env up -d --build
            docker exec ninjasec-backend bash -c "cd /app && PYTHONPATH=/app alembic upgrade head"
            docker image prune -f
            echo "Deploy completado"
          EOF

      - name: Smoke test
        run: |
          sleep 10
          curl -fsSL https://ninjasec.duckdns.org/health || exit 1
          echo "Health check OK"
```

---

## Secrets necesarios

Con self-hosted runner, la cantidad de secrets baja bastante.

### Ya no necesitas

- `DEPLOY_HOST` publico
- `DEPLOY_PORT` publico
- `DEPLOY_SSH_KEY` para un server expuesto a Internet

### Sigues necesitando segun el caso

- ninguno, si la key `~/.ssh/web_deploy` vive localmente en la VM runner
- opcionalmente, secrets de app si luego quieres expandir pipeline

### Recomendacion

Para esta primera version:
- dejar la key `web_deploy` solo en la VM runner
- no meter esa key en GitHub Secrets
- mantener el deploy totalmente interno

---

## 2.8.3 Probar el flujo

### Test manual simple

```bash
# En tu PC local, dentro del repo

echo "# Test deploy $(date)" >> README.md
git add README.md
git commit -m "test: trigger deploy"
git push origin main
```

### Verificar en GitHub

Ir a:

- `https://github.com/marksato13/PY_NINJASEC/actions`

Esperado:
- el job arranca sobre `self-hosted`
- hace checkout
- conecta por SSH a `192.168.10.4`
- ejecuta rebuild
- corre smoke test

### Resultado esperado

- `Checkout` OK
- `known_hosts` OK
- `Deploy via local SSH` OK
- `Smoke test` OK
- app accesible en `https://ninjasec.duckdns.org`

---

## 2.8.4 Validacion local del runner

En la VM runner puedes validar esto antes del primer push:

```bash
cd ~/actions-runner
sudo ./svc.sh status
```

Esperado:
- servicio activo
- runner visible como `Idle` en GitHub

Tambien probar SSH interno:

```bash
ssh -i ~/.ssh/web_deploy ninjadeploy@192.168.10.4 "hostname && docker ps"
```

Esperado:
- responde `ninjasec-web`
- lista contenedores

---

## 2.8.5 Snapshot post-CI/CD

Crear snapshot de las 3 VMs una vez validado el pipeline:

- `ninjasec-runner`
- `ninjasec-web`
- `ninjasec-db`

Nombre sugerido:
- `ci-cd-ready`

---

# FASE 2.9 — Hardening y monitoreo final

## 2.9.1 Cambiar passwords seed

Loguear en:
- `https://ninjasec.duckdns.org`

Credenciales iniciales:
- `admin@ninjasec.local`
- `change-me`

Luego:
1. Ir a `/dashboard/users`
2. Cambiar passwords de usuarios seed
3. Crear usuarios administrativos reales
4. Desactivar o eliminar cuentas demo si no las necesitas

---

## 2.9.2 Cerrar Swagger en produccion

Validar que el backend en produccion no exponga `/docs`.

### Verificacion

```bash
curl -I https://ninjasec.duckdns.org/docs
```

Esperado:
- `404`
- o ausencia de documentación pública

### Nota

Esto debe estar controlado por la configuración de producción, no solo por disciplina manual.

---

## 2.9.3 Instalar Netdata (monitoreo simple)

En ambas VMs principales:

- `ninjasec-web`
- `ninjasec-db`

```bash
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-wait
```

Acceso esperado:
- `https://192.168.10.4:19999`
- idealmente solo accesible desde `VLAN10`

---

## 2.9.4 Configurar log shipping a Suricata (opcional)

Si existe un IDS/collector en `VLAN30`:

```bash
sudo nano /etc/rsyslog.conf
# Agregar al final:
# *.* @@172.16.30.X:514

sudo systemctl restart rsyslog
```

Objetivo:
- centralizar logs de app/host hacia tu stack de seguridad

---

# Snapshots VMware ESXi automatizados

En `vSphere -> VM -> Schedule Tasks -> Create Snapshot`

| VM | Frecuencia | Retencion |
|---|---|---|
| `ninjasec-web` | Semanal (domingo 04:00) | 4 snapshots |
| `ninjasec-db` | Diario (04:00) | 7 snapshots |
| `ninjasec-runner` | Semanal | 2 snapshots |

> Monitorear consumo de datastore. Los snapshots no reemplazan backups de PostgreSQL.

---

# Troubleshooting comun

| Sintoma | Causa probable | Solucion |
|---|---|---|
| Caddy no obtiene cert Let's Encrypt | NAT 80/443 mal o DuckDNS no apunta bien | `dig ninjasec.duckdns.org`, revisar logs de Caddy |
| Backend no conecta a Postgres | `pg_hba.conf`, reglas pfSense, password `.env` | probar `psql` desde web VM |
| 502 Bad Gateway | backend/frontend caido | revisar `docker compose ps` y logs |
| Self-hosted runner no toma jobs | runner apagado o no registrado | revisar `svc.sh status` y GitHub runners |
| SSH runner -> web falla | key no instalada o `known_hosts` faltante | probar SSH manual desde la VM runner |
| Disco lleno | logs, imágenes Docker o snapshots | `df -h`, `docker system df`, revisar vSphere |

---

# Comandos utiles post-deploy

```bash
# Logs de la app
ssh ninjadeploy@192.168.10.4 "docker compose -f /opt/ninjasec/infra/docker-compose.prod.yml logs -f"

# Reiniciar backend
ssh ninjadeploy@192.168.10.4 "docker compose -f /opt/ninjasec/infra/docker-compose.prod.yml restart backend"

# Estado de contenedores
ssh ninjadeploy@192.168.10.4 "docker compose -f /opt/ninjasec/infra/docker-compose.prod.yml ps"

# Backup manual DB
ssh ninja@172.16.30.5 "sudo -u postgres pg_dump -Fc ninjasec > /tmp/manual_$(date +%Y%m%d_%H%M).dump"
```

---

# Checklist final pre-go-live

- [ ] VMs creadas con VLANs correctas en ESXi
- [ ] `ninjasec-db` operativa en VLAN30
- [ ] `ninjasec-web` operativa en VLAN20
- [ ] `ninjasec-runner` operativa en VLAN20
- [ ] PostgreSQL solo escucha en `172.16.30.5`
- [ ] `pg_hba.conf` restringido a `192.168.10.4/32`
- [ ] `ufw` activo en todas las VMs necesarias
- [ ] DuckDNS actualiza IP publica correctamente
- [ ] pfSense NAT 80/443 funcional
- [ ] Caddy obtuvo certificado valido
- [ ] `/docs` no expuesto en produccion
- [ ] Self-hosted runner aparece `Idle` en GitHub
- [ ] `push -> deploy` funciona correctamente
- [ ] Smoke test devuelve OK
- [ ] Backups diarios de PostgreSQL corriendo
- [ ] Snapshots ESXi configurados
- [ ] fail2ban activo
- [ ] passwords seed rotados

---

# Cierre

Cuando todo el checklist este en verde, puedes considerar NinjaSec listo para primer entorno productivo controlado.
