# Flujo: De Lead a Cliente (Pipeline Comercial)

---

## Descripción

Recorrido completo de un prospecto desde el primer contacto hasta convertirse en cliente activo en la plataforma.

---

## Actores

| Actor | Rol |
|-------|-----|
| Prospecto (empresa interesada) | Se contacta con NinjaSec |
| Responsable comercial (admin) | Gestiona el pipeline |
| Gerente de operaciones (admin) | Da de alta al cliente ganado |

---

## Pipeline completo

```
[NUEVO LEAD]
│
│  Orígenes del lead:
│  - Formulario de contacto en la web (/ o /contacto)
│  - Referencia de cliente existente
│  - Prospección activa del equipo
│  - Evento o conferencia de seguridad
│
↓
ETAPA 1: NEW (Nuevo)
│  - Se crea el lead en /dashboard/leads
│  - Datos: nombre empresa, email, teléfono, mensaje inicial
│  - Asignado a responsable comercial
│
↓
ETAPA 2: CONTACTED (Contactado)
│  - Se realizó el primer contacto (email, llamada, reunión)
│  - Se registra nota de la conversación
│  - Botón "Mover a CONTACTED"
│
↓
ETAPA 3: QUALIFIED (Calificado)
│  - El prospecto tiene interés real y presupuesto
│  - Se validó que NinjaSec puede atender su necesidad
│  - Criterios de calificación:
│    ✓ Tiene infraestructura que monitorear
│    ✓ Tiene presupuesto aprobado o en evaluación
│    ✓ Hay tomador de decisión identificado
│    ✓ Hay necesidad urgente o planificada
│
↓
ETAPA 4: PROPOSAL (Propuesta)
│  - Se envió propuesta comercial formal
│  - Incluye: alcance, servicios, precios, SLAs, condiciones
│  - Lead está evaluando la propuesta
│
↓
           ┌─────────────────┐
           │                 │
    CLOSED_WON         CLOSED_LOST
    (Ganado ✓)         (Perdido)
           │                 │
           ↓                 ↓
    ALTA EN SISTEMA    Archivar lead con
                       motivo de pérdida

```

---

## Proceso después de CLOSED_WON

```
1. Marcar lead como CLOSED_WON en el Kanban

2. Crear cliente en /dashboard/clients
   - Usar los datos del lead como base
   
3. Configurar integraciones del cliente nuevo
   (ver Flujo: Onboarding de Cliente)

4. Crear usuario portal para el cliente

5. Agendar la primera revisión de seguridad

6. El lead queda como registro histórico
   del origen del cliente
```

---

## Motivos comunes de CLOSED_LOST

- Precio fuera de presupuesto
- Eligieron a la competencia
- Proyecto postergado o cancelado
- Sin toma de decisión interna
- No cumplen requisitos mínimos

---

## Métricas del pipeline (para seguimiento)

| Métrica | Cómo medirla |
|---------|-------------|
| Tasa de conversión | CLOSED_WON / total leads × 100 |
| Tiempo promedio en pipeline | Días de NEW a CLOSED |
| Leads por etapa | Conteo en cada columna del Kanban |
| Leads ganados este mes | CLOSED_WON con fecha del mes actual |

---

## Notas importantes

- Un lead puede retroceder entre etapas (ej: QUALIFIED → CONTACTED si pierde interés temporalmente)
- No se puede ir directamente de CONTACTED a PROPOSAL (debe calificarse primero)
- Los leads CLOSED_WON y CLOSED_LOST son terminales — no se pueden mover
- Para reabrir un lead perdido, crear uno nuevo con nota de referencia al anterior
