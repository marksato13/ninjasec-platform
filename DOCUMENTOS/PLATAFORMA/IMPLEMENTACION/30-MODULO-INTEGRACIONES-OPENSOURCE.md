# Implementación — Módulo Integraciones Open Source y Mini-SOAR

> Basado en: `PLANIFICACION/30-MODULO-INTEGRACIONES-OPENSOURCE.md`
> Creado: 2026-08-05 · **Estado: no iniciado**

---

## ⏳ P1 — Esquema normalizado + conector Wazuh

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `SecurityEvent` (esquema común) | ⏳ | |
| 2 | Migración Alembic + índices por `occurred_at` y `client_id` | ⏳ | |
| 3 | Campo `raw_payload` — nunca se descarta el original | ⏳ | 🔴 |
| 4 | Conector Wazuh (API REST, solo lectura) | ⏳ | |
| 5 | Credenciales cifradas en reposo | ⏳ | 🔴 |
| 6 | `GET /security-events` con filtros | ⏳ | |
| 7 | Recolección manual bajo demanda | ⏳ | |
| 8 | Vista de eventos con filtros por fuente, tipo y severidad | ⏳ | |
| 9 | **Política de retención configurable** | ⏳ | 🔴 sin esto la tabla crece sin control |

## ⏳ P2 — Normalización y correlación

| # | Requisito | Estado |
|---|-----------|--------|
| 10 | Mapeo de severidad Wazuh → escala propia | ⏳ |
| 11 | Correlación evento → `device_id` por IP o hostname | ⏳ |
| 12 | Correlación evento → cliente | ⏳ |
| 13 | Dashboard de eventos con series temporales | ⏳ |
| 14 | Top N reglas disparadas | ⏳ |

## ⏳ P3 — Informe ejecutivo ("SOC as a report")

| # | Requisito | Estado |
|---|-----------|--------|
| 15 | PDF con traducción a lenguaje no técnico | ⏳ |
| 16 | Índice de "salud de seguridad" para gerencia | ⏳ |
| 17 | Envío programado por correo (cron nocturno) | ⏳ |
| 18 | Consolidación multi-sede en un solo informe | ⏳ |
| 19 | Vista para rol `client` | ⏳ |

## ⏳ P4 — Reputación de IPs

| # | Requisito | Estado |
|---|-----------|--------|
| 20 | Modelo `IpReputation` | ⏳ |
| 21 | Conector AbuseIPDB (respetando el límite gratuito) | ⏳ |
| 22 | Cálculo de `risk_score` combinado | ⏳ |
| 23 | Priorización de alertas por score | ⏳ |
| 24 | Caché para no agotar la cuota de API | ⏳ |

## ⏳ P5 — Motor de playbooks (sin ejecución automática)

| # | Requisito | Estado |
|---|-----------|--------|
| 25 | Modelos `SoarPlaybook` y `SoarExecution` | ⏳ |
| 26 | **`requires_approval = true` por defecto** | ⏳ 🔴 |
| 27 | Playbook "ticket por evento crítico" | ⏳ |
| 28 | Playbook "escalamiento de vulnerabilidad" | ⏳ |
| 29 | Bandeja de ejecuciones pendientes de aprobación | ⏳ |
| 30 | Registro completo en audit log | ⏳ 🔴 |
| 31 | **Modo simulación (dry run)** | ⏳ 🔴 |

## ⏳ P6 — Puente Wazuh ↔ pfSense 🔴

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 32 | Acción `block_ip_pfsense` vía API | ⏳ | 🔴 |
| 33 | **Lista blanca verificada por cliente** | ⏳ 🔴 | IP pública, VPN, rangos de gestión |
| 34 | **Bloqueos con caducidad automática** | ⏳ 🔴 | Nunca permanentes |
| 35 | **Botón de reversión inmediata** | ⏳ 🔴 | Siempre accesible |
| 36 | Aprobación humana obligatoria hasta acumular historial | ⏳ 🔴 | |
| 37 | Autorización escrita del cliente | ⏳ 🔴 | |

## ⏳ P7 — Conectores adicionales

| # | Requisito | Estado |
|---|-----------|--------|
| 38 | Suricata (alertas IDS/IPS) | ⏳ |
| 39 | OpenVAS / Nessus Essentials (CVE) | ⏳ |
| 40 | NVD (base pública de CVEs) | ⏳ |

---

## Dependencias

| Depende de | Estado |
|---|---|
| 04 Integraciones | ✅ — se extiende su modelo |
| 07 Tickets | ✅ — destino de eventos críticos |
| 18 Alertas | ✅ — fuente adicional |
| 24 Cumplimiento | ⏳ — evidencia A.8.16 |
| 25 Riesgos | ⏳ — eventos recurrentes elevan probabilidad |

---

## Estimación

| Fase | Esfuerzo | Riesgo |
|---|---|---|
| P1 | 2 sesiones | 🟢 Bajo |
| P2 | 1.5 sesiones | 🟢 Bajo |
| P3 | 1.5 sesiones | 🟢 Bajo |
| P4 | 1 sesión | 🟢 Bajo |
| P5 | 2 sesiones | 🟠 Medio |
| P6 | 2 sesiones | 🔴 **Muy alto** |
| P7 | 2 sesiones | 🟢 Bajo |

---

## ⚠️ Puerta de seguridad antes de P6

**P6 es la funcionalidad de mayor riesgo de toda la plataforma.** Una regla mal disparada deja al cliente sin servicio; una lista blanca mal configurada lo deja fuera de su propia red.

Los 6 requisitos marcados 🔴 en P6 son **innegociables**. Si no se pueden garantizar, **el módulo se queda en P5** — recomendación sin ejecución — y sigue aportando casi todo el valor.

Un falso positivo que tumba la red del cliente cuesta más que todo lo que aporta la automatización.

---

## Sinergia con el lab de deploy

Este módulo conecta directamente con el trabajo de infraestructura ya en curso:

| Lab | Aporte al módulo |
|---|---|
| FASE 2.6 — Suricata IDS/IPS + DVWA | Genera eventos reales para probar el conector Suricata (P7) |
| pfSense operativo con API | Entorno de pruebas para P6 sin tocar un cliente real |
| VM `ninjasec-web` con Docker | Puede alojar el Wazuh manager del laboratorio |

**El lab es el mejor entorno de pruebas posible para este módulo**, y a la vez este módulo le da un propósito de producto al lab. Cierra el círculo entre el trabajo de infraestructura y la plataforma.
