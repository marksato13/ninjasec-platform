# Módulo: Alertas y Notificaciones

**Ruta:** widget transversal en `/dashboard` (no tiene página propia)
**Acceso:** `super_admin`, `admin`, `collaborator` · el `refresh` es exclusivo de `super_admin`
**Backend:** `modules/alerts` · prefijo `/alerts`

---

## ¿Qué es?

Motor de alertas **derivadas**. No existe una tabla `alerts`: cada alerta se calcula al vuelo cruzando el estado real de integraciones, hallazgos y tickets. Si la condición desaparece, la alerta desaparece sola — no hay que "cerrarla" a mano ni queda basura acumulada.

Resuelve el problema clásico de las bandejas de alertas: alertas zombis que nadie limpia y que terminan generando fatiga.

---

## Tipos de alerta

| Tipo | Severidad | Condición que la dispara |
|---|---|---|
| `license_expired` | 🔴 critical | Integración con `license_expires_at` anterior a hoy |
| `critical_finding_open` | 🔴 critical / 🟡 warning | Hallazgo `critical` o `high` en estado `open` **sin ticket ni recomendación asociada** |
| `ticket_overdue` | 🟡 warning | Ticket `open` o `in_progress` con más de **7 días** desde `opened_at` |

La severidad de `critical_finding_open` es `critical` si el hallazgo es `critical`, y `warning` si es `high`.

### Orden de presentación
Siempre `critical` → `warning` → `info`. El orden lo impone el backend, no la UI.

---

## Umbrales configurados

| Constante | Valor | Significado |
|---|---|---|
| `_OVERDUE_DAYS` | 7 | Días para considerar un ticket vencido |
| `_NO_REVIEW_DAYS` | 30 | Días sin revisión para marcar un dispositivo |
| `_INACTIVE_DEVICE` | `retired`, `inactive` | Estados excluidos del barrido |

---

## Endpoints

### `GET /alerts/active`
Devuelve las alertas vigentes. Admite `client_id` opcional para acotar a un cliente. **Solo lectura, sin efectos secundarios.**

### `POST /alerts/refresh`
Acción en **batch que sí muta datos** — por eso está restringida a `super_admin`:

1. Integraciones con licencia vencida → `status = "risk"`
2. Dispositivos cuya integración no tiene revisión cerrada en los últimos 30 días → `status = "pending_review"`

Devuelve el conteo de registros afectados y **deja constancia en el audit log** con la acción `alerts.refresh`.

---

## Funcionalidades

- Widget de alertas en el dashboard con conteo por severidad
- Filtro por cliente
- Refresco automático cada 60 s vía TanStack Query (toggle "Auto ON/OFF" persistido en `localStorage`)
- Mensajes redactados en español, listos para mostrar sin transformación en la UI

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver alertas activas | ✅ | ✅ | ✅ | ❌ |
| Filtrar por cliente | ✅ | ✅ | ✅ | ❌ |
| Ejecutar refresh en batch | ✅ | ❌ | ❌ | ❌ |

---

## Reglas de negocio

1. **La alerta no se persiste, se deriva.** Corregida la causa, deja de aparecer.
2. Un hallazgo crítico con ticket **o** con recomendación ya no alerta — se asume gestionado.
3. `refresh` degrada el estado de integraciones y dispositivos: es una operación con consecuencias visibles, y por eso queda auditada.
4. El cliente **nunca** ve alertas internas: son de operación, no de cara al cliente.
5. Los umbrales están hardcodeados como constantes del módulo — parametrizarlos por organización es una mejora futura.

---

## Limitación conocida

El frontend hace **polling cada 60 s**, no hay push real. Un WebSocket eliminaría la latencia y la carga de consultas repetidas. Registrado como pendiente `02-P-05`.
