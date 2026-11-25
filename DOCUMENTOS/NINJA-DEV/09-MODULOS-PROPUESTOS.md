# Qué convertir en módulos de la plataforma

**Corte de revisión: 2026-11-25.** Se contrastaron las carpetas `PY-MK/backend/app/modules` y las rutas `PY-MK/frontend/src/app`. Esto es una propuesta de producto, no un pendiente aprobado del roadmap. Antes de implementarla, crear planificación, ID `NN-P-NN` y checklist según las reglas del repositorio. **S/M/L** expresa esfuerzo relativo de una primera versión, no horas comprometidas.

| Prioridad | Propuesta y primera versión útil | Esfuerzo | Qué ya existe y diferencia |
| --- | --- | --- | --- |
| P1 | **Estimador de costos:** partidas por rol, horas, riesgo e importes iniciales/recurrentes; versión exportable y aprobación interna. | M | `leads`, `projects` y `services` registran oportunidades/proyectos/servicios; no se observó un estimador de partidas ni una ruta de cotización. Tarifas reales deben ser privadas y de acceso restringido. |
| P1 | **Plantillas de documentos de proyecto:** elegir SOW, historia, ADR o acta; completar campos; generar versión revisable y publicar al proyecto tras aprobación. | M | `docs` ya gestiona tipos, documentos, archivos y visibilidad; `/portal/documents` los muestra. Proponer generación y control de versiones como ampliación de ese módulo, no otro repositorio de documentos. |
| P2 | **Registro de despliegues:** versión/SHA, entorno, responsable, checklist, respaldo, smoke test y reversión; consulta desde proyecto. | M | `projects` y `tracking` ya muestran avance, fases y actualizaciones; no se observó registro estructurado de despliegue. Integrar como evento del proyecto. |
| P2 | **UAT y conformidad:** casos por historia, resultado, evidencia, observaciones y aprobación del cliente. | M | `projects/routers/extras.py` contiene requisitos; `projects/routers/tasks.py` contiene tareas; `tracking` presenta progreso al cliente. Falta un flujo explícito de aceptación y acta. |
| P2 | **Catálogo de stack y ADR:** fichas por tipo de proyecto, restricciones y decisión aprobada, enlazadas al proyecto. | S | `catalogs` administra áreas, productos y tipos de proyecto; `docs` guarda documentos. Conviene empezar como contenido/plantillas dentro de ellos; crear tablas nuevas solo si se necesita filtrar o comparar decisiones. |
| P3 | **Actas y acuerdos de reuniones:** agenda, decisiones, responsables y vencimientos vinculados al proyecto. | S | `projects` maneja tareas y `tracking` publica avances; puede empezar como plantilla en `docs` y tareas existentes. Automatizar recordatorios solo tras validar uso real. |
| P3 | **Panel de mantenimiento/SLA:** contratos, ventanas, tiempos de respuesta y reporte mensual. | L | `support_tickets` ya gestiona incidencias y `services` catálogo/solicitudes. Falta contrato SLA medible; requiere definir reglas comerciales antes de programar alertas. |

## Orden de validación

1. LP y RC prueban el estimador y las plantillas con **un proyecto ficticio**. Confirmar campos, permisos y qué se mantiene fuera de la plataforma pública.
2. LT compara el registro de despliegue con el runbook y el seguimiento actual; evitar duplicar avances.
3. CL piloto valida si UAT y actas facilitan aceptación. Medir tiempo de preparación y correcciones antes de ampliar.

**No proponer de nuevo:** gestión básica de proyectos, tareas, requisitos, servicios, leads, documentos, tickets ni vista de seguimiento. Sus módulos/rutas ya existen. Las ideas anteriores amplían flujos concretos; ninguna afirma que una pantalla existente tenga todas las funciones descritas.
