# Flujo: Ciclo de Vida de un Ticket de Soporte

---

## Descripción

Proceso completo de atención desde que el cliente reporta un problema hasta el cierre del ticket.

---

## Actores

| Actor | Rol |
|-------|-----|
| Responsable TI del cliente | Abre el ticket desde el portal |
| Admin NinjaSec | Asigna y supervisa |
| Técnico (collaborator) | Atiende y resuelve |

---

## Flujo completo

```
CLIENTE abre ticket en /portal/tickets
│
│  Datos que ingresa:
│  - Título descriptivo
│  - Descripción detallada del problema
│  - Prioridad: low / medium / high / critical
│
↓
SISTEMA crea ticket con estado "open"
│  - Se genera ID único (#001, #002, ...)
│  - Se registra timestamp de apertura
│  - Inicia el conteo del SLA
│
↓
ADMIN recibe alerta en el dashboard (si es critical)
│  - Ve el nuevo ticket en /dashboard/support-tickets (tab "open")
│  - Asigna técnico responsable
│  - Ticket cambia a estado "in_progress"
│
↓
TÉCNICO atiende el ticket
│  - Revisa el detalle y el historial de eventos
│  - Agrega notas de avance ("Agregar evento")
│  - Si necesita info del cliente → cambia a "pending"
│
↓
[Si se necesita respuesta del cliente]
│  CLIENTE es notificado
│  Al responder o proveer info → técnico vuelve a "in_progress"
│
↓
TÉCNICO aplica solución
│  - Ingresa descripción de la resolución en el campo "Resolución"
│  - Cambia estado a "resolved"
│
↓
CLIENTE confirma la resolución
│  - Si todo está correcto → Admin cierra el ticket ("closed")
│  - Si hay problemas → vuelve a "in_progress"
│
↓
TICKET CERRADO
│  - Se registra timestamp de cierre
│  - Se calcula tiempo total de resolución
│  - Disponible en historial y reportes
```

---

## SLA por prioridad

| Prioridad | SLA | Qué pasa si vence |
|-----------|-----|-------------------|
| critical | 4 horas | Alerta roja en Dashboard, badge "Vencido" |
| high | 8 horas | Alerta en Dashboard |
| medium | 24 horas | Badge naranja en tabla |
| low | 72 horas | Sin alerta proactiva |

---

## Eventos que se registran automáticamente

| Evento | Trigger |
|--------|---------|
| `ticket_opened` | Creación del ticket |
| `status_change` | Cada cambio de estado |
| `assignment` | Al asignar o reasignar técnico |
| `manual_note` | Al usar "Agregar evento" |
| `resolution_added` | Al escribir resolución |

---

## Diagrama de estados

```
         ┌──────────────────────────────┐
         │                              │
  open ──→ in_progress ──→ pending ──→ resolved ──→ closed
   ↑            ↑              │
   └────────────┘              │
                └──────────────┘
                (cliente responde)
```
