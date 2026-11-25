# Flujo: Proceso de Revisión de Seguridad

---

## Descripción

Proceso de auditoría de seguridad que el equipo Ninja Tech ejecuta en la infraestructura de un cliente. Culmina con un reporte PDF entregado al cliente.

---

## Actores

| Actor | Rol |
|-------|-----|
| Gerente de operaciones (admin) | Agenda y supervisa la revisión |
| Ingeniero de seguridad (collaborator) | Ejecuta la revisión |
| Cliente | Recibe el reporte final |

---

## Flujo completo

```
1. AGENDAR LA REVISIÓN
   │
   Admin en /dashboard/security-reviews → "Nueva revisión"
   - Selecciona cliente
   - Selecciona integración/consola a revisar
   - Asigna técnico responsable
   - Define fecha programada
   - Estado inicial: "scheduled"
   │
   ↓
2. PREPARACIÓN (scheduled)
   │
   Técnico revisa el contexto del cliente:
   - Dispositivos conectados a la consola
   - Revisiones anteriores y sus hallazgos
   - Historial de tickets recientes
   │
   ↓
3. INICIO DE LA REVISIÓN (in_progress)
   │
   Técnico cambia estado a "in_progress"
   Ejecuta el checklist de verificación:
   - Reglas de firewall
   - Logs de acceso
   - Actualizaciones de firmware
   - Configuración de VPN
   - Políticas de contraseñas
   - Segmentación de red
   - Backups
   │
   ↓
4. REGISTRO DE HALLAZGOS
   │
   Por cada vulnerabilidad encontrada:
   - Severidad: critical / high / medium / low / info
   - Título descriptivo
   - Descripción técnica detallada
   - Recomendación de remediación
   - Evidencia (capturas, logs)
   │
   ↓
5. REDACCIÓN DEL RESUMEN EJECUTIVO
   │
   Técnico escribe el resumen para el reporte:
   - Contexto de la revisión
   - Hallazgos principales
   - Riesgo general evaluado
   - Recomendaciones prioritarias
   │
   ↓
6. CIERRE DE LA REVISIÓN (closed)
   │
   Admin o técnico cambia estado a "closed"
   │
   ↓
7. GENERACIÓN Y ENTREGA DEL REPORTE
   │
   Admin genera el PDF desde /dashboard/reports
   - Reporte incluye: resumen ejecutivo, hallazgos por severidad,
     checklist completado, recomendaciones
   - Se sube el PDF al portal del cliente en /portal/documents
   - Cliente puede descargarlo desde su portal
```

---

## Frecuencia recomendada de revisiones

| Tipo de cliente | Frecuencia |
|----------------|------------|
| Crítico (salud, finanzas) | Mensual |
| Estándar | Trimestral |
| Básico | Semestral |

---

## Impacto en el Dashboard

- Los hallazgos `critical` y `high` de revisiones `closed` incrementan el KPI de "Hallazgos críticos abiertos"
- El porcentaje de revisiones ejecutadas sube cuando se cierran revisiones programadas
- Una integración sin revisión en más de 90 días genera alerta automática

---

## Checklist de cierre

- [ ] Todos los ítems del checklist evaluados
- [ ] Hallazgos registrados con severidad y recomendación
- [ ] Resumen ejecutivo redactado
- [ ] Revisión cerrada en el sistema
- [ ] Reporte PDF generado
- [ ] PDF subido al portal del cliente
- [ ] Cliente notificado de la disponibilidad del reporte
