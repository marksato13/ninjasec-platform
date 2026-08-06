# ROADMAP — NinjaSec

> Priorización de los módulos 23-30 y de los pendientes críticos detectados en 15-22.
> Creado: 2026-08-05 · **Revisado y verificado contra el código: 2026-08-06**

📋 Inventario completo de pendientes: **`IMPLEMENTACION/00-BACKLOG-GLOBAL.md`**

---

## Criterio de priorización

Tres ejes, en este orden:

1. **Deadline duro** — los entregables académicos del ciclo 10 tienen fecha; el producto no
2. **Relación valor/esfuerzo** — trabajo ya hecho que no se está aprovechando va primero
3. **Riesgo** — lo que puede romper la confianza del cliente antes que lo que agrega funciones

---

## 🔥 Tanda 0 — Deuda crítica (antes de cualquier módulo nuevo)

Pendientes que comprometen la integridad del dato o el aislamiento entre clientes.
Revisado el 2026-08-06: **entra `20-P-08` en primer lugar** y se añade la deuda de esquema.

| # | Pendiente | Módulo | Por qué es crítico |
|---|---|---|---|
| 1 | `20-P-08` Filtrar `GET /products` por organización | 20 | 🆕 **Fuga entre tenants.** `Product.organization_id` es `NOT NULL` pero el endpoint no filtra: cualquier autenticado —incluido un `client`— ve los productos de todas las organizaciones. **El fix es una línea** |
| 2 | `21-P-02` / `17-P-05` Expiración de certificaciones | 21, 17 | Se muestra "verificado" sobre certificaciones caducadas — **información falsa de cara al cliente** |
| 3 | `21-P-01` / `17-P-04` Re-verificación al editar | 21, 17 | Permite elevar una capacidad ya aprobada sin nueva revisión |
| 4 | `15-P-05` Rate limiting en el endpoint público | 15 | Único endpoint sin autenticación; vector de inundación trivial |
| 5 | `20-P-06` Endpoints de escritura para areas y project-types | 20 | Bloquea toda la administración de catálogos |
| 6 | `20-P-09` Unicidad compuesta con `organization_id` | 20 | 🆕 `Area.name` y `ProjectType.name` son `unique` globales: el segundo tenant no puede crear sus catálogos. **Requiere migración — más barato antes de tener datos que colisionen** |

**Esfuerzo total: ~1 sesión.** Es barato y cierra seis huecos reales.

> **Orden dentro de la tanda:** `20-P-08` primero. Es la de menor esfuerzo y la única con consecuencia hacia afuera.

---

## 🧱 Tanda 0-bis — Deuda de esquema (bloqueante de FASE 2.8)

No pertenece a ningún módulo, pero condiciona todo despliegue.

**El problema:** el esquema no lo construye Alembic. Lo construye `Base.metadata.create_all()` en `app/main.py:19`, y `migrations/versions/` solo tiene dos parches incrementales cuyo primer archivo lleva `down_revision = None` sin crear tabla alguna.

Dos consecuencias, ambas silenciosas:

| # | Consecuencia | Detalle |
|---|---|---|
| G-01 | **`create_all` nunca altera lo existente** | Crea las tablas que faltan y no toca las que ya están. Cualquier columna nueva en un modelo se aplica en una base vacía y **se ignora sin error** en una base con datos. Es exactamente el escenario de una actualización en producción |
| G-02 | **`alembic upgrade head` no levanta una base desde cero** | La primera migración hace `add_column` sobre `clients`, `services`, `projects`… que aún no existen |

Hoy no duele porque el entorno se recrea. **Duele el día que haya una base con datos que actualizar** — es decir, el día del deploy self-hosted.

**Fix:** generar la migración base con `alembic revision --autogenerate` sobre una base vacía, encadenarla antes de `20260522_01`, y retirar `create_all()` de `main.py`.

**Esfuerzo: ~0.5 sesión.** Debe estar hecho **antes** de FASE 2.8, no después.

---

## 🎯 Tanda 1 — Ganancia rápida

| Orden | Trabajo | Esfuerzo | Por qué ahora |
|---|---|---|---|
| 1 | **23-P1** Diagrama de topología (UI) | 1 sesión | 🔥 El backend está 100% hecho y **nadie lo consume**. Máximo retorno del roadmap |
| 2 | **23-P2** Editor de conexiones | 0.5 sesión | Completa el módulo y lo hace usable |
| 3 | `20-P-01`/`20-P-02` CRUD de catálogos en UI | 0.5 sesión | Desbloquea `18-P-02` |
| 4 | `16-P-01` Export del audit log a PDF/XLSX | 0.5 sesión | Requisito del curso de Auditoría y de E5 |

**Total: ~2.5 sesiones.** Al terminar hay una funcionalidad demostrable nueva (topología) y la plataforma queda administrable.

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
| 1 | **28-P1** Base de conocimiento NetDoctor + modo guiado | 2 sesiones | Alto — producto completo por sí solo |
| 2 | **29-P1→P3** Catálogo de equipos + **alerta de EOL** | 3.5 sesiones | 🔥 Motor de oportunidades comerciales |
| 3 | **30-P1** Conector Wazuh + esquema normalizado | 2 sesiones | Alto — amplía el stack open source |
| 4 | **23-P3/P4** Config Visualizer (parser Cisco IOS) | 3 sesiones | Alto — muy demostrable |
| 5 | **30-P3** Informe ejecutivo "SOC as a report" | 1.5 sesiones | Alto — el patrón que define el proyecto |
| 6 | **28-P2** Cobertura Cisco + MikroTik | 1.5 sesiones | Medio |

**Total: ~13.5 sesiones.**

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

## Lo que NO va en NinjaSec

Ideas válidas que pertenecen a un repo de portafolio en GitHub Pages, no a la plataforma:

- Calculadora de VLSM / subnetting
- Simulador visual de STP
- Simulador de ACLs
- Flashcards de troubleshooting para CCNA / Network+
- Visualizador de tabla de enrutamiento
- Analizador de logs syslog client-side
- Consultor de CVEs vía API del NVD

Son excelentes demos de portafolio. Dentro de NinjaSec serían ruido: no tienen cliente, ni rol, ni dato que persistir.

---

## Resumen de esfuerzo

| Tanda | Sesiones | Naturaleza |
|---|---|---|
| 0 — Deuda crítica | ~1 | Obligatoria |
| 0-bis — Deuda de esquema | ~0.5 | Obligatoria **antes de FASE 2.8** |
| 1 — Ganancia rápida | ~2.5 | Alto retorno inmediato |
| 2 — Académica | ~17 | **Deadline duro** |
| 3 — Producto | ~13.5 | Sin fecha |
| 4 — Alto riesgo | — | Condicionada |

**Camino recomendado: 0 → 1 → 2**, intercalando la tanda 3 cuando la 2 esté encaminada.
La **0-bis** puede esperar mientras el entorno se siga recreando, pero **no puede saltarse antes del deploy self-hosted**.

---

## Lo que quedó fuera de las tandas

Los **7 pendientes abiertos de los módulos 01-14** no entran en ninguna tanda: son mejoras de UX de baja consecuencia (`02-P-04`, `02-P-05`, `05-P-05`, `06-P-05`, `09-P-05`) más dos que dependen de decisiones ya listadas (`08-P-02` necesita `@dnd-kit`, `10-P-05` necesita el storage).

Se atienden por oportunidad, cuando se toque el módulo por otra razón. Están en `IMPLEMENTACION/00-BACKLOG-GLOBAL.md` §3.
