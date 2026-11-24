# Desplegar en Google Cloud con los $300 de prueba

Guía para poner NinjaSec en línea **sin gastar nada durante 90 días**.
Verificada contra la documentación de Google el **2026-11-23**.

Cuenta a usar: una **personal**, no la institucional. Una cuenta de la
universidad suele tener la facturación bloqueada por el administrador de la
organización, y si dejas la UPeU te quedas sin el proyecto.

## Antes de registrarte: lee esto

> **El período de prueba no se puede pausar ni extender.**
> — documentación de Google Cloud

**Los 90 días empiezan en el segundo en que te registras, no cuando
despliegas.** Si te registras hoy y tardas una semana en estar listo, has
quemado una semana de las doce.

Regístrate el día que vayas a desplegar. Todo lo de este repositorio ya está
preparado para que eso sea una tarde.

## Lo que Google promete, y lo que no

**Lo que sí:**

> *No se te facturará durante la prueba gratuita. Cuando finalice, se
> detendrán todos los recursos y no se te cobrará, a menos que actives una
> cuenta pagada completa.*

La tarjeta sirve para verificar identidad. La transacción es de **entre
$0.00 y $1.00** y se revierte sola. **No es un cargo.**

**Lo que no:**

| | |
| --- | --- |
| **Sin garantía de servicio** | Google dice textualmente que *no recomienda ejecutar aplicaciones de producción* durante la prueba |
| **Al acabar, los datos se marcan para borrado** | 30 días de gracia y se pierden |
| **No puedes pedir aumentos de cuota** | |
| **Nada de GPU ni Windows Server** | Irrelevante aquí |

## El plan de salida se decide ahora

Lo que queda gratis después de los 90 días es **una `e2-micro`, solo en tres
regiones de EE. UU. y con 1 GB de salida al mes**. Eso no aguanta este sitio.

Así que esto te da **90 días para enseñar el producto y captar clientes**, no
para quedarte. Dos salidas:

1. **Oracle Always Free** — gratis de verdad y sin caducidad. Intenta el
   registro ahora, en paralelo: si entra, migras antes del día 80. Si te
   rechaza, no has perdido nada.
2. **Pagar** — Hetzner 4 GB, unos S/ 205 al año. Ver
   [`08-DECISION-HOSTING.md`](08-DECISION-HOSTING.md).

**Antes del día 85, saca los respaldos de la máquina.** Están dentro de ella
y desaparecen con ella.

---

## Paso 1 — Registrarte

1. Entra a <https://cloud.google.com/free> y pulsa **Comenzar gratis**.
2. Inicia sesión con tu **Gmail personal**.
3. Acepta los términos.
4. Rellena el perfil de pagos: tipo de cuenta **Individual**, nombre,
   dirección y tarjeta.

En cuanto termines, **el reloj de 90 días arranca**.

## Paso 2 — Crear la máquina

En la consola, menú **Compute Engine → Instancias de VM → Crear instancia**.

| Campo | Valor | Por qué |
| --- | --- | --- |
| **Nombre** | `ninjasec` | |
| **Región** | `us-east1` o `us-central1` | Más barato, y es donde está el nivel gratuito por si migras ahí después |
| **Tipo** | **`e2-medium`** (2 vCPU, 4 GB) | **No bajes de 4 GB.** Con 2 GB el build de Next.js muere por falta de memoria, y el error solo dice `killed` |
| **Disco de arranque** | Ubuntu 24.04 LTS, **30 GB** | |
| **Cortafuegos** | marca **HTTP** y **HTTPS** | |

Con una `e2-medium` encendida todo el mes gastas del orden de $25-30. Con
$300 te sobra para los tres meses y te queda crédito.

> **Crea una alerta de presupuesto.** Facturación → Presupuestos y alertas,
> con avisos al 50% y al 90%. Es lo que te da tiempo a reaccionar antes de
> quedarte sin crédito de golpe.

## Paso 3 — Entrar a la máquina

Desde la lista de instancias, botón **SSH**. Abre una terminal en el
navegador: no hace falta configurar claves.

## Paso 4 — Instalar

```bash
# en la VM
sudo apt-get update && sudo apt-get install -y git
curl -fsSL https://raw.githubusercontent.com/marksato13/ninjasec-platform/main/PY-MK/infra/instalar-en-vm.sh -o instalar.sh
less instalar.sh      # leelo antes de ejecutarlo
sudo bash instalar.sh
```

El script comprueba la máquina, instala Docker, **genera los secretos**
—así la rotación de G-03 ocurre por construcción—, cierra el cortafuegos y
levanta el stack.

Te va a pedir dos cosas y a parar una vez:

1. **El dominio o la IP** de la VM.
2. **Un correo** para el certificado de Let's Encrypt.
3. **Que autorices una clave de despliegue en GitHub.** El repositorio es
   privado: el script genera una clave y te la muestra para que la pegues en
   `Settings → Deploy keys`. **No marques «Allow write access»**: esa máquina
   está expuesta a internet y solo necesita leer.

## Paso 5 — El dominio

Sin dominio propio, Caddy no puede emitir certificado y entras por `http://IP`
sin HTTPS. Para un enlace que mandar a un cliente, eso no vale.

Un `.com` cuesta unos S/ 40 al año en Namecheap o Porkbun. Es el único gasto
real de todo esto, y es el que convierte una IP en una marca.

Apunta un registro **A** del dominio a la IP externa de la VM, espera unos
minutos y reinicia Caddy:

```bash
cd /opt/ninjasec/PY-MK/infra
sudo docker compose -p ninjasec -f docker-compose.prod.yml restart caddy
```

## Paso 6 — Comprobar

```bash
sudo docker compose -p ninjasec -f docker-compose.prod.yml ps
curl -s https://TUDOMINIO/health
curl -s https://TUDOMINIO/api/v1/capsulas
sudo docker logs ninjasec-respaldos --tail 20
```

El último es el que más se olvida: comprueba que **el primer respaldo se
hizo y se verificó**.

Para entrar: `admin@ninjasec.local`. La clave la generó el instalador y está
en el `.env`:

```bash
sudo grep SEED_PASSWORD /opt/ninjasec/PY-MK/infra/.env
```

**Cámbiala desde la aplicación en cuanto entres.**

## Paso 7 — Antes de mandarle el enlace a nadie

- [ ] `https://` funciona y el candado es válido
- [ ] Entraste y **cambiaste la clave de `admin`**
- [ ] `/api/v1/capsulas` dice que `telemetria` está **apagada** — si no, estarías enseñando conectores simulados como si fueran reales
- [ ] `docker logs ninjasec-respaldos` muestra un respaldo verificado
- [ ] `https://TUDOMINIO/docs` **no** responde: Swagger se cierra en producción

---

## Cuando se acabe

A los 90 días, o cuando se agote el crédito:

1. **Saca los respaldos** antes del día 85.
2. Google **para** los recursos. No te cobra.
3. Tienes **30 días de gracia** para recuperarlos activando una cuenta de
   pago. Después se pierden.

No hace falta cancelar nada: si no activas una cuenta de pago, la cuenta de
facturación se suspende sola y no se genera ningún cargo.

Ver también: [`08-DECISION-HOSTING.md`](08-DECISION-HOSTING.md) ·
[`09-STAGING-MULTIPROYECTO.md`](09-STAGING-MULTIPROYECTO.md) ·
[`../../PY-MK/infra/respaldos/README.md`](../../PY-MK/infra/respaldos/README.md)
