# Roadmap de Proyectos — Networking & Ciberseguridad
### Ecosistema "Ninja SOC" y módulos complementarios

> Pegado por el usuario el 2026-08-09 como fuente de nuevas ideas de módulos. Es
> brainstorming histórico, no especificación (ver regla de `tash/` en `PY-MK/CLAUDE.md`).
> Las partes que sí se incorporaron a la plataforma quedaron registradas en
> `DOCUMENTOS/PLATAFORMA/ROADMAP.md` (Tanda 3, módulos 30-P2, 31, 32) con su propio
> issue en GitHub. La sección 3 y varias ideas de la sección 4 se decidieron
> **fuera de NinjaSec** (ver "Lo que NO va en NinjaSec" en el ROADMAP) por no tener
> cliente, rol ni dato que persistir — son candidatas a un repo de portafolio en
> GitHub Pages aparte.

---

## 1. Proyecto base ya existente

### Ninja SOC
Sistema en Python que consume APIs de herramientas open source (Wazuh, pfSense) y genera reportes PDF automatizados con métricas de seguridad.

---

## 2. Módulos backend / infraestructura (Python)

### 2.1 NetDoctor — Diagnóstico multi-vendor
Herramienta que se conecta por SSH (Netmiko/NAPALM) a Cisco, MikroTik, Huawei y Ubiquiti, ejecuta comandos de diagnóstico, interpreta la salida contra una base de conocimiento (JSON/YAML) de los 30 problemas comunes de un ingeniero de redes, y genera reporte PDF con hallazgos y remediación sugerida.

**Basado en (de tu infografía MR IT & Networking):** conflictos de IP, sin conectividad, rendimiento lento, latencia/pérdida de paquetes, DNS, DHCP, VLANs, trunk, OSPF/EIGRP/BGP, gateway, puertos down, duplex mismatch, STP loops, ACLs, NAT, VPN, firewall rules, wireless, AAA/RADIUS, hardware failures, cables, PoE, broadcast storms, CPU/memoria, outages por config, CRC errors, MTU, QoS, SNMP, Syslog.

**APIs/librerías open source:**
- **Netmiko** / **NAPALM** — conexión multi-vendor SSH
- **Nornir** — orquestación de tareas de red a escala (alternativa/complemento a Ansible)
- **TextFSM** / **ntc-templates** — parseo estructurado de `show` commands ya con plantillas hechas para decenas de vendors
- **Genie (Cisco)** — parsing avanzado de outputs Cisco, gratuito

### 2.2 Puente Wazuh ↔ pfSense (mini-SOAR)
Cuando Wazuh detecta fuerza bruta repetida, dispara bloqueo automático de IP en pfSense vía su API.

**Recursos:**
- **Wazuh API** (REST, documentada oficialmente)
- **pfSense API** (paquete community `pfsense-api` de jaredhendrickson13, open source)
- **TheHive + Cortex** (open source SOAR real, puedes inspirarte en su modelo de playbooks)
- **Shuffle** (SOAR open source, gratis, puedes integrar tus propios workflows)

### 2.3 Normalizador de logs multi-fuente
Convierte logs de Suricata, pfSense, Wazuh a un esquema común (tipo CEF o ECS) y los centraliza.

**Recursos:**
- **Elastic Common Schema (ECS)** — estándar abierto de normalización
- **Fluentd** / **Vector.dev** — recolección y transformación de logs, open source
- **Grafana + Loki** (gratis, self-hosted) — visualización, alternativa ligera a ELK completo

### 2.4 Scoring de riesgo por IP/host
Combina reputación externa + alertas internas de Wazuh para priorizar qué atender primero.

**APIs gratuitas (con límites free tier):**
- **AbuseIPDB API** — reputación de IPs, gratis hasta 1000 consultas/día
- **VirusTotal API** (community) — reputación de IPs/dominios/hashes
- **Shodan API** (free tier limitado) — exposición de activos públicos
- **GreyNoise Community API** — distingue ruido de internet vs. ataques dirigidos, gratis

### 2.5 Reporte de cumplimiento (ISO 27001 / Ley de Protección de Datos Perú)
Cruza datos de Wazuh + pfSense contra checklist normativo, genera gap analysis en PDF.

**Recursos:**
- **CIS Benchmarks** (gratuitos en PDF, puedes tokenizarlos como base de checklist)
- **OpenSCAP** — evaluación automatizada de compliance, open source

### 2.6 Inventario de activos vulnerables
Cruza resultados de escaneo con CVEs recientes, prioriza por criticidad.

**APIs/herramientas:**
- **NVD API** (api.nist.gov) — CVEs oficiales, gratis, requiere API key gratuita para más throughput
- **OpenVAS / Greenbone Community Edition** — escáner de vulnerabilidades open source
- **CIRCL CVE Search API** — alternativa a NVD, sin key
- **EPSS API** (FIRST.org) — probabilidad de explotación real de un CVE, gratis, complementa muy bien al CVSS

---

## 3. Módulos frontend estático (GitHub Pages)

### 3.1 Centralized Network Device Documentation Hub
Base de datos de equipos (Cisco, MikroTik, Huawei, Ubiquiti...) con filtros facetados (marca, categoría, capa OSI, PoE, apilable, EOL, precio), búsqueda fuzzy y links externos a datasheets oficiales (nunca alojados localmente, por copyright).

**Stack:** Fuse.js (búsqueda), JSON por vendor/categoría, Tailwind, opcionalmente Eleventy para páginas individuales por equipo (mejor SEO).

### 3.2 Config Visualizer
El usuario sube un archivo de configuración (Cisco IOS, MikroTik, pfSense XML), todo se parsea 100% client-side (nunca sale del navegador — argumento de seguridad fuerte para pymes), y genera:
- Diagrama de topología con interfaces, VLANs, trunk/access, IPs (Mermaid.js o D3.js)
- Tarjetas de especificación por interfaz
- Resumen ejecutivo con alertas de misconfiguración (conecta directo con NetDoctor)

**Estructura modular:** `parsers/cisco.js`, `parsers/mikrotik.js`, `parsers/pfsense.js` — empezar solo con Cisco IOS y escalar.

### 3.3 Wizard de diagnóstico interactivo
Árbol de decisión (¿tienes conectividad? → ¿ping al gateway? → ...) que termina identificando cuál de los 30 problemas comunes tienes, con el comando exacto por marca. Todo en JS + JSON local, sin backend.

### 3.4 Cheat sheet multi-vendor / Rosetta Stone de comandos
Tabla comparativa: seleccionas el problema y el equipo, te muestra el comando equivalente entre Cisco, MikroTik, Huawei, Ubiquiti.

### 3.5 Simulador de ACLs
Defines reglas tipo `permit/deny`, pruebas paquetes contra ellas, visualización de si pasan o se bloquean.

### 3.6 Simulador visual de STP
Dibujas una topología, eliges el root bridge, animación de cómo se bloquean puertos para evitar loops.

### 3.7 Calculadora de VLSM/Subnetting
Con visualización gráfica del árbol de subredes.

### 3.8 Visualizador de tabla de enrutamiento
Pegas el output de `show ip route`, se grafica como árbol/topología.

### 3.9 Analizador de logs Syslog (client-side)
Subes un log, se parsea en el navegador, resalta patrones de error comunes — nunca sale de tu máquina.

### 3.10 Dashboard de CVEs recientes
Consume la NVD API públicamente, gráfica tendencias por severidad, todo con `fetch()` directo desde el navegador, sin backend.

### 3.11 Consultor de vulnerabilidades por producto
Buscas "Cisco IOS 15.2" y consulta NVD API para mostrar CVEs conocidos del producto.

### 3.12 Verificador de DNS/MX
Usando DNS-over-HTTPS (Cloudflare o Google, ambas APIs públicas y gratuitas) para diagnosticar problemas de resolución sin servidor propio.

### 3.13 Wiki estática de troubleshooting
Docsify o MkDocs + GitHub Pages, documentando los 30 problemas con ejemplos reales — funciona como marca personal técnica.

### 3.14 Flashcards/quiz de troubleshooting
Modo estudio para certificaciones (CCNA, Network+, Security+) usando los 30 escenarios como banco de preguntas.

---

## 4. Ideas nuevas complementarias

### 4.1 Simulador de ataques comunes (educativo, client-side)
Visualización animada de cómo funciona ARP spoofing, DDoS, DNS spoofing — sin ejecutar nada real, solo pedagógico, con D3.js. Muy usado en portafolios de ciberseguridad porque demuestra que entiendes el "por qué", no solo el "cómo mitigar".

### 4.2 Generador de topologías desde JSON a Mermaid/D3
Tú (o el usuario) defines una topología en JSON simple, el sistema la dibuja automáticamente — útil como herramienta de documentación para tus propios labs y como demo reusable en otros módulos.

### 4.3 Password/Hash analyzer client-side
Calcula entropía, tiempo estimado de crackeo y detecta si un hash corresponde a un algoritmo débil (MD5/SHA1) — todo en el navegador, refuerza el mensaje "nunca sale tu dato".

### 4.4 Verificador de cabeceras de seguridad HTTP
El usuario ingresa una URL, tú haces `fetch()` (con CORS proxy propio simple o usando `securityheaders.com` como referencia) y evalúas si tiene CSP, HSTS, X-Frame-Options, etc. — tipo Mozilla Observatory casero.

### 4.5 Comparador de EOL/EOS de equipos
Cruzas tu Device Hub con fechas de fin de soporte, alertas automáticas de "este equipo ya no recibe parches" — muy útil para pymes que no monitorean el ciclo de vida de su hardware.

### 4.6 Generador de diagramas de red desde Nmap
El usuario pega el output de un escaneo Nmap (XML), tú lo parseas client-side y generas un mapa visual de la red descubierta con puertos/servicios detectados.

### 4.7 Simulador de subneteo IPv6
Complemento al de VLSM — el IPv6 sigue siendo un vacío de herramientas didácticas en español.

### 4.8 Generador de políticas de firewall en múltiples sintaxis
Defines la regla una vez en un formato propio (JSON/YAML) y el sistema te la traduce a sintaxis de iptables, pfSense, Cisco ASA y MikroTik — resuelve el problema real de migrar reglas entre plataformas.

### 4.9 Panel de "salud de red" tipo semáforo (ejecutivo)
Consumiendo Wazuh + pfSense + NetDoctor, cada problema detectado resta puntos de un índice 0-100, con lenguaje no técnico para gerencia — cierra el círculo entre todos tus módulos backend.

### 4.10 Escáner de exposición pasiva con Shodan
Ingresas tu IP pública o rango, consultas Shodan (free tier) para ver qué ve internet de tu infraestructura sin escanear activamente (pasivo, sin riesgo legal).

---

## 5. Tabla resumen de APIs/recursos open source mencionados

| Recurso | Uso | Costo |
|---|---|---|
| Netmiko / NAPALM / Nornir | Automatización SSH multi-vendor | Gratis |
| TextFSM / ntc-templates / Genie | Parsing de outputs de red | Gratis |
| Wazuh API | SIEM open source | Gratis |
| pfSense API (community) | Firewall automation | Gratis |
| TheHive + Cortex / Shuffle | SOAR open source | Gratis |
| Elastic Common Schema | Normalización de logs | Gratis (estándar) |
| Fluentd / Vector.dev | Pipeline de logs | Gratis |
| Grafana + Loki | Visualización de logs | Gratis (self-hosted) |
| AbuseIPDB API | Reputación de IPs | Gratis (limitado) |
| VirusTotal API | Reputación IP/dominio/hash | Gratis (limitado) |
| Shodan API | Exposición de activos | Free tier limitado |
| GreyNoise Community API | Ruido vs. ataque dirigido | Gratis |
| NVD API | Base de datos de CVEs | Gratis (con key) |
| CIRCL CVE Search | Alternativa a NVD | Gratis, sin key |
| EPSS API (FIRST.org) | Probabilidad de explotación | Gratis |
| OpenVAS / Greenbone CE | Escáner de vulnerabilidades | Gratis |
| OpenSCAP | Compliance automatizado | Gratis |
| CIS Benchmarks | Checklists de hardening | Gratis (PDF) |
| Cloudflare / Google DoH | Consultas DNS seguras | Gratis |
| Mermaid.js / D3.js | Diagramas y topologías | Gratis |
| Fuse.js | Búsqueda fuzzy | Gratis |

---

## 6. Sugerencia de priorización

1. **Corto plazo (portafolio rápido, GitHub Pages):** Device Hub + Config Visualizer (Cisco) + Wizard de diagnóstico — los tres se conectan visualmente y son fáciles de demostrar en una entrevista.
2. **Mediano plazo (tesis/proyecto fuerte):** NetDoctor con Netmiko/NAPALM + integración con Wazuh/pfSense — demuestra automatización real, no solo frontend.
3. **Largo plazo (diferenciador):** Puente Wazuh↔pfSense (mini-SOAR) + panel de salud de red — es lo que más "vende" como solución real para pymes sin SOC propio.
