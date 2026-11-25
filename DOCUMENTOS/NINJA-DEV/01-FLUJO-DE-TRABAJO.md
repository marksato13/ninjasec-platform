# Flujo de trabajo: de la solicitud a la entrega

**Roles:** responsable comercial (RC) recibe y negocia; líder de proyecto (LP) coordina alcance, calendario y cliente; líder técnico (LT) diseña y revisa; desarrollador (DEV) implementa y prueba; responsable de calidad (QA) verifica; cliente responsable (CL) decide prioridades y acepta. Una persona puede cubrir varios roles; el LP deja el nombre de cada responsable por escrito.

| Paso y salida | Responsable · participantes | Acción ejecutable | Puerta para avanzar |
| --- | --- | --- | --- |
| 1. Solicitud → ficha de oportunidad | RC · CL | Registrar problema, contacto, objetivo, fecha deseada, presupuesto orientativo y restricciones. Confirmar recepción y próxima reunión. | CL identifica quién decide y quién usará el producto. |
| 2. Descubrimiento → resumen de necesidades | LP · RC, CL, usuarios | Entrevistar a usuarios; dibujar flujo actual; pedir ejemplos anonimizados; listar integraciones, datos, volumen, restricciones legales y criterio de éxito medible. | CL confirma problema, prioridades y supuestos pendientes. |
| 3. Propuesta → propuesta técnica, estimación y SOW preliminar | LP · LT, RC | Comparar solución mínima y alternativas; estimar con [07](07-ESTIMACION-Y-COSTOS.md); separar entregables, exclusiones, dependencias, hitos y soporte. | RC envía versión fechada; CL aprueba alcance y condiciones comerciales por canal trazable. |
| 4. Kickoff → acta y plan inicial | LP · todos | Confirmar responsables, canales, accesos autorizados, datos de prueba, calendario de sprints y forma de aprobar cambios. Usar [02](02-REUNIONES-CON-EL-CLIENTE.md). | Hay SOW aprobado, responsable de UAT y acceso a entorno de trabajo. |
| 5. Preparación → backlog priorizado y especificación | LP · LT, DEV, CL | Escribir historias y criterios verificables según [03](03-DOCUMENTOS-DEL-PROYECTO.md); dividir lo grande; definir arquitectura y ADR de decisiones relevantes. | Cada historia del primer sprint tiene criterio de aceptación y datos de prueba. |
| 6. Sprint de 1–2 semanas → incremento probado | DEV · LT, QA, LP | Planificar capacidad; implementar en rama; revisar código; ejecutar pruebas proporcionales y registrar resultados. Publicar estado y bloqueos al menos dos veces por semana. | QA verifica criterios; LP revisa evidencia y cambios de alcance. |
| 7. Demo → acta de demo y backlog actualizado | LP · DEV, CL | Mostrar flujo real con datos de prueba; registrar lo aceptado, observaciones y decisiones. No presentar pantallas incompletas como terminadas. | CL prioriza observaciones; lo nuevo entra por control de cambios. |
| 8. UAT → casos y acta de resultados | CL · LP, QA | CL ejecuta casos de aceptación en entorno acordado; QA reproduce defectos; DEV corrige; CL repite casos fallidos. | Defectos críticos y altos resueltos o excepción escrita y aceptada por CL. |
| 9. Despliegue → registro de versión | LT · DEV, QA, LP | Seguir [05](05-DESPLIEGUES.md): respaldo, aprobación, despliegue, smoke test y plan de reversión. Comunicar ventana y resultado. | Salud, flujos críticos y datos verificados; CL recibe acceso y manual. |
| 10. Cierre → acta de conformidad y entrega | LP · CL, LT | Entregar manual de usuario, manual técnico, accesos por canal seguro, repositorio o paquete pactado, pendientes y periodo de garantía. | CL firma o deja observaciones con fecha; LP registra lo pendiente. |
| 11. Soporte → registro de incidencias y reporte | Responsable de soporte · CL, DEV | Clasificar severidad según SOW/SLA; confirmar recepción; diagnosticar, resolver, validar con CL y cerrar ticket. Revisar respaldos y alertas. | Ticket cerrado con causa, solución y validación; cambios mayores van a propuesta nueva. |

## Cadencia mínima del sprint

1. **Planificación (30–60 min):** LP y equipo eligen historias que caben según capacidad real y dependencias; anotan objetivo del sprint.
2. **Seguimiento (10–15 min, 2–5 veces por semana):** cada responsable dice qué terminó, qué sigue y qué bloqueo necesita decisión. LP registra impedimentos.
3. **Refinamiento (30–60 min):** CL aclara reglas de negocio y prioriza; DEV señala incertidumbre técnica.
4. **Demo (30–45 min):** mostrar criterios funcionando; cerrar con decisiones en acta.
5. **Retrospectiva interna (30 min):** una mejora concreta con responsable y fecha.

Un pedido nuevo después de aprobar el SOW se registra como cambio: descripción, impacto en horas/plazo/costo, opción de intercambiar por otro entregable y aprobación del CL antes de ejecutarlo. La ausencia de respuesta no equivale a aprobación.

## Evidencia mínima por proyecto

Ficha → resumen de descubrimiento → propuesta/SOW aprobado → acta de kickoff → backlog y criterios → pruebas y demos → UAT → registro de despliegue → manuales → acta de conformidad → tickets de soporte. Ver [plantillas](03-DOCUMENTOS-DEL-PROYECTO.md).
