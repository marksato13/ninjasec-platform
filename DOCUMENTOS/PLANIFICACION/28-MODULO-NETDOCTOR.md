# Módulo: NetDoctor — Diagnóstico Multi-Vendor

**Ruta prevista:** `/dashboard/netdoctor`
**Acceso:** `super_admin`, `admin`, `collaborator` · `client` (solo el informe resultante)
**Backend previsto:** `modules/netdoctor`

---

## ¿Qué es?

Sistema de diagnóstico guiado de incidencias de red. Convierte una base de conocimiento de problemas comunes en algo accionable: **síntoma → causa probable → comando de verificación por marca → solución → verificación automatizada**.

No compite con SolarWinds ni PRTG. Aquellos monitorean; este **diagnostica y enseña**. Es una base de conocimiento ejecutable.

---

## Problema que resuelve

Un técnico junior o una PYME sin ingeniero senior no sabe diagnosticar rápido: busca en foros dispersos, prueba a ciegas y alarga la caída. NetDoctor centraliza el conocimiento y además **ejecuta** el comando de verificación en el equipo real por SSH.

---

## Entidades

### `nd_problems` — la base de conocimiento
| Campo | Descripción |
|---|---|
| `code` | Correlativo (`ND-007`) |
| `title` | "Configuración incorrecta de VLAN" |
| `category` | `physical` · `switching` · `routing` · `wireless` · `security` · `services` · `performance` |
| `symptoms` | Lista de síntomas observables |
| `common_causes` | Causas frecuentes |
| `severity_default` | Impacto típico |
| `references` | Enlaces a documentación oficial |

### `nd_vendor_procedures` — el diagnóstico por marca
| Campo | Descripción |
|---|---|
| `problem_id` | Problema al que aplica |
| `vendor` | `cisco_ios` · `mikrotik` · `pfsense` · `huawei_vrp` · `ubiquiti` · `fortigate` |
| `diagnostic_command` | `show vlan brief` · `/interface vlan print` |
| `expected_output` | Cómo se ve lo correcto |
| `failure_pattern` | Regex que identifica el fallo en la salida |
| `remediation_command` | Comando de corrección |
| `remediation_notes` | Advertencias antes de aplicar |

### `nd_diagnostics` — la ejecución
| Campo | Descripción |
|---|---|
| `client_id` / `device_id` | Sobre qué se diagnosticó |
| `executed_by` / `executed_at` | Quién y cuándo |
| `mode` | `guided` (asistido) · `automated` (por SSH) |
| `health_score` | Índice 0-100 resultante |
| `raw_outputs` | Salidas capturadas |
| `ticket_id` | Ticket generado, si aplica |

### `nd_diagnostic_results`
Un registro por problema evaluado: `detected` (sí/no), evidencia, recomendación aplicable.

---

## Categorías de la base de conocimiento

Estructura inicial sobre los ~30 problemas de red más frecuentes:

| Categoría | Ejemplos |
|---|---|
| **Físico** | Errores de interfaz, duplex mismatch, cable degradado, SFP incompatible |
| **Switching** | VLAN mal configurada, bucle STP, puerto en modo incorrecto, MAC flapping |
| **Routing** | Ruta faltante, métrica incorrecta, redistribución mal hecha, asimetría |
| **Wireless** | Interferencia de canal, cobertura insuficiente, roaming fallido, PoE insuficiente |
| **Seguridad** | ACL bloqueando tráfico legítimo, NAT mal configurado, regla de firewall en orden incorrecto |
| **Servicios** | Fallo de DHCP, resolución DNS, NTP desincronizado |
| **Rendimiento** | Saturación de enlace, MTU/fragmentación, buffer overrun |

---

## Modos de operación

### Modo guiado (sin acceso al equipo)
Árbol de decisión interactivo: *¿hay conectividad? → ¿responde el gateway? → ¿resuelve DNS?* Al final identifica el problema probable y entrega el comando exacto para la marca del equipo. **Funciona sin credenciales y sin conectividad al dispositivo.**

### Modo automatizado (con SSH)
Se conecta al equipo vía Netmiko/NAPALM, ejecuta los comandos de diagnóstico, parsea la salida contra `failure_pattern` y determina qué problemas están presentes. Requiere credenciales gestionadas por el módulo de Integraciones.

---

## Índice de salud de red

Cada problema detectado resta puntos según severidad. Resultado 0-100 con semáforo, pensado para dirección no técnica:

| Rango | Estado |
|---|---|
| 90-100 | 🟢 Saludable |
| 70-89 | 🟡 Con observaciones |
| 50-69 | 🟠 Requiere atención |
| 0-49 | 🔴 Crítico |

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Consultar base de conocimiento | ✅ | ✅ | ✅ | ❌ |
| Ejecutar diagnóstico guiado | ✅ | ✅ | ✅ | ❌ |
| **Ejecutar diagnóstico automatizado (SSH)** | ✅ | ✅ | ✅¹ | ❌ |
| **Aplicar comando de remediación** | ✅ | ❌ | ❌ | ❌ |
| Editar base de conocimiento | ✅ | ✅ | ❌ | ❌ |
| Ver historial de diagnósticos | ✅ | ✅ | ✅¹ | ✅² |
| Exportar informe | ✅ | ✅ | ✅ | ✅² |

¹ Solo clientes asignados. ² Solo los propios.

---

## Reglas de negocio

1. **El diagnóstico es de solo lectura por defecto.** Solo ejecuta comandos `show` / `print` / `display`. Ningún comando que modifique configuración corre sin acción deliberada de un `super_admin`.
2. Aplicar una remediación exige confirmación explícita, queda en el audit log y **debe tomarse un respaldo de la configuración antes**.
3. Las credenciales SSH nunca se muestran en la UI ni se registran en logs.
4. Un diagnóstico con hallazgos críticos ofrece crear un ticket de soporte con la evidencia adjunta.
5. Los resultados se conservan: la recurrencia es señal de falla de hardware ("este switch acumula errores de interfaz cada semana").
6. La base de conocimiento documenta explícitamente qué versiones de firmware cubre — un comando puede cambiar entre versiones.

---

## Alcance por fases

| Fase | Alcance |
|---|---|
| **P1** | Base de conocimiento (10 problemas más frecuentes) + modo guiado. **Sin SSH.** |
| **P2** | Comandos por vendor para Cisco IOS y MikroTik |
| **P3** | Modo automatizado con Netmiko sobre Cisco IOS + índice de salud |
| **P4** | Parseo de salidas con `failure_pattern` + generación de tickets |
| **P5** | Informe PDF + historial y tendencias por equipo |
| **P6** | Vendors adicionales (pfSense, Huawei, FortiGate) |

**P1 es autosuficiente y ya entrega valor:** una base de conocimiento consultable con comandos por marca sirve al equipo desde el primer día, sin tocar un solo equipo por SSH.

---

## ⚠️ Consideración de seguridad crítica

Este módulo pide credenciales SSH de equipos de red de clientes. Es el componente **más sensible de toda la plataforma**. Requisitos innegociables antes de P3:

- Credenciales cifradas en reposo, nunca en texto plano
- Cuenta de solo lectura en el equipo cuando el vendor lo permita
- Registro completo de cada comando ejecutado, con autor
- Lista blanca de comandos permitidos — nunca ejecución arbitraria
- Timeout y límite de sesiones concurrentes
- Autorización escrita del cliente antes de habilitar el modo automatizado

Si P3 no puede cumplir esto, **se queda en P2**. Una plataforma de seguridad no puede ser el vector de compromiso de la red del cliente.

---

## Conexión con otros módulos

- **05 Dispositivos:** sobre qué se diagnostica
- **04 Integraciones:** de dónde salen las credenciales
- **07 Tickets:** destino de los hallazgos
- **23 Topología:** las alertas de higiene del parser alimentan el diagnóstico
- **29 Catálogo de Equipos:** qué comandos aplican a qué modelo y firmware
