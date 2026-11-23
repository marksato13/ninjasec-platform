# Decisión de hosting — dónde se despliega NinjaSec

> Creado: 2026-11-22 · **Documento de decisión, para retomar en otra sesión.**
> Complementa a [`DESPLIEGUE-PRODUCCION.md`](DESPLIEGUE-PRODUCCION.md), que
> tiene el runbook, y corrige sus cifras de Oracle (ver §6).

---

## 0. Resumen en diez líneas

El objetivo es tener **tres sistemas públicos**: NinjaSec, un sistema demo y
un portafolio. Pagando poco o nada.

**La recomendación: arquitectura híbrida.** Lo estático se va a Cloudflare
Pages, que es gratis de verdad y sin trampas. Solo NinjaSec necesita
servidor, y con eso basta un VPS de 4 GB.

| | Coste |
|---|---|
| Cloudflare Pages (portafolio + demos estáticas) | **S/ 0** |
| Hetzner 4 GB (NinjaSec) | ~S/ 17/mes |
| Dominio | ~S/ 45/año |
| **Total** | **~S/ 250/año** · unos S/ 21/mes |

La alternativa de coste cero es Oracle Cloud Always Free, con cuatro
asteriscos que están en §6.

---

## 1. Cuánto consume de verdad cada sistema

Medido sobre lo que corre hoy en desarrollo, no estimado a ojo.

| Componente | En reposo | Con 10 usuarios |
|---|---|---|
| PostgreSQL 16 | ~200 MB | ~400 MB |
| FastAPI (uvicorn, 1 worker) | ~200 MB | ~250 MB |
| Next.js 16 en producción | ~250 MB | ~300 MB |
| Caddy | ~50 MB | ~50 MB |
| **NinjaSec completo** | **~700 MB** | **~1 GB** |
| Ubuntu 24.04 + Docker | ~500 MB | ~500 MB |

**Diez usuarios casi no se notan.** Lo que consume es tener los procesos
levantados, no las visitas: 10 usuarios registrados son 2 o 3 conexiones
concurrentes en el peor momento del día.

### El pico real es compilar

Un `npm run build` de Next.js pide **más de 2 GB él solo**. Eso, y no el
tráfico, es lo que decide el tamaño del servidor:

| RAM del VPS | Sirve si… |
|---|---|
| **4 GB** | Las imágenes se construyen en GitHub Actions y la VM solo las descarga |
| **8 GB** | Se puede compilar en la propia VM sin pensarlo |

### Disco y tráfico

- **Disco:** imágenes Docker (~1,5 GB por sistema), datos de Postgres y caché
  de build ⇒ **40-50 GB**. Con 80 GB sobra.
- **Tráfico de salida:** un sitio con pocas visitas no pasa de **50 GB/mes**.
  Todos los proveedores dan mucho más.

---

## 2. La arquitectura recomendada

```
Cloudflare Pages  (S/ 0)          VPS 4 GB  (~S/ 17/mes)
├── Portafolio                    ├── Caddy  (único que publica 80/443)
└── Demo estática                 └── NinjaSec
                                      ├── PostgreSQL
                                      ├── FastAPI
                                      └── Next.js
```

**Por qué partirlo así:** un hosting estático sirve archivos; no ejecuta
procesos ni guarda bases de datos. NinjaSec necesita tres cosas que ninguno
da — un proceso vivo permanentemente, PostgreSQL con datos que persisten, y
un WebSocket sostenido (`/api/v1/alerts/ws`). Lo demás no las necesita, así
que no tiene por qué pagar servidor.

**El ahorro:** sacar lo estático baja el consumo del VPS de ~2,5 GB a ~1,5 GB,
y con eso basta el plan de 4 GB en vez del de 8. **Casi la mitad de precio.**

---

## 3. Opciones gratuitas, con sus trampas

| Opción | ¿Repo privado? | ¿Uso comercial? | Veredicto |
|---|---|---|---|
| **Cloudflare Pages** | ✅ | ✅ | **La buena.** Ancho de banda sin límite práctico, HTTPS y dominio propio |
| GitHub Pages | ❌ **Solo público** en el plan gratuito | ✅ | Sirve si no te importa publicar el código |
| Netlify Free | ✅ | ✅ | Alternativa válida, 100 GB/mes |
| Vercel Hobby | ✅ | ❌ **Prohibido** | **Descartado** |

### Las dos trampas que importan

**GitHub Pages desde repositorio privado exige plan de pago.** En el plan
gratuito el repo tiene que ser público. Y aunque se pague Pro, **el sitio
publicado sigue siendo público**: lo privado es el código, no la web.

**El plan Hobby de Vercel prohíbe el uso comercial**, con una definición
amplia: cualquier despliegue del que alguien que participó en construirlo
obtenga beneficio económico. Un consultor que cobra por hacerlo ya lo
convierte en comercial. **NinjaSec entra de lleno.**

---

## 4. Opciones de pago, con precios

Verificados en noviembre de 2026. **Cambian a menudo: confirmar en la página
del proveedor antes de contratar.**

Supuesto de conversión: **1 € = S/ 3,80 · 1 US$ = S/ 3,45**. No se pudo
verificar con fuente fiable (la única cotización encontrada venía marcada
como de hace 188 días). Comprobar en la [SBS](https://www.sbs.gob.pe/) o el
BCRP.

| Proveedor | Plan | Mensual | Anual |
|---|---|---:|---:|
| **Hetzner** CX22 | 4 GB / 2 vCPU / 40 GB | ~€4,50 · **S/ 17** | **S/ 205** |
| **Hetzner** CX33 | 8 GB / 4 vCPU / 80 GB | €8,49 · S/ 32 | S/ 387 |
| **Contabo** | 8 GB / 4 vCPU / 100 GB | €5,50 · S/ 21 | S/ 251 |
| Contabo (24 meses prepago) | mismo | €4,40 · S/ 17 | S/ 401 los dos años |
| **Vultr** | 8 GB / 4 vCPU | US$ 40 · S/ 138 | S/ 1.656 |

### Si el tipo de cambio es otro

Regla rápida: **Hetzner CX22 son ~4,5 € al mes.** Multiplicar por el tipo real.

| 1 € = | Al mes | Al año |
|---|---:|---:|
| S/ 3,80 | S/ 17 | S/ 205 |
| S/ 4,00 | S/ 18 | S/ 216 |
| S/ 4,20 | S/ 19 | S/ 227 |

**La decisión no cambia en ese rango.**

### Dos costes que no salen en ninguna página de precios

1. **Comisión del banco peruano por compra en moneda extranjera:**
   habitualmente **3-5%**, más posibles cargos por transacción internacional.
   Sobre S/ 250 al año son S/ 8-13 extra.
2. **El IVA alemán del 19% probablemente NO se paga.** Hetzner y Contabo son
   alemanes y su precio de lista suele incluirlo; como cliente fuera de la UE
   normalmente hay exención. Si aplica, el CX22 baja a ~€3,78 ⇒ **~S/ 14/mes,
   S/ 172/año**. Confirmar al contratar.

### Por qué Hetzner y no los otros

- **No Contabo**, aunque ahorre ~S/ 11/mes: fama consistente de hardware
  sobrevendido y soporte lento. Para un laboratorio da igual; para la
  plataforma donde entran clientes, esos S/ 130 al año no compensan una
  tarde de diagnóstico.
- **No Vultr** pese a tener Santiago: casi cinco veces el precio. Santiago
  daría ~40 ms frente a los ~100 ms de Hetzner Ashburn, y **esa diferencia no
  la percibe un usuario** en una aplicación web normal.

### ⚠️ Elegir Ashburn, no Alemania

Ninguno de los proveedores baratos tiene datacenter en Sudamérica. Desde Lima:

| Destino | Latencia |
|---|---|
| Hetzner **Ashburn** (EE.UU. este) | ~90-110 ms |
| Hetzner Alemania | ~200 ms |

Mismo precio, la mitad de latencia. Es la decisión que más se nota y la que
más gente se salta por aceptar el datacenter que viene por defecto.

---

## 5. Comparación de las tres rutas

| | **Oracle gratis** | **Híbrida (recomendada)** | **Todo en un VPS** |
|---|---|---|---|
| Coste anual | S/ 45 (solo dominio) | **~S/ 250** | ~S/ 430 |
| Riesgo de que te apaguen | 🔴 Alto | 🟢 Ninguno | 🟢 Ninguno |
| Riesgo de recorte del proveedor | 🔴 Ya pasó | 🟢 Bajo | 🟢 Bajo |
| ¿Te rechazan el registro? | 🟡 Posible | 🟢 No | 🟢 No |
| ¿Compilas en el servidor? | Sí (12 GB) | ❌ No, en CI | Sí |
| Latencia desde Lima | ~40 ms (Bogotá) | ~100 ms | ~100 ms |

---

## 6. Oracle Cloud Always Free — corrección y asteriscos

`DESPLIEGUE-PRODUCCION.md` (issue #87) dice **4 OCPU / 24 GB**. **Ya no.**
El 15 de junio de 2026 Oracle lo redujo a **2 OCPU / 12 GB** sin anuncio
público —solo editó la documentación— y a partir del 18 de agosto de 2026
terminó las instancias que excedían el nuevo límite.

**No tiene fecha de caducidad:** no es un trial. Mientras se respeten los
límites, funciona indefinidamente. Pero tiene cuatro asteriscos:

| # | Asterisco | Mitigación |
|---|---|---|
| 1 | **Pide tarjeta** de crédito o débito real. Prepago y virtuales se rechazan | Ninguna. Es verificación, no cobro |
| 2 | **Recortaron el tier a la mitad** en junio de 2026, sin avisar | Ninguna. Es su decisión |
| 3 | 🔴 **Apagan instancias ociosas**: CPU p95 <20% **y** red <20% **y** memoria <20% durante 7 días | **Pedir 6 GB, no 12.** Con ~2 GB de uso real eso es el 33%, por encima del umbral. Más UptimeRobot cada 5 min |
| 4 | **"Out of host capacity"** — escasez crónica de ARM. La región no se cambia después | Elegir región poco disputada (Bogotá) y reintentar |

**Sobre convertir a Pay As You Go:** se recomendó en su momento para evitar
el asterisco 3, y **se retira esa recomendación**. Con una tarjeta de saldo
ajustado, un cargo accidental por exceder límites puede suspender la cuenta
con la plataforma dentro. Quedarse en Always Free puro y mitigar con el
dimensionado.

### Registro: dónde falla la gente

El registro rechaza cuentas por sistema antifraude. **Tras dos fallos se
entra en revisión manual**, con casos reportados de más de 10 días.

| Factor | Qué hacer |
|---|---|
| Tarjeta | Visa/Mastercard **de crédito**, con ~20-30 soles disponibles |
| Red | **Sin VPN.** Si el internet es compartido (CGNAT), usar el hotspot del móvil |
| Datos | Nombre = titular de la tarjeta; dirección = la del banco |
| 🔴 Región principal | **Colombia Central (Bogotá)** — cercana a Lima y poco disputada. **Irreversible** |
| VM | **2 OCPU / 6 GB**, Ubuntu 24.04 **ARM (aarch64)**, 100 GB |
| Red de la VM | Abrir 80/443 en **dos capas**: Security List de OCI **y** `iptables` dentro. Las imágenes de Oracle traen iptables restrictivo y abrir solo la primera es el error más común |

---

## 7. 🔴 Bloqueantes antes de exponer nada

Independientes del proveedor elegido.

| # | Bloqueante | Estado |
|---|---|---|
| 1 | **Contraseñas del seed.** `admin@ninjasec.local` / `change-me` está en texto plano en el repositorio. En staging se quieren datos demo, así que no basta con apagar el seed: las contraseñas deben venir de un secreto por entorno (~10 líneas en `seed.py`) | Pendiente |
| 2 | **Rotar G-03** — `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` y el token DuckDNS. **Acción humana**, no automatizable | Pendiente |
| 3 | **Copias de seguridad automáticas.** `docker-compose.prod.yml` monta `./backups` pero no hay ningún trabajo que escriba ahí: es un punto de montaje, no una funcionalidad | Pendiente |
| 4 | Rate limiter en memoria sin `REDIS_URL` | No bloquea con un solo proceso |

**Lo que ya NO bloquea** (resuelto entre el 2026-11-20 y el 2026-11-22):

- ✅ Las guardas de producción funcionan (`IS_PRODUCTION` no encendía nada — PR #119)
- ✅ Swagger cerrado en producción (PR #119)
- ✅ Next.js 16.4.6 y PyJWT 2.14 — dos críticas con RCE y bypass de autenticación
- ✅ Tres fugas multi-tenant en sedes, contactos y topología (PR #131)
- ✅ Alembic es la fuente de verdad del esquema (G-01/G-02, issue #2)

---

## 8. Por dónde continuar

**Decisión pendiente, y es la única que bloquea:**

> **¿Los dos sistemas adicionales son estáticos de verdad** —HTML, CSS, JS,
> sin base de datos— **o alguno necesita backend?**
>
> - Los dos estáticos ⇒ VPS de **4 GB**, ~S/ 250/año
> - Alguno con backend ⇒ VPS de **8 GB**, ~S/ 430/año

**Secuencia una vez decidido:**

1. Cerrar el bloqueante 1 (contraseñas del seed) — es lo único que impide dar
   el visto bueno a publicar
2. Rotar los secretos de G-03 — acción de Mark
3. Contratar el VPS (**Ashburn**, no Alemania) o crear la cuenta de Oracle
4. Dominio en Cloudflare
5. Desplegar con `docker-compose.prod.yml`, que ya está escrito y probado
6. Crear el primer `super_admin` real (script en `DESPLIEGUE-PRODUCCION.md`)
7. Copias de seguridad automáticas
8. CI/CD de despliegue — **después** del primer despliegue manual, nunca antes

---

## Fuentes

- [Comparativa de VPS de 8 GB, noviembre 2026](https://vpsscouter.com/cheapest-vps/8gb-ram)
- [Is Hetzner Still the Cheapest VPS? 24 alternativas, octubre 2026](https://dev.to/hostingsift/is-hetzner-still-the-cheapest-vps-we-priced-24-alternatives-october-2026-271g)
- [Hetzner vs Contabo](https://peon.sh/blogs/hetzner-vs-contabo) · [Contabo vs Hetzner, Cybernews](https://cybernews.com/best-web-hosting/contabo-vs-hetzner/)
- [GitHub Pages desde repositorio privado: planes y visibilidad](https://smartscope.blog/en/Tips/GitHub/github-pages-private-repository/) · [Discusión oficial en GitHub Community](https://github.com/orgs/community/discussions/167331)
- [Vercel Hobby: uso no comercial](https://convika.com/compare/vercel-hobby-commercial-use/)
- [Always Free Resources — documentación oficial de Oracle](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)
- [Oracle recortó el free tier de Ampere A1 a la mitad — InfoQ](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/)
- [Reclamación de instancias ociosas — Oracle Cloud Customer Connect](https://community.oracle.com/customerconnect/discussion/671904/reclamation-of-idle-compute-instances)
