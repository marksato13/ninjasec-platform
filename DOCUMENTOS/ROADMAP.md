# ROADMAP — Ninja Tech

> Priorización de los módulos 23-30 y de los pendientes críticos detectados en 15-22.
> Creado: 2026-08-05 · **Revisado y verificado contra el código: 2026-08-06**

📋 Inventario completo de pendientes: **`IMPLEMENTACION/00-BACKLOG-GLOBAL.md`**
🖥️ Staging publico multiproyecto (ESXi ahora, Oracle Cloud despues): **`ESTRATEGIA/09-STAGING-MULTIPROYECTO.md`**

---

## Criterio de priorización

Tres ejes, en este orden:

1. **Deadline duro** — los entregables académicos del ciclo 10 tienen fecha; el producto no
2. **Relación valor/esfuerzo** — trabajo ya hecho que no se está aprovechando va primero
3. **Riesgo** — lo que puede romper la confianza del cliente antes que lo que agrega funciones

---

## ✅ Tanda 0 — Deuda crítica · **CERRADA el 2026-08-06**

Los seis huecos que comprometían la integridad del dato o el aislamiento entre clientes. **63 tests pasan** (26 previos + 37 nuevos), sin regresiones.

| # | Pendiente | Módulo | Cómo se cerró |
|---|---|---|---|
| 1 | ~~`20-P-08` Filtrar `GET /products` por organización~~ | 20 | Los tres catálogos filtran por `organization_id`. `Area`/`ProjectType` admiten además globales (`NULL`). **Los tests se corrieron contra el código original y fallaron** — tienen dientes |
| 2 | ~~`21-P-02` / `17-P-05` Expiración de certificaciones~~ | 21, 17 | `is_expired`, `days_until_expiry` y `effective_status` derivados en lectura, sin mutar el `status` almacenado |
| 3 | ~~`21-P-01` / `17-P-04` Re-verificación al editar~~ | 21, 17 | `app/common/verification.py` — la regla en un solo sitio para que skills y certificaciones no diverjan |
| 4 | ~~`15-P-05` Rate limiting en el endpoint público~~ | 15 | Ventana deslizante en memoria: 5 postulaciones/hora por IP |
| 5 | ~~`20-P-06` Endpoints de escritura para areas y project-types~~ | 20 | `POST`/`PUT` + endpoints `/usage`. Cubre también `20-P-07` |
| 6 | ~~`20-P-09` Unicidad compuesta con `organization_id`~~ | 20 | `UniqueConstraint` en los 3 modelos + migración `20260806_01` |

**Dos límites que quedaron escritos, no escondidos:**

- El rate limiter es **por proceso y en memoria**: con varios workers el límite efectivo se multiplica y no frena un ataque distribuido. Migrar a Redis o a Caddy cuando el despliegue crezca.
- En PostgreSQL los `NULL` son distintos entre sí, así que la unicidad compuesta **no** impide dos catálogos globales homónimos. Los globales vienen del seed, que sí es controlado.

---

## ✅ Tanda 0-bis — Deuda de esquema — **CERRADA el 2026-08-07** (issue #2, G-01/G-02)

No pertenecía a ningún módulo, pero condicionaba todo despliegue. **Este párrafo quedó desactualizado y se corrige acá** — `CLAUDE.md` ya lo tenía marcado como resuelto, este documento no.

**El problema que había:** el esquema no lo construía Alembic. Lo construía `Base.metadata.create_all()` en `app/main.py:19`, y `migrations/versions/` solo tenía dos parches incrementales cuyo primer archivo llevaba `down_revision = None` sin crear tabla alguna.

| # | Consecuencia que tenía | Cómo se cerró |
|---|---|---|
| G-01 | `create_all` nunca alteraba lo existente — una columna nueva se aplicaba en una base vacía y se ignoraba sin error en una base con datos | Migración base `20260807_00_esquema_base_completo.py` (generada con `--autogenerate` sobre una base vacía), encadenada antes de `20260522_01`. `create_all()` retirado de `app/main.py` |
| G-02 | `alembic upgrade head` no levantaba una base desde cero | Resuelto por la misma migración base |

`app/db/migrate.py` corre `alembic upgrade head` automáticamente al arrancar el contenedor backend (ver `backend/Dockerfile`) — las migraciones ya son parte del flujo normal de despliegue, no un paso manual aparte. Verificado además contra un Postgres real vacío en cada PR que toca el esquema (`tests/test_alembic_bootstrap.py -m integration`).

**Runbook de despliegue self-hosted completo (issue #87):** `FLUJOS/DESPLIEGUE-PRODUCCION.md`.

---

## Tanda 0-c — Entrega segura y automatización

Trabajo transversal documentado como **módulo 33** el 2026-08-23. No bloquea el
desarrollo local de la Tanda 1 ni los entregables académicos, pero sí bloquea
cualquier activación de CD real.

| Orden | Trabajo | Esfuerzo | Por qué ahora |
|---|---|---|---|
| 1 | `33-P-01` a `33-P-05` | 2 sesiones | Endurece CI existente, seguridad de supply chain y actualizaciones revisables |
| 2 | `33-P-06`, `33-P-08`, `33-P-07`, `33-P-09` | 2 sesiones | Staging, backup/restauración, producción protegida y evidencia operativa |
| 3 | `33-P-10` y `33-P-11` | 1 sesión de piloto | Evalúa agentes abiertos sin permisos de merge, despliegue o secretos |

**Puerta innegociable:** no se habilita producción hasta contar con backup y
restauración probados, aprobación humana en GitHub y rollback verificable.
Detalles en `PLANIFICACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md`.

---

## 🎯 Tanda 1 — Ganancia rápida

| Orden | Trabajo | Esfuerzo | Por qué ahora |
|---|---|---|---|
| 1 | **23-P1** Diagrama de topología (UI) | 1 sesión | 🔥 El backend está 100% hecho y **nadie lo consume**. Máximo retorno del roadmap |
| 2 | **23-P2** Editor de conexiones | 0.5 sesión | Completa el módulo y lo hace usable |
| 3 | ~~`20-P-01`/`20-P-02` CRUD de catálogos en UI~~ | — | ✅ **Cerrado 2026-08-09**: `/dashboard/settings` ya permite crear, editar y desactivar áreas y tipos de proyecto; la desactivación consulta `/usage` y exige confirmación cuando hay dependencias |
| 4 | `16-P-01` Export del audit log a PDF/XLSX | 0.5 sesión | Requisito del curso de Auditoría y de E5 |

**Total pendiente: ~2 sesiones.** Al terminar hay una funcionalidad demostrable nueva (topología) y la plataforma queda administrable.

---

## 🎓 Tanda 2 — Entregables académicos (deadline duro)

Esta es la tanda con fecha real. Los tres cursos del ciclo 10 concentran sus entregables de mayor peso en la última semana.

| Orden | Trabajo | Esfuerzo | Entregable | Peso |
|---|---|---|---|---|
| 1 | **26-P1** Plan de auditoría + export PDF | 1.5 sesiones | Auditoría de Sistemas | **25%** |
| 2 | **24-P1** Catálogo ISO 27001 + SoA | 2 sesiones | Seguridad — U1 | **15%** |
| 3 | **25-P1** Registro de riesgos + scores | 1.5 sesiones | Seguridad — U2 (parte) | — |
| 4 | **25-P2** Catálogos + mapa de calor | 1.5 sesiones | Seguridad — U2 | **25%** |
| 5 | **27-P1** Repositorio de arquitectura | 1.5 sesiones | Arq. Empresarial — U1 | **25%** |
| 6 | **24-P2** Evidencia derivada | 2 sesiones | Seguridad — U2/U3 | — |
| 7 | **26-P2/P3** Programa + hallazgos ISO 19011 | 2.5 sesiones | Auditoría | — |
| 8 | **27-P2** Sincronización capa tecnológica | 1 sesión | Arq. Empresarial | — |
| 9 | **24-P3** Gap analysis + export | 1.5 sesiones | Seguridad — U3 | **30%** |
| 10 | **26-P4** Informe final de auditoría | 1.5 sesiones | Auditoría | **30%** |
| 11 | **27-P4** Gap analysis de arquitectura | 1 sesión | Arq. Empresarial — U2 | **45%** |

**Total: ~17 sesiones.** Cubre el 70% de Seguridad, el 55% de Auditoría y el 70% de Arquitectura Empresarial.

⚠️ **Empezar con margen.** El plan de auditoría (26-P1) va primero porque es el entregable más temprano y el más autónomo.

---

## 🚀 Tanda 3 — Producto y diferenciación

Sin deadline externo. Se ejecuta cuando la tanda 2 esté encaminada.

| Orden | Trabajo | Esfuerzo | Valor |
|---|---|---|---|
| 1 | **28-P1** Base de conocimiento NetDoctor + modo guiado | 2 sesiones | Alto — producto completo por sí solo ✅ **Cerrado 2026-08-10** (mayormente — ver notas en IMPLEMENTACION) |
| 2 | **29-P1→P3** Catálogo de equipos + **alerta de EOL** | 3.5 sesiones | 🔥 Motor de oportunidades comerciales — 🟡 P1+P2 cerrados 2026-08-10 (issue #85, ver IMPLEMENTACION), **la alerta de EOL de P3 sigue pendiente** |
| 3 | **30-P1** Conector Wazuh + esquema normalizado (incluye normalización multi-fuente vs. Suricata/pfSense) | 2 sesiones | Alto — amplía el stack open source |
| 4 | **23-P3/P4** Config Visualizer (parser Cisco IOS) | 3 sesiones | Alto — muy demostrable ✅ **Cerrado 2026-08-09** |
| 5 | **30-P2** Scoring de riesgo por IP/host (AbuseIPDB + VirusTotal + GreyNoise cruzado con alertas de Wazuh) | 1.5 sesiones | Alto — prioriza qué atender primero |
| 6 | **30-P3** Informe ejecutivo "SOC as a report" (incluye panel de salud de red tipo semáforo, no técnico) | 1.5 sesiones | Alto — el patrón que define el proyecto ✅ **Cerrado 2026-08-10** (parcial — envío por correo y multi-sede quedan pendientes) |
| 7 | **28-P2** Cobertura Cisco + MikroTik | 1.5 sesiones | Medio |
| 8 | **31-P1** Compliance automatizado: cruce Wazuh/pfSense vs. CIS Benchmarks / OpenSCAP | 2 sesiones | Alto — complementa el 24 (SoA manual) con verificación técnica automática ✅ **Cerrado 2026-08-10** |
| 9 | **32-P1** Inventario de vulnerabilidades (CIRCL + EPSS) por dispositivo del cliente | 1.5 sesiones | Alto — prioriza parches por explotabilidad real, no solo CVSS ✅ **Cerrado 2026-08-10** |
| 10 | **32-P2** Exposición pasiva vía Shodan (solo IP/rango del cliente, sin escaneo activo) | 0.5 sesión | Medio — bajo riesgo legal, alto valor de venta |

**Total: ~15.5 sesiones.**

**Nota sobre 2.5/2.6 de la propuesta original (`ideas-roadmap-networking.md`):** el "reporte de cumplimiento" y el "inventario de activos vulnerables" no son el mismo trabajo que el módulo 24 (SGSI ISO 27001). El 24 es la Declaración de Aplicabilidad que un consultor completa a mano sobre los 93 controles del Anexo A. Los módulos 31 y 32 son **verificación técnica automática** contra datos reales de Wazuh/pfSense/NVD — se complementan, no se pisan.

---

## 🔒 Tanda 4 — Alto riesgo (requiere puerta de seguridad)

**No arrancan hasta cumplir sus requisitos previos.** Ambos manipulan infraestructura de clientes.

| Trabajo | Requisito previo innegociable |
|---|---|
| **28-P3** NetDoctor por SSH | Credenciales cifradas · lista blanca de comandos · registro por comando · timeout · cuenta de solo lectura · **autorización escrita del cliente** |
| **30-P6** Bloqueo automático Wazuh→pfSense | Lista blanca verificada · bloqueos con caducidad · reversión inmediata · aprobación humana · dry run · **autorización escrita del cliente** |

Si los requisitos no se pueden garantizar: **28 se queda en P2 y 30 en P5.** Ambos siguen aportando casi todo su valor.

---

## Decisiones pendientes que bloquean trabajo

| Decisión | Bloquea | Recomendación |
|---|---|---|
| Librería de diagramación | 23-P1, 27-P3 | **React Flow** (`@xyflow/react`) — se amortiza en dos módulos |
| ¿Editor ArchiMate propio o importar desde Archi? | 27-P3 | **Importar.** Ahorra ~3 sesiones sin perder el diferencial |
| Almacenamiento de archivos | 10-P-05, 15-P-02, 19-P-01, 21-P-05 | Un solo storage (MinIO o filesystem + Caddy) resuelve cuatro pendientes |
| ¿Se retoma FASE 2.6 del lab? | 30-P7 (conector Suricata) | El lab es el mejor entorno de pruebas del módulo 30 |
| Estrategia Alembic | G-01, G-02, FASE 2.8 | Migración base autogenerada + retirar `create_all()`. **No es opcional para producción** |
| ¿`Area`/`ProjectType` son globales o por tenant? | 20-P-09, 20-P-10 | Hoy son ambiguos (`organization_id` nullable + `unique` global). Decidir y hacerlo explícito |

---

## Lo que NO va en Ninja Tech

Ideas válidas que pertenecen a un repo de portafolio en GitHub Pages, no a la plataforma:

- Calculadora de VLSM / subnetting (y su variante IPv6)
- Simulador visual de STP
- Simulador de ACLs
- Flashcards de troubleshooting para CCNA / Network+
- Visualizador de tabla de enrutamiento
- Analizador de logs syslog client-side
- Consultor de CVEs vía API del NVD (búsqueda genérica por producto, sin cliente asociado)
- Wizard de diagnóstico interactivo genérico (árbol de decisión sin datos de un cliente real)
- Cheat sheet / Rosetta Stone de comandos multi-vendor
- Wiki estática de troubleshooting
- Simulador educativo de ataques comunes (ARP spoofing, DDoS, DNS spoofing)
- Generador genérico de topologías desde JSON a Mermaid/D3 (sin persistencia ni cliente)
- Password/Hash analyzer client-side
- Verificador de cabeceras de seguridad HTTP (tipo Mozilla Observatory)
- Generador de diagramas de red desde un XML de Nmap pegado a mano
- Generador de políticas de firewall multi-sintaxis (iptables/pfSense/ASA/MikroTik) sin cliente asociado
- Verificador de DNS/MX vía DoH

Son excelentes demos de portafolio (revisado y ampliado 2026-08-09 contra `ideas-roadmap-networking.md`, la propuesta completa que dio origen a los módulos 23/24/25/26/27/28/29/30). Dentro de Ninja Tech serían ruido: no tienen cliente, ni rol, ni dato que persistir. **Si en algún momento se decide que sí van dentro de la plataforma** (por ejemplo, como una sección pública `/herramientas` de lead-gen en el sitio de marketing), es una decisión de producto explícita — no asumirla por defecto.

---

## Resumen de esfuerzo

| Tanda | Sesiones | Naturaleza |
|---|---|---|
| ~~0 — Deuda crítica~~ | — | ✅ **Cerrada el 2026-08-06** |
| 0-bis — Deuda de esquema | ~0.5 | Obligatoria **antes de FASE 2.8** · ⚠️ ahora más urgente: la migración `20260806_01` es la primera que la necesita |
| 1 — Ganancia rápida | ~2.5 | Alto retorno inmediato |
| 2 — Académica | ~17 | **Deadline duro** |
| 3 — Producto | ~13.5 | Sin fecha |
| 4 — Alto riesgo | — | Condicionada |

**Siguiente paso: Tanda 1**, empezando por `23-P1` (UI de topología) — el backend está hecho y nadie lo consume.
La **0-bis** puede esperar mientras el entorno se siga recreando, pero **no puede saltarse antes del deploy self-hosted**.

---

## Lo que quedó fuera de las tandas

Los **7 pendientes abiertos de los módulos 01-14** no entran en ninguna tanda: son mejoras de UX de baja consecuencia (`02-P-04`, `02-P-05`, `05-P-05`, `06-P-05`, `09-P-05`) más dos que dependen de decisiones ya listadas (`08-P-02` necesita `@dnd-kit`, `10-P-05` necesita el storage).

Se atienden por oportunidad, cuando se toque el módulo por otra razón. Están en `IMPLEMENTACION/00-BACKLOG-GLOBAL.md` §3.
