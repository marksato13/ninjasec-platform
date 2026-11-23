# Módulo: Integraciones Open Source y Mini-SOAR

**Ruta prevista:** `/dashboard/integrations` (ampliación) · `/dashboard/soar`
**Acceso:** `super_admin`, `admin` · `collaborator` (consulta) · `client` (informes)
**Backend previsto:** ampliación de `modules/integrations` + `modules/soar`

---

## ¿Qué es?

Ampliación del módulo de Integraciones para consumir herramientas open source de seguridad —**Wazuh**, Suricata, OpenVAS, AbuseIPDB— normalizar sus datos a un esquema común y ejecutar respuestas automatizadas simples entre ellas.

Es la materialización del patrón que define el proyecto: **API de herramienta open source → análisis → reporte PDF**, ahora con respuesta automatizada encima.

---

## Problema que resuelve

Cada herramienta open source habla su propio idioma. Una PYME que instala Wazuh, Suricata y pfSense termina con tres consolas que no se hablan, tres formatos de log y ningún analista para correlacionarlos.

Las tres funciones que faltan:
1. **Normalizar** — un esquema común para eventos de todas las fuentes
2. **Correlacionar** — cruzar eventos entre herramientas
3. **Responder** — actuar automáticamente sobre lo detectado

---

## Conectores previstos

| Herramienta | Qué aporta | Prioridad |
|---|---|---|
| **Wazuh** | Eventos HIDS, cumplimiento, detección de vulnerabilidades, FIM | 🔴 P1 |
| **pfSense** | Tráfico, reglas, bloqueos (ya integrado) | ✅ existente |
| **Suricata** | Alertas IDS/IPS de red | 🟠 P2 |
| **OpenVAS / Nessus Essentials** | Escaneo de vulnerabilidades con CVE | 🟠 P2 |
| **AbuseIPDB** | Reputación de IPs (gratuito con límite) | 🟡 P3 |
| **NVD** | Base pública de CVEs | 🟡 P3 |
| **FortiGate** | Consola comercial (ya integrado) | ✅ existente |

---

## Entidades

### `security_events` — el esquema normalizado
Todos los conectores escriben aquí, sin importar su formato de origen.

| Campo | Descripción |
|---|---|
| `client_id` / `integration_id` | Origen |
| `source_tool` | `wazuh` · `suricata` · `pfsense` · `openvas` |
| `event_type` | `intrusion` · `malware` · `policy_violation` · `vulnerability` · `authentication` · `file_integrity` |
| `severity` | Normalizada a la escala propia (`critical` a `info`) |
| `source_ip` / `destination_ip` / `port` | Datos de red |
| `rule_id` / `rule_name` | Regla que disparó |
| `raw_payload` | Evento original, para no perder información |
| `occurred_at` / `ingested_at` | Cuándo ocurrió y cuándo llegó |
| `device_id` | Dispositivo relacionado, si se puede correlacionar |

### `ip_reputation`
Puntuación acumulada por IP: reputación externa (AbuseIPDB) + eventos internos. Base del scoring de riesgo que combate la fatiga de alertas.

| Campo | Descripción |
|---|---|
| `ip_address` / `client_id` | La IP en contexto |
| `abuse_score` | 0-100 de fuente externa |
| `internal_event_count` | Eventos internos asociados |
| `risk_score` | Combinado |
| `is_blocked` / `blocked_at` | Estado de bloqueo |

### `soar_playbooks` y `soar_executions`
| Campo | Descripción |
|---|---|
| `trigger_type` / `trigger_condition` | Qué dispara el playbook |
| `action_type` | `block_ip_pfsense` · `create_ticket` · `send_report` · `notify` |
| `action_params` | Parámetros de la acción |
| `requires_approval` | **Si exige visto bueno humano antes de ejecutar** |
| `is_active` | Habilitado |

---

## Playbooks iniciales

| Playbook | Disparador | Acción |
|---|---|---|
| **Bloqueo por fuerza bruta** | Wazuh detecta N intentos fallidos desde una IP | Bloquear la IP en pfSense vía API |
| **Ticket por evento crítico** | Evento `critical` sin ticket asociado | Crear ticket con la evidencia adjunta |
| **Escalamiento de vulnerabilidad** | OpenVAS reporta CVE crítico en activo `critical` | Crear hallazgo + notificar al responsable |
| **Informe nocturno** | Cron diario | Consolidar métricas y enviar PDF al encargado de TI |

El último es la idea **"SOC as a report"**: la PYME no tiene tiempo de mirar dashboards, pero sí lee un PDF en el correo.

---

## Scoring de riesgo por IP

Combina reputación externa con eventos internos para priorizar qué atender primero. Ataca el problema real de los SOC pequeños: **alert fatigue**. Con 4.000 alertas diarias y una persona, el orden lo es todo.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver eventos normalizados | ✅ | ✅ | ✅¹ | ✅² |
| Configurar conector | ✅ | ✅ | ❌ | ❌ |
| Ejecutar recolección manual | ✅ | ✅ | ✅¹ | ❌ |
| Ver playbooks | ✅ | ✅ | ✅ | ❌ |
| **Crear / editar playbook** | ✅ | ❌ | ❌ | ❌ |
| **Aprobar ejecución pendiente** | ✅ | ✅ | ❌ | ❌ |
| **Bloquear IP manualmente** | ✅ | ✅ | ❌ | ❌ |
| Ver informes | ✅ | ✅ | ✅¹ | ✅² |

¹ Clientes asignados. ² Solo los propios, en vista ejecutiva.

---

## Reglas de negocio

1. **Toda acción automatizada que modifique un firewall exige `requires_approval = true` por defecto.** Desactivarlo es una decisión consciente y documentada por cliente.
2. Un playbook nunca bloquea una IP de la lista blanca del cliente — su propia IP pública, VPN corporativa y rangos de gestión son intocables.
3. `raw_payload` se conserva siempre: normalizar no puede destruir el original.
4. Las credenciales de las herramientas van cifradas y jamás aparecen en la UI ni en logs.
5. Toda ejecución de playbook queda en el audit log con disparador, acción y resultado.
6. Un bloqueo automático es **reversible y con caducidad** — nunca permanente sin revisión humana.
7. Los eventos tienen política de retención configurable: sin ella, la tabla crece sin control.

---

## Alcance por fases

| Fase | Alcance |
|---|---|
| **P1** | Esquema `security_events` + conector Wazuh (lectura) + listado con filtros |
| **P2** | Normalización de severidad + correlación con dispositivos + dashboard de eventos |
| **P3** | Informe ejecutivo PDF con traducción a lenguaje no técnico + envío programado |
| **P4** | Scoring de reputación de IP con AbuseIPDB |
| **P5** | Motor de playbooks con aprobación humana obligatoria |
| **P6** | Puente Wazuh ↔ pfSense (bloqueo automático) |
| **P7** | Conectores Suricata y OpenVAS |

---

## ⚠️ Consideración de seguridad crítica

P6 —bloqueo automático en el firewall del cliente— es la funcionalidad de **mayor riesgo de toda la plataforma**. Una regla mal disparada deja al cliente sin servicio, y una lista blanca mal configurada puede dejarlo fuera de su propia red.

Requisitos innegociables:
- Aprobación humana obligatoria hasta que el playbook acumule historial demostrable
- Lista blanca verificada antes de activar cualquier bloqueo
- Bloqueos con caducidad automática, nunca permanentes
- Botón de reversión inmediata siempre accesible
- Simulación (*dry run*) obligatoria antes de la primera activación real
- Autorización escrita del cliente

**Si estos requisitos no se pueden garantizar, el módulo se queda en P5** (recomendación sin ejecución). Un falso positivo que tumba la red del cliente cuesta más que todo lo que aporta la automatización.

---

## Conexión con otros módulos

- **04 Integraciones:** extiende el modelo de conectores existente
- **06 Revisiones:** los eventos alimentan hallazgos
- **07 Tickets:** destino automático de eventos críticos
- **18 Alertas:** fuente adicional de alertas
- **24 Cumplimiento:** evidencia del control A.8.16 (monitoreo)
- **25 Riesgos:** los eventos recurrentes elevan la probabilidad del riesgo asociado
