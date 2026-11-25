# Módulo: Revisiones de Seguridad

**Ruta:** `/dashboard/security-reviews`
**Acceso:** `super_admin`, `admin`, `collaborator` (solo las asignadas)

---

## ¿Qué es?

Las revisiones de seguridad son auditorías periódicas que el equipo de Ninja Tech realiza sobre la infraestructura de los clientes. Incluyen un checklist de verificación y el registro de hallazgos (vulnerabilidades, configuraciones incorrectas, riesgos).

---

## Estados de una revisión

```
scheduled → in_progress → closed
```

| Estado | Descripción |
|--------|-------------|
| `scheduled` | Revisión programada, aún no iniciada |
| `in_progress` | En ejecución, el técnico está trabajando |
| `closed` | Completada y cerrada con reporte final |

---

## Severidad de hallazgos (findings)

| Nivel | Color | Descripción |
|-------|-------|-------------|
| `critical` | 🔴 Rojo | Vulnerabilidad explotable activamente |
| `high` | 🟠 Naranja | Alto riesgo, requiere acción inmediata |
| `medium` | 🟡 Amarillo | Riesgo moderado, atender en el ciclo normal |
| `low` | 🟢 Verde | Riesgo bajo, mejora recomendada |
| `info` | 🔵 Azul | Informativo, sin riesgo directo |

---

## Estructura de una revisión

- **Datos generales:** Cliente, consola revisada, técnico asignado, fechas
- **Checklist:** Lista de ítems de verificación (cumple / no cumple / N/A)
- **Hallazgos:** Lista de vulnerabilidades encontradas con severidad y recomendación
- **Resumen ejecutivo:** Texto de cierre para el reporte PDF

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator |
|--------|:-----------:|:-----:|:------------:|
| Ver todas las revisiones | ✅ | ✅ | Solo asignadas |
| Crear revisión | ✅ | ✅ | ❌ |
| Editar revisión | ✅ | ✅ | ✅ propias |
| Agregar hallazgos | ✅ | ✅ | ✅ propias |
| Cerrar revisión | ✅ | ✅ | ✅ propias |
| Exportar PDF del reporte | ✅ | ✅ | ✅ |
| Eliminar revisión | ✅ | ❌ | ❌ |

---

## Impacto en Dashboard

Los hallazgos críticos abiertos (revisiones no cerradas con findings críticos) aparecen como KPI en el Dashboard principal y generan alertas.

El porcentaje de revisiones ejecutadas se calcula como:
```
(revisiones "closed" del mes) / (total de revisiones del mes) × 100
```

---

## Datos técnicos

- Endpoint: `GET /api/v1/security-reviews`
- Hallazgos: `GET /api/v1/security-reviews/{id}/findings`
- PDF: `GET /api/v1/reports/security-review/{id}/pdf`
