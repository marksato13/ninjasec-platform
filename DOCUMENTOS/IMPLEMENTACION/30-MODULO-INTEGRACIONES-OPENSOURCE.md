# Implementación — Módulo Integraciones Open Source y Mini-SOAR

> Basado en: `PLANIFICACION/30-MODULO-INTEGRACIONES-OPENSOURCE.md`
> Creado: 2026-08-05 · Actualizado: 2026-08-09 · **P1 parcial (issue #61)**

---

## 🟡 P1 — Esquema normalizado + conector Wazuh (parcial)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 1 | Modelo `SecurityEvent` (esquema común) | ⏳ | **Decisión deliberada**: no se creó una tabla nueva. Se reutilizó `CollectionSnapshot` (ya existente, ya tiene `raw_payload`/`normalized_payload` por integración+dispositivo) en vez de duplicar infraestructura — ver nota abajo |
| 2 | Migración Alembic + índices por `occurred_at` y `client_id` | ⏳ | No aplica mientras no exista `SecurityEvent` — `CollectionSnapshot` ya tiene `collected_at` e `integration_id` indexado |
| 3 | Campo `raw_payload` — nunca se descarta el original | ✅ | Ya existía en `CollectionSnapshot` para pfSense/FortiGate; el conector Wazuh sigue el mismo contrato |
| 4 | Conector Wazuh (API REST, solo lectura) | 🟡 | **Simulado**, mismo criterio que pfSense/FortiGate (`simulate_connector_test`) — no hay llamada HTTP real a un Wazuh Manager todavía. Ver nota abajo |
| 5 | Credenciales cifradas en reposo | ⏳ | Sigue pendiente — bloqueante para conectar un Wazuh real, no para el modo simulado |
| 6 | `GET /security-events` con filtros | ⏳ | Los eventos siguen accesibles vía `GET /device-configs`-equivalente (`CollectionSnapshot` por integración), no hay endpoint dedicado todavía |
| 7 | Recolección manual bajo demanda | ✅ | `POST /integrations/{id}/collect` ya existe y ya soporta `wazuh` como `connector_type` |
| 8 | Vista de eventos con filtros por fuente, tipo y severidad | ⏳ | |
| 9 | **Política de retención configurable** | ⏳ | 🔴 sin esto la tabla crece sin control |

### Esquema normalizado (ECS-lite) — issue #61, resuelto 2026-08-09

**El problema real que se resolvió**: pfSense y FortiGate ya tenían `normalized_payload`, pero con formatos completamente distintos entre sí (`{"uptime_status":...}` vs `{"threat_events":...}`) — no había ninguna clave en común, imposible correlacionar eventos entre fuentes.

**La solución**: las tres fuentes (pfSense, FortiGate, Wazuh) ahora devuelven la misma envoltura en `normalized_payload`:
```json
{"events": [{"@timestamp": "...", "event": {"category": "...", "severity": "..."}, "source": {"ip": "..."}, "rule": {"description": "..."}, "extra": {...}}]}
```
Subconjunto real de Elastic Common Schema (ECS) — de ahí "ECS-lite". Lo que no encaja en ECS (ej. `active_vpn_sessions`, `rule_id`) queda en `extra`, sin perderse.

**Por qué no se creó `SecurityEvent` todavía**: `CollectionSnapshot` (módulo `collection`, ya existente) ya persiste `raw_payload`/`normalized_payload` por `integration_id`+`device_id`. Crear una tabla `SecurityEvent` que solo re-empaqueta ese mismo JSON en filas individuales es trabajo real, pero no era necesario para resolver el problema de fondo del issue (falta de esquema común). Se deja explícitamente como pendiente (#1/#2/#6/#8 arriba) para cuando haga falta filtrar/consultar eventos individuales por severidad o tipo — hoy el JSON ya trae esa información, solo que no es queryable por SQL.

**Frontend**: `integration-form.tsx` agrega "Wazuh" al selector de `connector_type`; el banner de `/dashboard/integrations` ya no dice "solo pfSense y FortiGate".

**Verificado**: `pytest` completo en verde (175 tests, 1 skip, incluye 4 casos nuevos en `test_integration_connectors.py`: conector alcanzable, conector no soportado, las tres fuentes comparten el mismo esquema, Wazuh genera dispositivo + evento crítico). Smoke test manual end-to-end vía curl: crear integración Wazuh → `POST /collect` → dispositivo `wazuh-manager` creado automáticamente.

## ⏳ P2 — Normalización y correlación

| # | Requisito | Estado |
|---|-----------|--------|
| 10 | Mapeo de severidad Wazuh → escala propia | ⏳ |
| 11 | Correlación evento → `device_id` por IP o hostname | ⏳ |
| 12 | Correlación evento → cliente | ⏳ |
| 13 | Dashboard de eventos con series temporales | ⏳ |
| 14 | Top N reglas disparadas | ⏳ |

## 🟡 P3 — Informe ejecutivo ("SOC as a report") — parcial (issue #63)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 15 | PDF con traducción a lenguaje no técnico | ✅ | `modules/health_score/services/soc_report_pdf.py` — número grande + semáforo + narrativa en español llano, sin jerga técnica |
| 16 | Índice de "salud de seguridad" para gerencia | ✅ | `HealthScoreService.compute()` — parte de 100 y resta puntos por 4 señales reales ya construidas en la plataforma (hallazgos abiertos, hardening incumplido, hosts de alto riesgo, CVEs de alta explotabilidad), cada una con tope de deducción documentado. `GET /health-score?client_id=` + página `/dashboard/soc-report` |
| 17 | Envío programado por correo (cron nocturno) | ⏳ | No implementado — requiere infraestructura de envío de correo, fuera de alcance de esta fase |
| 18 | Consolidación multi-sede en un solo informe | ⏳ | El índice es por cliente, no agrega múltiples sedes en un solo número todavía |
| 19 | Vista para rol `client` | ⏳ | Hoy el endpoint exige rol staff (`super_admin`/`admin`/`collaborator`); una vista de solo lectura para `client` queda pendiente |

### Fórmula del índice (documentada, no una caja negra)

Parte de 100. Cuatro deducciones, cada una con un tope máximo para que ninguna señal por sí sola hunda el score:

| Señal | Peso por severidad | Tope |
|---|---|---|
| Hallazgos de revisiones abiertos (`open`/`in_progress`) | crítico=15, alto=10, medio=5, bajo=2 | 30 |
| Reglas de hardening que fallan (31-P1) | crítico=15, alto=10, medio=5, bajo=2 | 40 |
| Hosts de alto riesgo, `composite_score` ≥ 70 (30-P2/P4) | 5 por host | 20 |
| CVEs con EPSS ≥ 0.5 (32-P1) | 3 por CVE | 10 |

Semáforo: **≥80 Saludable** (verde) · **60-79 Con observaciones** (ámbar) · **<60 Requiere atención** (rojo).

**Verificado**: 204 tests pasan (1 skip, 5 casos nuevos, incluyendo el caso honesto de que un cliente sin ninguna integración configurada arrastra el gap base de hardening — no tener firewall ni SIEM integrado es en sí mismo una brecha real, no un bug del cálculo). Smoke test manual vía `curl` con datos reales de hardening de sesiones anteriores. `npx tsc --noEmit` sin errores; build de producción real confirma la ruta `/dashboard/soc-report` (2.87 kB).

## ✅ P4 — Reputación de IPs — Resuelto 2026-08-09 (issue #62, referido como "30-P2" en ROADMAP.md)

| # | Requisito | Estado | Notas |
|---|-----------|--------|-------|
| 20 | Modelo `IpReputation` | ✅ | `db/models/ip_reputation.py` → `IpReputationCache(ip_address, source, score, category, checked_at)`, único por `(ip_address, source)` |
| 21 | Conector AbuseIPDB (respetando el límite gratuito) | ✅ | Más VirusTotal y GreyNoise (los tres mencionados en la propuesta original) — `services/reputation.py`. Sin API key configurada, degrada a un score simulado determinista (mismo hash → mismo score) en vez de fallar |
| 22 | Cálculo de `risk_score` combinado | ✅ | `composite_score = round(0.6 × externo + 0.4 × interno)`; interno = suma de pesos por severidad de eventos ECS-lite (30-P1) con tope en 100 |
| 23 | Priorización de alertas por score | ✅ | `GET /risk-scoring/hosts?client_id=` devuelve los hosts ordenados descendente por `composite_score`; panel "Prioridad de hosts" en `/dashboard/risks` |
| 24 | Caché para no agotar la cuota de API | ✅ | TTL de 24h por `(ip, source)` en `IpReputationCache` — verificado con test que confirma que una segunda consulta no duplica ni vuelve a llamar a la fuente externa |

**Fuente de datos internos**: reutiliza los eventos ECS-lite de `CollectionSnapshot` (30-P1) — agrupa por `source.ip` y pondera por `event.severity` (crítico=40, alto=25, medio=10, bajo=3, tope 100).

**Verificado**: 180 tests pasan (1 skip, incluye 4 casos nuevos: cálculo combinado, hosts sin IP se ignoran, caché no se duplica, aislamiento entre organizaciones); migración `20260809_09_ip_reputation.py` verificada con `alembic upgrade head` sobre Postgres limpio; smoke test manual vía curl con datos reales de una integración Wazuh; `npx tsc --noEmit` sin errores.

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
