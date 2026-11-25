# Flujo: Ciclo de Cumplimiento y Auditoría (SGSI)

---

## Descripción

Ciclo completo de gestión de seguridad de la información: desde el inventario de activos hasta el informe de auditoría que verifica que los controles funcionan. Es el flujo que une los módulos 24, 25 y 26 con los datos que la plataforma ya tiene.

**Estado:** flujo objetivo — depende de los módulos 24, 25 y 26, aún no implementados.

---

## Actores

| Actor | Rol |
|-------|-----|
| Cliente (dirección) | Aprueba la aceptación de riesgos y responde a hallazgos |
| Responsable de seguridad (admin) | Gestiona el SGSI y el tratamiento de riesgos |
| Analista (collaborator) | Identifica riesgos y recolecta evidencia |
| Auditor líder (collaborator/admin) | Ejecuta la auditoría y emite la opinión |

---

## Flujo completo

```
1. INVENTARIO DE ACTIVOS
   │
   Módulo 05 — Dispositivos (ya operativo)
   - Cada activo con criticality y data_classification
   - Responsable asignado (responsible_user_id)
   - Topología documentada (módulo 23)
   │
   → Evidencia automática del control A.5.9
   │
   ↓
2. VALORACIÓN DE ACTIVOS
   │
   Módulo 25 — Riesgos
   - Valoración CIA (confidencialidad, integridad, disponibilidad) 1-5
   - business_value = máx(C, I, A)
   - Activos intangibles agregados a mano (procesos, información, personas)
   │
   ↓
3. IDENTIFICACIÓN DE RIESGOS
   │
   ┌────────────────┴────────────────┐
   │                                  │
 MANUAL                        AUTOMÁTICA
   │                                  │
 Analista declara            - Hallazgo critical → riesgo candidato
 activo→amenaza→             - Licencia vencida → "software sin soporte"
 vulnerabilidad              - Puerto de gestión sin ACL → exposición
   └────────────────┬────────────────┘
                    ↓
4. VALORACIÓN DEL RIESGO
   │
   probabilidad (1-5) × impacto (1-5) = inherent_score (1-25)
   Posicionamiento en el mapa de calor
   │
   ↓
5. TRATAMIENTO
   │
   ┌──────────┬──────────┬──────────┬──────────┐
 Mitigar   Transferir   Evitar     Aceptar
   │          │          │            │
 Aplicar   Contratar  Eliminar   Decisión de dirección:
 controles seguro     el activo  justificación obligatoria
 del SGSI                        + audit log + rol admin+
   └──────────┴──────────┴──────────┴──────────┘
                    ↓
6. IMPLEMENTACIÓN DE CONTROLES
   │
   Módulo 24 — Cumplimiento
   - Control pasa a implementation_status = implemented
   - Nivel de madurez 0-5
   - Responsable y fecha comprometida
   │
   ⚠️ Sin evidencia asociada → se marca "no verificado"
   │
   ↓
7. RECOLECCIÓN DE EVIDENCIA
   │
   ┌──────────────────┴──────────────────┐
 DERIVADA (automática)              MANUAL
   │                                     │
 Se recalcula desde:                Documento adjunto
 - Dispositivos  → A.5.9/A.5.10     desde módulo 19
 - Audit log     → A.8.15
 - Revisiones    → A.8.8
 - Tickets       → A.5.24
 - Alertas       → A.8.16
 - Topología     → A.8.9
   └──────────────────┬──────────────────┘
                      ↓
8. RIESGO RESIDUAL
   │
   Recalculado tras los controles implementados
   ⚠️ residual nunca puede superar al inherente
   │
   Si residual > umbral de aceptación del cliente
   → vuelve al paso 5
   │
   ↓
9. AUDITORÍA
   │
   Módulo 26 — Auditorías COBIT / ISO 19011
   - Plan de auditoría (objetivo, alcance, criterios, equipo)
   - Programa de trabajo con pruebas por objetivo COBIT
   - Verificación de independencia del auditor
   │
   ↓
10. HALLAZGOS
   │
   Cada hallazgo con los 5 atributos ISO 19011:
   condición · criterio · causa · efecto · recomendación
   │
   Respuesta de la dirección + plan de acción + responsable + fecha
   │
   ↓
11. INFORME Y OPINIÓN
   │
   - Solo si todas las pruebas tienen resultado
   - Opinión emitida por el auditor líder
   - El cliente lo ve solo cuando status = closed
   │
   ↓
12. SEGUIMIENTO
   │
   - Auditoría follow_up verifica el cierre de hallazgos
   - Hallazgo accepted_risk → enlaza al riesgo aceptado (paso 5)
   - Comparativa de madurez entre auditorías
   │
   └──────→ vuelve al paso 3 (ciclo de mejora continua)
```

---

## Módulos que intervienen

| Paso | Módulo |
|---|---|
| 1 | **05 Dispositivos** · **23 Topología** |
| 2-5, 8 | **25 Riesgos** |
| 6-7 | **24 Cumplimiento** |
| 7 | **16 Auditoría** · **06 Revisiones** · **07 Tickets** · **18 Alertas** · **19 Documentos** |
| 9-12 | **26 Auditorías COBIT** |

---

## Reglas críticas del flujo

1. **Aceptar un riesgo es decisión de dirección**: rol admin o superior, justificación obligatoria, queda en el audit log.
2. Un control `implemented` sin evidencia **no cuenta** como cumplido.
3. La evidencia derivada se recalcula: si el inventario se degrada, el cumplimiento baja solo.
4. El riesgo residual nunca puede superar al inherente — es error de datos.
5. Un auditor no puede auditar un cliente donde figura como responsable operativo.
6. Un hallazgo sin los 5 atributos no entra al informe final.
7. El ciclo **no termina**: el paso 12 realimenta al 3.

---

## Por qué este flujo es el diferencial de Ninja Tech

Un SGSI llevado en Excel muere a los tres meses porque **mantenerlo actualizado es trabajo manual puro**. Aquí, siete de los diez controles clave se evidencian solos desde datos que la plataforma ya captura para operar.

El cliente no paga por un SGSI: paga por operar su infraestructura. El cumplimiento sale como subproducto.

---

## 🎓 Cobertura académica del flujo

| Tramo del flujo | Curso / Entregable |
|---|---|
| Pasos 1-2 | Arquitectura Empresarial — capa tecnológica (módulo 27) |
| Pasos 3-8 | Seguridad de la Información — SGSI ISO 27001/27005 · E5 (CE032) |
| Pasos 9-12 | Auditoría de Sistemas — Plan (25%) + Informe (30%) |

**Un solo caso organizacional recorre los tres cursos**, que es exactamente la estrategia de caso único ya definida para el ciclo 10.
