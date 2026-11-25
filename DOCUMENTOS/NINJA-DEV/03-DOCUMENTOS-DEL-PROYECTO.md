# Documentos del proyecto: plantillas mínimas

Copiar el esqueleto necesario a la carpeta del proyecto y completar los campos entre corchetes. Nombrar cada versión como `[proyecto]-[documento]-vX.Y`; guardar fecha, autor, aprobador y enlace a la versión anterior. El SOW aprobado manda sobre comentarios informales. No incluir contraseñas, tokens ni datos personales en estos documentos.

## 1. Propuesta técnica

    # Propuesta técnica — [cliente / proyecto]
    Versión / fecha / autor: [...]
    Problema y objetivo medible: [...]
    Solución recomendada: [componentes y flujo principal]
    Alternativas consideradas: [opción, ventaja, costo o límite]
    Entregables: [lista numerada]
    Supuestos y dependencias del cliente: [...]
    Riesgos principales y mitigación: [...]
    Cronograma por hitos: [hito, semana, responsable]
    Estimación y vigencia de oferta: [referencia al cálculo aprobado]
    Próximo paso: [aprobación del SOW / reunión]

## 2. Alcance de trabajo (SOW)

    # SOW — [cliente / proyecto]
    Versión / fecha / partes / aprobadores: [...]
    Objetivo y resultado esperado: [...]
    Entregables incluidos: [ID, descripción, criterio de aceptación]
    Exclusiones explícitas: [...]
    Responsabilidades de Ninja Tech: [...]
    Responsabilidades del cliente: [contenido, accesos, UAT, aprobaciones]
    Hitos, fechas y dependencias: [...]
    Entornos, propiedad de cuentas y datos: [...]
    Pruebas, UAT y plazo de respuesta del cliente: [...]
    Despliegue, capacitación y transferencia: [...]
    Garantía, soporte y SLA aplicable: [...]
    Gestión de cambios: [solicitud → impacto → aprobación escrita]
    Condiciones comerciales: [enlace al documento privado aprobado]
    Aprobación: [nombre, cargo, fecha, medio verificable]

## 3. Especificación funcional e historias

    # Especificación — [proyecto]
    Versión / fecha / responsable: [...]
    Usuarios y permisos: [...]
    Flujo actual y flujo objetivo: [...]
    Reglas de negocio y datos: [...]
    Integraciones y restricciones: [...]
    Requisitos no funcionales: [rendimiento, seguridad, respaldo, accesibilidad]

    ## HU-01 — [título]
    Como [rol], quiero [acción] para [beneficio].
    Prioridad: [alta/media/baja] · Dependencias: [...]
    Criterios de aceptación:
    - Dado [estado], cuando [acción], entonces [resultado verificable].
    - Dado [error o permiso insuficiente], cuando [...], entonces [...].
    Datos de prueba: [sintéticos o anonimizados]
    Evidencia UAT: [enlace / pendiente]

Una historia se puede iniciar cuando el CL entiende los criterios y el equipo puede probarlos. El comportamiento ante error y permisos forma parte de la historia.

## 4. Registro de decisión de arquitectura (ADR)

    # ADR-001 — [decisión]
    Estado: propuesta / aceptada / reemplazada
    Fecha / responsables: [...]
    Contexto y restricción: [...]
    Opciones consideradas: [...]
    Decisión y motivo: [...]
    Consecuencias y riesgos: [...]
    Cómo se validará: [...]
    Reemplaza / es reemplazada por: [ADR o no aplica]

Crear ADR cuando una decisión afecte costos, operación, datos, seguridad o capacidad de cambio. Un ADR aceptado no sustituye la aprobación comercial del cliente.

## 5. Manual de usuario

    # Manual de usuario — [producto y versión]
    Público y permisos necesarios: [...]
    Acceso y recuperación de cuenta: [sin credenciales reales]
    Tareas frecuentes: [pasos numerados, resultado esperado, captura o enlace]
    Mensajes de error comunes: [mensaje → acción]
    Preguntas frecuentes: [...]
    Cómo pedir soporte: [canal, horario, datos que debe aportar]
    Última revisión / responsable: [...]

## 6. Manual técnico

    # Manual técnico — [producto y versión]
    Diagrama y componentes: [...]
    Repositorio, rama y versión entregada: [...]
    Requisitos de infraestructura: [...]
    Variables de configuración: [nombres y propósito, nunca valores]
    Instalación y despliegue: [pasos y comprobaciones]
    Migraciones y compatibilidad: [...]
    Respaldos y restauración probada: [procedimiento y evidencia]
    Observabilidad: [salud, logs, alertas, responsables]
    Reversión: [versión anterior y pasos]
    Dependencias y licencias: [...]
    Contactos de operación y límites conocidos: [...]

## 7. Acta de conformidad

    # Acta de conformidad — [proyecto]
    Cliente / proveedor / fecha: [...]
    SOW y versión aprobada: [...]
    Entregables recibidos: [ID, versión, enlace]
    UAT: [casos aprobados, fecha, evidencia]
    Pendientes aceptados: [ID, severidad, responsable, fecha] o «ninguno»
    Fecha de inicio de garantía y soporte: [...]
    Declaración: [aceptación total / parcial con reservas / no aceptación]
    Observaciones: [...]
    Firma o aprobación verificable del cliente: [...]
    Firma o aprobación verificable de Ninja Tech: [...]

Si hay rechazo, conservar el resultado de UAT y acordar corrección y nueva fecha; no marcar el proyecto como conforme.
