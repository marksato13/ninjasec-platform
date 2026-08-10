# Implementación — Módulo NetDoctor

> Basado en: `PLANIFICACION/28-MODULO-NETDOCTOR.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-10 · **P1 mayormente resuelto (issue #60)**

---

## 🟡 P1 — Base de conocimiento + modo guiado (sin SSH)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `NdProblem` con síntomas y causas | ✅ | Implementado como `NetdoctorIssue` (`db/models/netdoctor.py`) — mismo propósito, nombre distinto |
| 2 | Modelo `NdVendorProcedure` | 🟡 | **Decisión deliberada**: no se creó una tabla separada. Los comandos por vendor viven como columna `diagnostic_commands` (JSON) en el mismo `NetdoctorIssue` — cubre el mismo caso de uso (comando por marca) sin la complejidad de un join adicional. Si en el futuro se necesita `expected_output`/`failure_pattern` por vendor (P4), sí hará falta la tabla separada |
| 3 | Migración Alembic | ✅ | `20260809_12_netdoctor_issues.py` |
| 4 | **Seed de los 10 problemas más frecuentes** | ✅ | 14 problemas reales (supera el mínimo), cubriendo direccionamiento, conectividad, rendimiento, servicios, VLAN, físico y seguridad |
| 5 | 7 categorías | 🟡 | 7 categorías reales pero con nombres adaptados a lo que el catálogo cubre: *Direccionamiento, Conectividad, Rendimiento, Servicios, VLAN, Físico, Seguridad* — sin categoría `wireless` dedicada (no hay problemas inalámbricos en el seed inicial) |
| 6 | `GET /netdoctor/problems` con filtros | ✅ | Como `GET /netdoctor/issues?category=&vendor=` |
| 7 | Página `/dashboard/netdoctor` — base consultable | ✅ | |
| 8 | Buscador por síntoma | ⏳ | Solo hay filtro por categoría, no búsqueda de texto libre sobre síntomas — pendiente |
| 9 | Ficha del problema con comandos por marca | ✅ | |
| 10 | Árbol de decisión interactivo (modo guiado) | ✅ | 27 nodos, JSON declarativo (`guided_tree.py`), sin IA/ML. Verificado que cubre exactamente los 14 códigos del catálogo sin referencias rotas (test dedicado) |
| 11 | Cheat sheet comparativo multi-vendor | ⏳ | **Fuera de alcance deliberado**: ya se documentó en `ROADMAP.md` § "Lo que NO va en NinjaSec" que un cheat sheet genérico multi-vendor sin cliente/rol/dato asociado pertenece a un repo de portafolio aparte, no a la plataforma. La ficha de cada problema sí muestra el comando del vendor seleccionado (item 9), que cubre el caso de uso real (un ingeniero atendiendo un cliente concreto) |

### Verificado (2026-08-10)

- 199 tests pasan (1 skip, 6 casos nuevos: catálogo de 14 problemas con comandos para los 4 vendors, filtro por categoría, obtener por código, código inexistente → 404, y **dos** tests que verifican la integridad del árbol guiado — vía HTTP y directo sobre la estructura Python — confirmando que cada hoja apunta a un código real del catálogo y cada "next" a un nodo real, sin referencias rotas).
- Migración verificada con `alembic upgrade head` sobre Postgres 16 limpio.
- Smoke test manual vía `curl`: catálogo completo, filtro por vendor, ficha individual, recorrido del árbol guiado paso a paso.
- `npx tsc --noEmit` sin errores; build de producción real confirma que `/dashboard/netdoctor` compila (2.32 kB).

## ⏳ P2 — Cobertura por vendor

| # | Requisito | Estado |
|---|-----------|--------|
| 12 | Procedimientos Cisco IOS para los 10 problemas | ⏳ |
| 13 | Procedimientos MikroTik RouterOS | ⏳ |
| 14 | Documentar versiones de firmware cubiertas | ⏳ |
| 15 | Ampliar a 30 problemas | ⏳ |
| 16 | Enlaces a documentación oficial por problema | ⏳ |

## ⏳ P3 — Modo automatizado (SSH) 🔴

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 17 | Modelo `NdDiagnostic` y `NdDiagnosticResult` | ⏳ | |
| 18 | Integrar Netmiko en el backend | ⏳ | |
| 19 | **Lista blanca de comandos permitidos** | ⏳ 🔴 | Nunca ejecución arbitraria |
| 20 | **Credenciales cifradas en reposo** | ⏳ 🔴 | |
| 21 | **Registro de cada comando ejecutado con autor** | ⏳ 🔴 | |
| 22 | Timeout y límite de sesiones concurrentes | ⏳ 🔴 | |
| 23 | Solo comandos de lectura por defecto | ⏳ 🔴 | `show` / `print` / `display` |
| 24 | Cálculo del índice de salud 0-100 | ⏳ | |
| 25 | Semáforo por rango | ⏳ | |

## ⏳ P4 — Parseo y tickets

| # | Requisito | Estado |
|---|-----------|--------|
| 26 | Motor de `failure_pattern` (regex sobre la salida) | ⏳ |
| 27 | Detección automática de problemas presentes | ⏳ |
| 28 | Creación de ticket con evidencia adjunta | ⏳ |
| 29 | Aplicar remediación: solo super_admin + confirmación + **respaldo previo** | ⏳ 🔴 |

## ⏳ P5 — Informes e historial

| # | Requisito | Estado |
|---|-----------|--------|
| 30 | Informe PDF del diagnóstico | ⏳ |
| 31 | Historial por dispositivo | ⏳ |
| 32 | Tendencias y detección de recurrencia | ⏳ |
| 33 | Vista para rol `client` (solo informe) | ⏳ |

## ⏳ P6 — Vendors adicionales

| # | Requisito | Estado |
|---|-----------|--------|
| 34 | pfSense | ⏳ |
| 35 | Huawei VRP | ⏳ |
| 36 | FortiGate | ⏳ |
| 37 | Ubiquiti EdgeSwitch | ⏳ |

---

## Dependencias

| Depende de | Estado |
|---|---|
| 05 Dispositivos | ✅ |
| 04 Integraciones (credenciales) | ✅ para P3 |
| 07 Tickets | ✅ para P4 |
| 29 Catálogo de Equipos | ⏳ opcional (qué comandos por modelo) |

---

## Estimación

| Fase | Esfuerzo | Riesgo |
|---|---|---|
| P1 | 2 sesiones | 🟢 Bajo — todo es datos y UI |
| P2 | 1.5 sesiones | 🟢 Bajo |
| P3 | 2.5 sesiones | 🔴 **Alto — superficie de seguridad** |
| P4 | 2 sesiones | 🟠 Medio |
| P5 | 1 sesión | 🟢 Bajo |
| P6 | 1.5 sesiones | 🟢 Bajo |

---

## ⚠️ Puerta de seguridad antes de P3

**P3 no arranca hasta que estén los 6 requisitos marcados 🔴.** Este módulo pide credenciales SSH de equipos de red de clientes: es la mayor superficie de ataque de toda la plataforma.

Requisitos previos innegociables:
1. Credenciales cifradas en reposo — nunca texto plano
2. Cuenta de solo lectura en el equipo cuando el vendor lo permita
3. Lista blanca de comandos — jamás ejecución arbitraria
4. Registro completo de comandos con autor
5. Timeout y límite de sesiones concurrentes
6. **Autorización escrita del cliente**

**Si no se pueden garantizar, el módulo se queda en P2 y sigue siendo útil.** Una plataforma de seguridad no puede convertirse en el vector de compromiso de la red que protege.

---

## Nota de alcance

P1 + P2 forman un **producto completo por sí solos**: una base de conocimiento de troubleshooting multi-vendor, consultable, con árbol de diagnóstico guiado. Sirve al equipo desde el primer día sin tocar un solo equipo por SSH, y es lo que hace este módulo genuinamente único frente a los NMS comerciales — ellos monitorean, este enseña a diagnosticar.
