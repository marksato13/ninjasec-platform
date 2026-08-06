# Implementación — Módulo NetDoctor

> Basado en: `PLANIFICACION/28-MODULO-NETDOCTOR.md`
> Creado: 2026-08-05 · **Estado: no iniciado**

---

## ⏳ P1 — Base de conocimiento + modo guiado (sin SSH)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `NdProblem` con síntomas y causas | ⏳ | |
| 2 | Modelo `NdVendorProcedure` | ⏳ | |
| 3 | Migración Alembic | ⏳ | |
| 4 | **Seed de los 10 problemas más frecuentes** | ⏳ | JSON estructurado |
| 5 | 7 categorías (físico, switching, routing, wireless, seguridad, servicios, rendimiento) | ⏳ | |
| 6 | `GET /netdoctor/problems` con filtros | ⏳ | |
| 7 | Página `/dashboard/netdoctor` — base consultable | ⏳ | |
| 8 | Buscador por síntoma | ⏳ | |
| 9 | Ficha del problema con comandos por marca | ⏳ | |
| 10 | Árbol de decisión interactivo (modo guiado) | ⏳ | Sin credenciales ni conectividad |
| 11 | Cheat sheet comparativo multi-vendor | ⏳ | El mismo diagnóstico en cada marca |

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
