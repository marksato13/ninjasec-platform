# Módulo: Leads / CRM Pipeline

**Ruta:** `/dashboard/leads`
**Acceso:** `super_admin`, `admin`

---

## ¿Qué es?

Sistema CRM de captación y seguimiento comercial. Los leads son prospectos (empresas o personas interesadas en los servicios de NinjaSec) que avanzan por un pipeline visual tipo Kanban hasta convertirse en clientes o descartarse.

---

## Pipeline Kanban — Etapas

```
NUEVO → CONTACTADO → CALIFICADO → PROPUESTA → GANADO ✓
                                             → PERDIDO
```

| Etapa | Color | Descripción |
|-------|-------|-------------|
| `NEW` | 🔵 Azul | Lead recién ingresado, sin contactar |
| `CONTACTED` | 🟣 Morado | Se realizó primer contacto |
| `QUALIFIED` | 🟡 Amarillo | Lead calificado con interés real |
| `PROPOSAL` | 🟠 Naranja | Se envió propuesta comercial |
| `CLOSED_WON` | 🟢 Verde | Deal cerrado — se convierte en cliente |
| `CLOSED_LOST` | 🔴 Rojo | Descartado — no hubo cierre |

---

## Transiciones permitidas

| Desde | Puede ir a |
|-------|-----------|
| NEW | CONTACTED |
| CONTACTED | NEW, QUALIFIED |
| QUALIFIED | CONTACTED, PROPOSAL |
| PROPOSAL | QUALIFIED, CLOSED_WON, CLOSED_LOST |
| CLOSED_WON | — (terminal) |
| CLOSED_LOST | — (terminal) |

---

## Información de un lead

- **Nombre** de la empresa o persona
- **Email** de contacto
- **Teléfono** (opcional)
- **Mensaje / nota inicial**
- **Estado** en el pipeline
- **Fecha de creación**

---

## Funcionalidades

### Vista Kanban
- 6 columnas, una por etapa
- Cards arrastrables (botones de transición de estado)
- Conteo de leads por columna
- Fondo de color suave por etapa

### Acciones por card
- Botones de transición directa (mueve el lead a la etapa siguiente/anterior permitida)
- Modal de detalle con todos los datos
- Edición de información del lead

---

## Acciones disponibles

| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Ver pipeline | ✅ | ✅ |
| Crear lead | ✅ | ✅ |
| Mover entre etapas | ✅ | ✅ |
| Editar lead | ✅ | ✅ |
| Eliminar lead | ✅ | ❌ |

---

## Conversión a cliente

Cuando un lead llega a `CLOSED_WON`, el proceso es:
1. Marcar como CLOSED_WON en el Kanban
2. Ir al módulo de Clientes y crear el cliente
3. El lead queda como registro histórico del origen comercial

> Nota: La conversión automática de lead → cliente está planificada para v0.3.0

---

## Datos técnicos

- Endpoint: `GET /api/v1/leads`
- Actualizar estado: `PATCH /api/v1/leads/{id}`
