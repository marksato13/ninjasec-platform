# Staging multiproyecto — ESXi ahora, Oracle Cloud después

> Creado: 2026-09-27 · Documento de decisión + runbook. No requiere cambios de código.
> Continúa y **corrige** a [`../FLUJOS/DESPLIEGUE-PRODUCCION.md`](../FLUJOS/DESPLIEGUE-PRODUCCION.md) (issue #87).
> Reemplaza el dimensionamiento y la topología de [`../HISTORICO/PLAN-DEPLOY-2026-05-22.md`](../HISTORICO/PLAN-DEPLOY-2026-05-22.md) (ver §2.2).
> **Decisión 2026-09-27: red plana, sin VLANs.** Ver §3.0.

---

## 1. Qué se quiere

Un entorno **público** que aloje **más de un proyecto** (NinjaSec y al menos otro) y que
se actualice solo: `main` → producción, `develop` → staging, cada PR → entorno efímero.

Se hace en dos fases:

| Fase | Dónde | Cuándo | Sección |
|---|---|---|---|
| **A** | VM en el hipervisor ESXi del laboratorio | Ahora | §3 |
| **B** | VM en Oracle Cloud Free Tier | Más adelante | §4 |

Las secciones §5 (arquitectura multiproyecto) y §6 (bloqueantes) aplican a las dos.

---

## 2. Correcciones a la documentación existente

### 2.1 `FLUJOS/DESPLIEGUE-PRODUCCION.md` — el dato de Oracle está obsoleto

Dice que Always Free da **4 OCPU / 24 GB**. **Ya no.** El 15 de junio de 2026 Oracle lo
redujo a **2 OCPU / 12 GB** sin anuncio público — solo editó la documentación — y a partir
del 18 de agosto de 2026 terminó las instancias que excedían el nuevo límite.

El documento se escribió el 10 de agosto, casi dos meses después del recorte, con el dato
viejo. Consecuencia: **12 GB no sostienen dos proyectos con prod + staging + entornos por
PR + compilación**. En la fase B hay que recortar alcance; en la fase A no, porque el
hipervisor da más margen.

### 2.2 `HISTORICO/PLAN-DEPLOY-2026-05-22.md` — vigente en la topología, obsoleto en el resto

Ese plan (2026-05-22) describe una topología segmentada en VLANs con pfSense. **No se va a
usar para el staging**: se ha decidido montarlo sobre red plana (§3.0).

Lo que quedó viejo:

| Punto | En `PLAN-DEPLOY.md` | Ahora |
|---|---|---|
| Red | VLAN20 DMZ + VLAN30 DC con pfSense | **Red plana, sin VLANs** |
| VMs | Dos (`ninjasec-web` y `ninjasec-db`) | **Una sola** (§3.2) |
| Repositorio | `PY_NINJASEC` | `ninjasec-platform` |
| Ubuntu | 22.04 LTS | **24.04 LTS** |
| Alcance | Un solo proyecto | **Multiproyecto + entornos por PR** |
| DNS | DuckDNS | **Dominio en Cloudflare** (§3.5) |

`PLAN-DEPLOY.md` sigue siendo válido como referencia si algún día se retoma la
segmentación — ver §3.0.

---

## 3. FASE A — VM en el hipervisor ESXi

### 3.0 Decisión: red plana

El staging se monta sobre **una red plana, sin VLANs ni segmentación por pfSense**. Es una
decisión deliberada para reducir el trabajo de infraestructura y poder tener el entorno
funcionando antes.

**Consecuencia directa: una sola VM en vez de dos.** El plan de mayo separaba aplicación
y base de datos en VLAN20 DMZ y VLAN30 DC. Sin VLANs esa separación ya no aísla nada —
dos VMs en el mismo segmento se ven entre sí igual que dos contenedores— así que solo
añadiría una VM que mantener a cambio de nada.

**Qué se pierde, dicho claramente:**

- Si comprometen la aplicación, la base de datos está en el mismo segmento que el resto de
  la red, incluidos los equipos de administración
- Se renuncia a un argumento demostrable: una plataforma de consultoría de seguridad cuyo
  propio staging está segmentado es un buen ejemplo en una demo

**Mitigaciones que sí se aplican en red plana** (§3.5 y §3.6):

| Riesgo | Mitigación |
|---|---|
| PostgreSQL alcanzable desde la red | No publicar el puerto 5432 en el host: vive solo en la red interna de Docker |
| Servicios expuestos sin querer | `ufw` en la VM: solo 22 desde la red local, nada más de entrada |
| Superficie hacia Internet | Cloudflare Tunnel: conexión saliente, **cero puertos de entrada** |

> Si más adelante se retoma la segmentación, `HISTORICO/PLAN-DEPLOY-2026-05-22.md` conserva la topología
> completa de vSwitches, Port Groups y reglas de pfSense.

### 3.1 Punto de partida

Solo hace falta:

- Un **Port Group estándar** del vSwitch con salida a la red local (el que ya use el
  hipervisor para sus VMs normales) — sin VLAN ID
- Una **IP fija** para la VM dentro de esa red, o una reserva DHCP
- Acceso admin al hipervisor

### 3.2 Aprovisionamiento de la VM

Una sola VM, `staging`, que aloja todos los proyectos y todos los entornos.

| Parámetro | Valor | Por qué |
|---|---|---|
| Name | `staging` | Genérico: aloja varios proyectos |
| Guest OS | Ubuntu Linux (64-bit) | |
| **CPU** | **6 vCPU** | Los builds de Next.js son lo que más tarda |
| **Memoria** | **16 GB** · *Reserve all guest memory* ☑ | Ver desglose abajo |
| **Disco** | **200 GB · Thin Provision** | Imágenes Docker, caché de build y datos de PostgreSQL |
| Network Adapter | Port Group de la red local, **sin VLAN ID** | |
| IP | Fija o reserva DHCP, dentro de la red local | Anotarla: la necesitan el túnel y el runner |
| CD/DVD | `ubuntu-24.04-live-server-amd64.iso` | |

**Desglose de los 16 GB:**

| Consumidor | Aprox. |
|---|---|
| Ubuntu Server + Docker daemon | 1,5 GB |
| Caddy compartido | 0,05 GB |
| **PostgreSQL 16** (una instancia para todos los entornos) | ~2 GB |
| NinjaSec prod + staging (solo app) | ~1,2 GB |
| Segundo proyecto prod + staging | ~1,2 GB |
| 3 entornos efímeros de PR | ~1,8 GB |
| **Margen para compilar** (un build de Next.js pide ~2 GB) | ~6 GB |
| Reserva del sistema | resto |

Con 16 GB **sí caben los entornos por PR**, que es lo que la fase B no puede dar.

**Una sola instancia de PostgreSQL 16 sirve a todos los entornos**, con una base de datos
distinta por cada uno (`ninjasec_prod`, `ninjasec_staging`, `ninjasec_pr_123`,
`proyecto2_prod`…). Levantar un contenedor Postgres por entorno desperdiciaría memoria sin
ganar aislamiento real.

> ⚠️ **Verificar antes de crear nada:** que el host ESXi tenga capacidad libre para
> 16 GB de RAM reservada y 6 vCPU.
> `vSphere Client → Host → Summary → Resources`.
> Si no la hay, bajar a 12 GB y renunciar a los entornos por PR.

### 3.3 Sistema operativo

**Ubuntu Server 24.04 LTS (amd64)**, sin escritorio.

Razones: soporte hasta 2029, misma base que los `Dockerfile` del proyecto, y es la misma
versión que se usará en la fase B (salvo la arquitectura, ver §3.7).

Durante el instalador:
- Network: **Set IP manually** con la IP fija elegida en §3.2, o dejar DHCP si hay reserva
- DNS: `1.1.1.1, 8.8.8.8`
- **Marcar "Install OpenSSH server"** ☑
- Featured Server Snaps: **ninguno** — la versión snap de Docker da problemas con los volúmenes
- Particionado: usar todo el disco, LVM por defecto

### 3.4 Usuario y acceso

**Usuario: `deploy`.** Genérico a propósito: la VM aloja más de un proyecto, así que
`ninjasec` envejecería mal. (El plan anterior usaba `ninja`, válido igualmente; lo
importante es que **no sea `root`**.)

```bash
# 1. Sudo sin contrasena (es un laboratorio, no un banco)
echo "deploy ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/deploy
sudo chmod 440 /etc/sudoers.d/deploy

# 2. Autorizar la clave publica
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys      # pegar aqui la clave PUBLICA
chmod 600 ~/.ssh/authorized_keys

# 3. Cerrar el acceso por contrasena
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/'               /etc/ssh/sshd_config
sudo systemctl restart ssh

# 4. Endurecimiento minimo
sudo apt update && sudo apt upgrade -y
sudo apt install -y fail2ban unattended-upgrades ufw
sudo systemctl enable --now fail2ban

# 5. Cortafuegos: en red plana esto sustituye a lo que hacian las VLANs
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp   # ajustar a tu red local
sudo ufw --force enable
```

⚠️ **`ufw` y Docker no se llevan bien.** Docker escribe sus propias reglas en `iptables`
y **puentea `ufw`**: cualquier puerto publicado con `ports:` en Compose queda accesible
aunque `ufw` lo niegue. Por eso la regla de §5.1 importa más que el cortafuegos: **no
publicar el puerto de PostgreSQL**. Si un contenedor no publica puerto, no hay nada que
filtrar.

Generar el par de claves **en el equipo de administración**, nunca en la VM:

```powershell
ssh-keygen -t ed25519 -C "staging"
# Privada: C:\Users\<usuario>\.ssh\id_ed25519       <- NUNCA sale de ahi
# Publica: C:\Users\<usuario>\.ssh\id_ed25519.pub   <- esta es la que se pega arriba
```

### 3.5 Exposición pública — Cloudflare Tunnel en vez de DuckDNS

El plan anterior usaba **DuckDNS + redirección de puertos en el router**. Funciona para un
dominio, pero **no da certificados wildcard**, y sin wildcard no hay entornos
`pr-123.staging…`. Obtenerlo con DuckDNS obligaría a compilar Caddy con el plugin DNS.

**Recomendación: dominio propio gestionado por Cloudflare (~10 USD/año) + Cloudflare
Tunnel** (el túnel es gratis).

Un demonio dentro de la VM `staging` abre una conexión **saliente** hacia Cloudflare, y
Cloudflare publica los servicios con HTTPS. Ventajas sobre la redirección de puertos:

| | DuckDNS + port forward | Cloudflare Tunnel |
|---|---|---|
| Certificados wildcard | ❌ Requiere Caddy con plugin DNS | ✅ Nativo |
| Necesita IP pública | ✅ Sí | ❌ No |
| Funciona bajo CGNAT | ❌ No | ✅ Sí |
| Expone la IP de la red | ✅ Sí | ❌ No |
| Abre puertos en el router | ✅ 80 y 443 | ❌ Ninguno |
| Sirve igual en la fase B | Hay que rehacerlo | ✅ Solo cambia dónde corre |

Que **no haga falta abrir puertos de entrada** es especialmente relevante en red plana: sin
VLANs, un puerto abierto desde Internet llega a un segmento donde está todo lo demás. El
túnel evita esa exposición por completo — es la mitigación que más compensa la ausencia de
segmentación.

```bash
# En la VM staging, tras crear el tunel en el panel de Cloudflare
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
sudo cloudflared service install <TOKEN-DEL-TUNEL>
```

> Si se prefiere mantener DuckDNS: redirigir **solo 80 y 443** en el router hacia la IP de
> la VM. **Nunca** exponer el 22 (SSH) ni el 5432 (PostgreSQL) — y menos en red plana,
> donde detrás de esa IP está el resto de la red.

### 3.6 Docker

PostgreSQL entra como un contenedor más del stack compartido, no como servicio nativo:
así queda en la red interna de Docker sin publicar puerto (§5.1).

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
# cerrar sesion y volver a entrar para que el grupo tenga efecto
docker run --rm hello-world
docker version --format '{{.Server.Arch}}'   # debe decir: amd64
```

### 3.7 ⚠️ La trampa de la arquitectura

**Las VMs de ESXi son `amd64`. La VM de Oracle será `arm64`.** Las imágenes Docker
compiladas para una **no arrancan** en la otra.

- Las imágenes de la fase A no se reutilizan en la fase B: hay que recompilar
- Si se publican a un registro, deben ser multi-arquitectura
  (`docker buildx build --platform linux/amd64,linux/arm64`)
- `docker compose up --build` funciona en ambas sin cambios, porque compila en destino

No es un bloqueo, pero es la causa número uno de "en mi máquina funcionaba" al migrar.

### 3.8 Respaldo

El hipervisor añade una red de seguridad que la nube gratuita no da:

- **Snapshots de ESXi** antes de cada cambio grande de infraestructura
- `pg_dump` diario de cada base, con retención de 7 días
- Los snapshots **no sustituyen** al `pg_dump`: restaurar una VM entera para recuperar una
  tabla es desproporcionado, y un snapshot viejo de una VM con base de datos activa puede
  quedar inconsistente

### 3.9 Límites honestos de la fase A

| Límite | Detalle |
|---|---|
| Disponibilidad = la del laboratorio | Un corte de luz o de internet lo tumba |
| **Sin segmentación de red** | Decisión de §3.0. Un compromiso de la VM deja al atacante en el mismo segmento que el resto de la red, sin un salto más que dar |
| **Un solo punto de fallo** | Una VM aloja todos los proyectos y todos los entornos. Si se cae, se cae todo a la vez |
| Compilar y servir compiten | Un build puede degradar los entornos en marcha. Mitigable con `cpus` y `mem_limit` en Compose |
| Consumo eléctrico | El hipervisor encendido de forma permanente tiene un coste real, aunque no aparezca en ninguna factura de nube |
| Depende de IP fija o DNS dinámico | Resuelto por el túnel de Cloudflare |

---

## 4. FASE B — Oracle Cloud Free Tier

### 4.0 Qué es y qué cuesta

OCI mezcla dos productos bajo la misma marca:

| | Qué es | Duración |
|---|---|---|
| **Free Trial** | 300 USD en créditos | 30 días |
| **Always Free** | Subconjunto de recursos gratis | **Permanente** |

Lo relevante es **Always Free**. Límites vigentes, verificados en la documentación oficial:

| Recurso | Límite |
|---|---|
| Cómputo ARM (Ampere A1) | 1.500 OCPU-hora + 9.000 GB-hora/mes = **2 OCPU / 12 GB** a tiempo completo |
| Cómputo AMD | 2 instancias micro, 1/8 OCPU y 1 GB RAM |
| Disco | 200 GB en total (boot + block), 5 copias de seguridad |
| Object Storage | 20 GB, 50.000 peticiones/mes |
| Tráfico de salida | 10 TB/mes |
| Load balancer | 1, fijo a 10 Mbps |

**Es gratuito de verdad, con cuatro advertencias:**

1. **Pide tarjeta** de crédito o débito real (prepago y virtuales se rechazan). Es
   verificación, no cobro.
2. **Recortaron el free tier a la mitad** en junio de 2026, sin anuncio, y terminaron las
   instancias que excedían el nuevo límite en agosto de 2026.
3. 🔴 **Reclaman instancias ociosas.** Si durante 7 días el uso de CPU (percentil 95) está
   por debajo del 20%, el de red por debajo del 20% y el de memoria por debajo del 20%
   (este último criterio solo en shapes A1), Oracle **apaga la instancia**.
   **Un staging público que casi nadie visita es exactamente ese perfil.**
4. **"Out of host capacity"** — escasez crónica de ARM. La región de origen no se puede
   cambiar después.

La advertencia 3 condiciona el plan: hay que convertir la cuenta a **Pay As You Go**
(§4.3), que desactiva la reclamación y sigue sin cobrar dentro de los límites.

### 4.1 Paso 0 — Preparación (decide si aceptan la cuenta)

El registro rechaza cuentas por sistema antifraude. Aquí falla la mayoría.

| Factor | Qué hacer | Por qué |
|---|---|---|
| Tarjeta | Visa o Mastercard **de crédito real** | Prepago y virtuales se rechazan casi siempre |
| Red | **Sin VPN ni proxy** | Rechazo instantáneo |
| Si falla | Reintentar desde el **hotspot del móvil** | Las IP domésticas con CGNAT pueden estar en listas negras por abuso ajeno |
| Datos | Nombre = titular de la tarjeta, dirección = la del banco | Cualquier incoherencia sube el score de riesgo |
| Intentos | Acertar a la primera | Tras 2 fallos se entra en revisión manual, con casos reportados de más de 10 días |

### 4.2 Registro

En **https://signup.oraclecloud.com/**

1. Email personal (no temporal) y país → **el país no se puede cambiar después**
2. Verificar email, definir contraseña
3. Tipo de cuenta: **Individual**
4. 🔴 **Región principal — irreversible.** No se cambia nunca más.

   Ampere A1 está disponible en todas las regiones latinoamericanas, así que se elige por
   cercanía y congestión. Orden recomendado desde Perú:

   | Orden | Región | Distancia a Lima | Nota |
   |---|---|---|---|
   | 1 | **Colombia Central (Bogotá)** | ~1.900 km | Cercana y poco disputada |
   | 2 | Chile Central (Santiago) | ~2.460 km | Buena alternativa |
   | 3 | Brazil East (São Paulo) | ~3.470 km | Hub grande: más competencia por ARM |
   | ❌ | US East (Ashburn), Phoenix | — | Las más saturadas y peor latencia |

   Las cuentas gratuitas no están en todas las regiones; elegir de las que ofrezca el
   desplegable.

5. Tarjeta → **retención temporal** de verificación, no un cargo
6. Aceptar términos

⚠️ **No crear una segunda cuenta para cambiar de región.** El propio formulario lo avisa,
y es el patrón que dispara el antifraude: se pueden perder las dos.

### 4.3 🔴 Convertir a Pay As You Go

**Billing & Cost Management → Upgrade and Manage Payment**

Es lo que impide que Oracle apague el staging por inactividad (advertencia 3). Sigue sin
cobrar mientras no se excedan los límites Always Free.

**Riesgo que se asume:** en PAYG, excederse **sí se factura**. En Always Free puro
simplemente cortan el servicio. Por eso el paso siguiente no es opcional.

### 4.4 Presupuesto y alerta, antes de crear nada

**Billing → Budgets → Create Budget**

Presupuesto de **1 USD** con alerta al 100%. Si algo se sale de Always Free se detecta el
mismo día, no en la factura del mes.

### 4.5 Crear la VM

**Compute → Instances → Create Instance**

| Campo | Valor |
|---|---|
| Shape | **Ampere A1 Flex** → **2 OCPU / 12 GB** (el techo actual) |
| Imagen | **Ubuntu 24.04 LTS**, variante **aarch64 / ARM** — no x86 |
| Boot volume | 100-150 GB (tope 200 GB en total; dejar margen) |
| SSH | Generar el par **en el equipo local** y subir **solo la pública** |
| Usuario | Oracle crea `ubuntu`; añadir `deploy` como en §3.4 |

**Si aparece "Out of host capacity":** es habitual, no es un error propio. Probar otro
Availability Domain y reintentar. Si se alarga demasiado, un VPS de pago (~4-6 EUR/mes)
empieza a compensar.

**Diferencia de alcance frente a la fase A:** con 12 GB y una sola VM no caben
simultáneamente dos proyectos completos y los entornos por PR. Hay que elegir: o se
sacrifican los entornos efímeros, o el segundo proyecto se queda solo con staging.

### 4.6 Red — abrir 80 y 443 en dos capas

Tropiezo clásico: se abre la primera capa, no la segunda, y parece que está roto.

**a) En OCI:** Networking → VCN → Security List → Ingress Rules → TCP 80 y 443 desde `0.0.0.0/0`

**b) Dentro de la VM:** las imágenes Ubuntu de Oracle traen **iptables restrictivo
preconfigurado**:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

(Con Cloudflare Tunnel este paso se puede omitir: el túnel sale hacia fuera.)

### 4.7 Hardening y Docker

Idénticos a §3.4 y §3.6, con una diferencia: el instalador de Docker detecta `arm64` solo.
Verificar con `docker version --format '{{.Server.Arch}}'` que responde `arm64`.

---

## 5. Arquitectura multiproyecto (común a las dos fases)

### 5.1 Qué hay que cambiar en el stack actual

El `docker-compose.prod.yml` de NinjaSec asume que es el único inquilino del servidor.

| Hoy | Por qué no sirve | Cambio |
|---|---|---|
| Caddy vive **dentro** del stack y toma `80/443` | El segundo proyecto no arranca: puerto ocupado | Sacarlo a su propio compose en una red Docker externa compartida |
| `Caddyfile` es mono-sitio, `{$DOMAIN}` fijo → `backend:8024` | No sabe enrutar a N proyectos | Un fragmento por entorno, o `caddy-docker-proxy` leyendo labels |
| `container_name: ninjasec-backend` fijo | Dos instancias del mismo proyecto colisionan por nombre | Quitar `container_name`, usar `-p <proyecto>` de Compose |
| Postgres dentro del stack de cada proyecto | Duplicaría una instancia por entorno | Una instancia compartida, una base por entorno |
| Postgres con `ports: 5432` publicado | En red plana lo deja accesible desde toda la LAN, y Docker puentea `ufw` | **Quitar `ports:`.** Solo `expose:`, visible en la red interna de Docker |

### 5.2 Disposición

Todo vive en la VM `staging`. El aislamiento ya no lo dan las VLANs, lo dan **las redes
internas de Docker**: solo Caddy publica puertos al host.

```
VM staging (red local, sin VLANs)
│
│   Cloudflare Tunnel  <- conexion SALIENTE, ningun puerto de entrada
│          │
├── caddy-shared/          <- unico que publica :80 y :443
│   └── red "edge" ────────────────┐   (frontales de cada entorno)
│                                  │
├── ninjasec-prod    ninjasec.tudominio      <- main
├── ninjasec-staging staging.ninjasec...     <- develop
├── ninjasec-pr-123  pr-123.ninjasec...      <- efimero
└── otro-proyecto    otro.tudominio
                                   │
    red "data" ────────────────────┘   (interna, SIN puertos publicados)
        │
        └── postgres-shared  (PostgreSQL 16)
            ├── ninjasec_prod
            ├── ninjasec_staging
            ├── ninjasec_pr_123
            └── proyecto2_staging
```

**Dos redes Docker, no una:**

| Red | Quién la usa | Publica puertos |
|---|---|---|
| `edge` | Caddy + el frontal de cada entorno | Solo Caddy: 80 y 443 |
| `data` | Los backends + `postgres-shared` | **Ninguno** |

Así el frontend nunca alcanza la base de datos, y la base de datos no es visible desde la
red local. Es lo más parecido a la separación DMZ/DC que se puede conseguir sin VLANs —
con la diferencia honesta de que aquí un compromiso del host lo tumba todo, mientras que
con VLANs había un salto más que dar.

### 5.3 Actualización automática

El CI actual (`.github/workflows/ci.yml`) corre gitleaks, pytest y el build, pero **no
publica imágenes ni despliega nada**. Falta:

1. Un workflow que construya y publique a GHCR
2. Un workflow de despliegue que avise a la VM
3. La rama **`develop`, que todavía no existe** — solo hay `main` y `docs/estrategia-plataforma`

**Cómo llega el despliegue a la VM.** El plan anterior usaba SSH entrante desde GitHub
Actions, lo que obliga a exponer el puerto 22. Alternativa preferible con el túnel ya
montado: un **runner self-hosted** dentro de la VM `staging`, que consulta hacia fuera y no
necesita ningún puerto de entrada. Es además la única opción razonable en la fase B, donde
los runners ARM gratuitos de GitHub solo aplican a repositorios públicos y este es privado.

---

## 6. 🔴 Bloqueantes antes de exponer esto públicamente

| # | Bloqueante | Detalle |
|---|---|---|
| 1 | **Contraseñas del seed** | `SEED_ON_STARTUP=true` siembra `admin@ninjasec.local` / `change-me` como `super_admin`. En un staging público es una puerta de administrador con credenciales en texto plano en el repositorio. En staging **sí** se quieren datos demo, así que no basta con poner la variable en `false`: las contraseñas deben venir de una variable de entorno inyectada como secreto, distinta por entorno |
| 2 | **G-03 — secretos comprometidos** | Rotar `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` y el token DuckDNS. Pasa de "pendiente" a bloqueante en cuanto esto sea alcanzable desde Internet |
| 3 | **Sin backups automáticos** | `docker-compose.prod.yml` monta `./backups` pero no hay ningún job que escriba ahí. Es un punto de montaje, no una funcionalidad. Ver §3.8 |
| 4 | **Rate limiter en memoria** | Con `REDIS_URL` sin configurar es por proceso. Hoy corre un único proceso backend, así que no es problema; solo importa al escalar a réplicas |
| 5 | **PostgreSQL sin puerto publicado** | En red plana (§3.0) es la mitigación principal: `expose:` en vez de `ports:` en el Compose. Docker puentea `ufw`, así que un `ports: 5432` quedaría accesible desde toda la LAN aunque el cortafuegos lo niegue |

---

## 7. Decisiones pendientes

| Decisión | Bloquea | Recomendación |
|---|---|---|
| ¿Dominio propio en Cloudflare o seguir con DuckDNS? | Túnel, certificados wildcard, entornos por PR | **Dominio propio (~10 USD/año).** DuckDNS no da wildcard sin compilar Caddy con plugins DNS |
| ¿Cuál es el segundo proyecto y qué forma tiene? | Diseño de la red compartida y de §5.2 | Si no es también Compose + PostgreSQL, la sección §5 cambia |
| ¿Se crea la rama `develop`? | Flujo de 3 niveles | Necesaria para `main`→prod, `develop`→staging |
| ¿Runner self-hosted o SSH entrante? | Workflow de despliegue | **Self-hosted**: no expone el 22 y sirve igual en la fase B |
| ¿Capacidad libre en el host ESXi? | §3.2 | Verificar antes de crear la VM; si no llega, 12 GB y sin entornos por PR |
| ¿Se retoma la segmentación en VLANs más adelante? | §3.0 | Hoy no. `HISTORICO/PLAN-DEPLOY-2026-05-22.md` conserva la topología si se decide volver |

---

## 8. Estado verificado

Contra el código y el entorno, el **2026-09-27**:

- `create_all` ya **no** está en `app/main.py`; existe `app/db/migrate.py` y la migración
  base `20260807_00_esquema_base_completo.py`. **G-01 y G-02 están cerrados** — el
  "Estado conocido" de `AGENTS.md` está desactualizado en ese punto
- 21 migraciones encadenadas; la base de desarrollo corre en `20260810_01`
- 47 archivos de test en `backend/tests/`
- Ramas existentes: `main`, `docs/estrategia-plataforma`. **No hay `develop`**
- El entorno de desarrollo local (Docker Compose, puertos 3018/8024/5433) sigue operativo
  y es independiente de todo lo anterior

### Fuentes externas

- [Always Free Resources — documentación oficial de Oracle](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)
- [Oracle Quietly Halves Free Tier Ampere A1 Compute Limits — InfoQ](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/)
- [Reclamation of Idle Compute Instances — Oracle Cloud Customer Connect](https://community.oracle.com/customerconnect/discussion/671904/reclamation-of-idle-compute-instances)
- [Resolving Oracle Cloud "Out of Capacity" issue — GitHub](https://github.com/oeufmeister/oci-arm-host-capacity)
- [VM.Standard.A1.Flex — disponibilidad por región](https://northflank.com/cloud/oci/instances/VM.Standard.A1.Flex)
