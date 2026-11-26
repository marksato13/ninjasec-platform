# Iconos para generar con GPT

Los logos de `public/marcas/` salen de **Simple Icons 13.21.0 (CC0)** y
**Devicon 2.16.0 (MIT)**. Las normas, los protocolos y los servicios propios
usan iconos de **lucide-react**. Lo que queda aquí no tiene icono libre en esas
fuentes.

## Regla que no se negocia

**Nunca se le pide a GPT que imite el logo de una marca.** Una marca
registrada solo se usa con su logo oficial y libre. Para las que no lo tienen,
se pide un **icono genérico de su categoría** con el nombre escrito como texto,
que no se confunde con el logo real.

## Estilo común (pegarlo al inicio de cada prompt)

> Icono cuadrado de 512×512 px, estilo plano, sin degradados ni sombras, fondo
> transparente. Trazos redondeados de grosor uniforme (equivalente a 2 px a
> 24 px). Paleta limitada: azul `#3B82F6`, cian `#22D3EE`, verde `#10B981`,
> violeta `#A78BFA` y un tono claro `#E2EEFF`; nada de negro puro. Debe leerse
> sobre fondo oscuro `#060D18` y sobre fondo claro `#F0F4FA`. Sin texto pequeño:
> si lleva texto, una sola palabra en una tipografía sans-serif gruesa que ocupe
> al menos un tercio del ancho. Márgenes interiores del 10 %. Entrega PNG y,
> si es posible, SVG.

## 1. Marcas sin icono libre (hoy se ven con iniciales)

Estas cuatro no existen en Simple Icons 13.21.0 ni en Devicon 2.16.0 (HTTP 404
en ambos). En la plataforma se muestran con **iniciales** hasta que haya icono.

| Slug | Marca | Iniciales que se ven hoy |
|---|---|---|
| `wazuh` | Wazuh | WA |
| `suricata` | Suricata | SU |
| `zabbix` | Zabbix | ZA |
| `nagios` | Nagios | NA |

### `wazuh.svg` — SIEM / XDR

> [Estilo común]. Icono genérico de «plataforma SIEM»: un escudo de contorno
> cian `#22D3EE` con un pequeño gráfico de líneas ascendente dentro, en azul
> `#3B82F6`, y un punto de alerta verde `#10B981` en la esquina superior
> derecha del escudo. Debajo, la palabra «WAZUH» en texto claro. No imites el
> logotipo oficial de Wazuh ni sus colores ni su forma.

### `suricata.svg` — IDS / IPS

> [Estilo común]. Icono genérico de «detección de intrusiones en red»: tres
> nodos unidos por líneas en azul `#3B82F6`, y una lupa cian `#22D3EE`
> superpuesta que examina la línea central, con un pequeño rombo de alerta
> verde `#10B981`. Debajo, la palabra «SURICATA». No dibujes un animal ni imites
> el logotipo oficial de Suricata.

### `zabbix.svg` — Monitoreo de infraestructura

> [Estilo común]. Icono genérico de «monitoreo de servidores»: un servidor de
> rack visto de frente, en contorno azul `#3B82F6`, con una línea de pulso cian
> `#22D3EE` que lo cruza y un indicador verde `#10B981` encendido. Debajo, la
> palabra «ZABBIX». No uses un cuadrado rojo con una letra ni imites el
> logotipo oficial de Zabbix.

### `nagios.svg` — Monitoreo y alertas

> [Estilo común]. Icono genérico de «estado de servicios»: una lista de tres
> filas, cada una con un círculo de estado (verde `#10B981`, cian `#22D3EE` y
> violeta `#A78BFA`), dentro de un marco de monitor azul `#3B82F6`. Debajo, la
> palabra «NAGIOS». No imites el logotipo oficial de Nagios.

Al tenerlos: guardarlos como `public/marcas/<slug>.svg`, verificar que el SVG no
trae `<script` ni atributos `on*=`, y en `src/lib/marcas.ts` cambiar su `fuente`
de `"pendiente-gpt"` a `"generado"` con `icono: "/marcas/<slug>.svg"` (añadir
ese valor al tipo `FuenteMarca` y a `MarcaIcono`, que los mostrará como `<img>`).

## 2. Opcional: normas y servicios con un icono propio

Hoy usan lucide y se ven bien. Si se quiere un juego propio, coherente con la
marca NinjaSec, estos son los prompts. Ninguna norma tiene un logo libre de
usar: **no reproducir el sello de ISO, NIST, CIS, AXELOS (ITIL), ISACA (COBIT)
ni The Open Group (TOGAF)**.

| Slug | Prompt (tras el estilo común) |
|---|---|
| `iso-27001` | Escudo azul con una marca de verificación cian y la palabra «27001». |
| `iso-27002` | Lista de controles: cuatro casillas, tres marcadas en verde, y la palabra «27002». |
| `iso-19011` | Portapapeles con una lupa cian encima y la palabra «19011». |
| `nist` | Cinco segmentos de un anillo (identificar, proteger, detectar, responder, recuperar) en azul, cian, verde, violeta y claro; sin texto. |
| `cis-controls` | Lista numerada de tres filas con números grandes 1, 2, 3 y la palabra «CIS». |
| `itil` | Ciclo de tres flechas circulares alrededor de un engranaje, y la palabra «ITIL». |
| `cobit` | Balanza equilibrada con un pequeño engranaje en el fiel, y la palabra «COBIT». |
| `magerit` | Medidor semicircular con la aguja en la zona media, y la palabra «MAGERIT». |
| `togaf` | Tres capas apiladas en perspectiva (negocio, aplicación, tecnología) en azul, cian y violeta, sin texto. |
| `svc-ciberseguridad` | Escudo cian con un circuito sencillo dentro. |
| `svc-auditoria` | Documento con lupa y una marca de verificación verde. |
| `svc-redes` | Tres nodos conectados en triángulo alrededor de un switch. |
| `svc-firewall` | Muro de ladrillos azul con una llama estilizada cian, sin texto. |
| `svc-monitoreo` | Pantalla con una línea de pulso cian. |
| `svc-nube` | Nube azul con una flecha de subida cian. |
| `svc-desarrollo` | Corchetes angulares `< />` en violeta. |
| `svc-apis` | Dos enchufes que se conectan, en azul y cian. |
| `svc-automatizacion` | Diagrama de flujo de tres pasos con flechas, en violeta y cian. |
| `svc-vulnerabilidades` | Insecto estilizado dentro de una mira, en verde y azul. |
| `svc-documentacion` | Libro abierto con líneas de texto cian. |

## Inventario por fuente

| Fuente | Cuántos |
|---|---|
| Simple Icons 13.21.0 | 59 |
| Devicon 2.16.0 | 5 (Java, PowerShell, Windows, AWS, Oracle Cloud) |
| lucide-react | 37 |
| Pendiente de GPT (iniciales) | 4 (Wazuh, Suricata, Zabbix, Nagios) |
