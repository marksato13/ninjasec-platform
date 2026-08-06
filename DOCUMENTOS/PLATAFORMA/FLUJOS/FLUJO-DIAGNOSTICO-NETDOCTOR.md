# Flujo: Diagnóstico de Incidencia de Red (NetDoctor)

---

## Descripción

Proceso completo desde que el cliente reporta un problema de red hasta que se cierra con evidencia documentada. Cruza cinco módulos y convierte un "no me anda el internet" en un diagnóstico técnico con evidencia y remediación trazable.

**Estado:** flujo objetivo — depende de [[28-MODULO-NETDOCTOR]], aún no implementado.

---

## Actores

| Actor | Rol |
|-------|-----|
| Usuario del cliente | Reporta el síntoma |
| Técnico de soporte (collaborator) | Ejecuta el diagnóstico |
| Gerente de operaciones (admin) | Supervisa y prioriza |
| Super admin | Único que puede aplicar remediación automatizada |

---

## Flujo completo

```
1. REPORTE DEL SÍNTOMA
   │
   Cliente en /portal/support → "Nuevo ticket"
   - Describe el síntoma en lenguaje no técnico
   - Sede afectada
   - Estado inicial: "open"
   │
   ↓
2. TRIAJE
   │
   Técnico abre el ticket y consulta el inventario del cliente:
   - Dispositivos de la sede afectada
   - Topología: qué depende de qué (módulo 23)
   - Diagnósticos anteriores del mismo equipo
   │
   ↓
3. DIAGNÓSTICO GUIADO  (modo sin credenciales)
   │
   /dashboard/netdoctor → árbol de decisión
   - ¿Hay conectividad física?      → sí/no
   - ¿Responde el gateway?          → sí/no
   - ¿Resuelve DNS?                 → sí/no
   │
   NetDoctor propone los problemas candidatos ordenados
   por probabilidad y entrega el comando exacto
   para la marca del equipo afectado.
   │
   ↓
4a. VERIFICACIÓN MANUAL          4b. DIAGNÓSTICO AUTOMATIZADO
   │                                 │
   Técnico ejecuta el comando        NetDoctor se conecta por SSH,
   en el equipo y pega la salida     ejecuta los comandos de la lista
   en la plataforma                  blanca y parsea la salida
   │                                 │
   └─────────────┬───────────────────┘
                 ↓
5. RESULTADO DEL DIAGNÓSTICO
   │
   - Problemas detectados con evidencia
   - Índice de salud de red 0-100
   - Recomendación de remediación por problema
   │
   ↓
6. REMEDIACIÓN
   │
   ┌──────────────────┴──────────────────┐
   │                                      │
 MANUAL                            AUTOMATIZADA (solo super_admin)
   │                                      │
 Técnico aplica el comando          1. Respaldo de configuración
 y registra el resultado            2. Confirmación explícita
   │                                3. Ejecución + audit log
   │                                4. Verificación posterior
   └──────────────────┬──────────────────┘
                      ↓
7. CIERRE DEL TICKET
   │
   - Diagnóstico adjunto como evidencia
   - Estado del ticket: "resolved"
   - Informe PDF disponible para el cliente
   │
   ↓
8. SEGUIMIENTO
   │
   - El diagnóstico queda en el historial del dispositivo
   - Si el mismo problema reaparece 3 veces → señal de falla de hardware
   - Recurrencia crítica → candidato a riesgo en el módulo 25
```

---

## Módulos que intervienen

| Paso | Módulo |
|---|---|
| 1, 7 | **07 — Tickets de Soporte** |
| 2 | **05 — Dispositivos** · **23 — Topología** |
| 3, 4, 5 | **28 — NetDoctor** |
| 4b, 6 | **04 — Integraciones** (credenciales) |
| 6 | **16 — Auditoría** (registro de comandos) |
| 8 | **25 — Riesgos** (recurrencia) · **29 — Catálogo** (EOL del modelo) |

---

## Reglas críticas del flujo

1. **El paso 3 funciona siempre**, incluso sin credenciales ni conectividad al equipo. Es el camino por defecto.
2. El paso 4b solo se habilita con autorización escrita del cliente.
3. El paso 6 automatizado **exige respaldo previo de la configuración**. Sin respaldo, no se ejecuta.
4. Solo `super_admin` aplica remediación automatizada; el técnico propone, no ejecuta.
5. Todo comando ejecutado sobre un equipo del cliente queda en el audit log con autor, timestamp y salida.
6. Si el diagnóstico detecta un problema crítico y el ticket no existe, se ofrece crearlo automáticamente.

---

## Valor del flujo

Convierte tres cosas que hoy se pierden:

| Hoy | Con el flujo |
|---|---|
| El conocimiento vive en la cabeza del técnico senior | Queda en la base de conocimiento, reutilizable |
| El diagnóstico no deja rastro | Queda como evidencia adjunta al ticket |
| La recurrencia no se detecta | El historial la hace visible y accionable |
