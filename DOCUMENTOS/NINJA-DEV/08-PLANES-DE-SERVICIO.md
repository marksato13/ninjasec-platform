# Estructura de planes de Ninja Dev

Estos planes son **marcos de alcance**, no ofertas vigentes ni cotizaciones. RC adapta entregables, límites y SLA en cada SOW. Los **precios reales viven en el repositorio privado `ninjasec-empresa`**; no se publican aquí ni se infieren.

| Plan | Incluye como base | Límites que el SOW debe completar | Entrega | Respuesta a defectos durante garantía, ejemplo |
| --- | --- | --- | --- | --- |
| Básico | Descubrimiento breve, web corporativa o automatización acotada, diseño adaptable, pruebas de flujo principal, publicación y manual breve. | Número de páginas o flujos, rondas de revisión, idiomas, carga de contenido, integraciones y plazo de garantía. | Entorno publicado, accesos, manual y acta. | 2 días hábiles dentro del horario pactado. |
| Profesional | Descubrimiento y especificación, sistema con roles y base de datos, integraciones pactadas, sprints de 1–2 semanas, pruebas funcionales, UAT, despliegue y manuales. | Número de módulos, usuarios, integraciones, migración de datos, rendimiento objetivo y horas de capacitación. | Código/artefacto acordado, documentación técnica y de usuario, UAT y acta. | 1 día hábil dentro del horario pactado. |
| A medida | Análisis detallado, arquitectura/ADR, fases y entregables negociados, requisitos especiales de seguridad, integración o disponibilidad, plan de operación. | Cada capacidad, dependencia, hito, aceptación, continuidad y responsabilidad se define en SOW; no asumir «ilimitado». | Entregas por hito, evidencias y transferencia pactada. | Por severidad y horario definidos en el SOW. |

## Mantenimiento mensual, contrato separado

| Nivel orientativo | Incluye | Límite a pactar | SLA de ejemplo para **primera respuesta**, no resolución |
| --- | --- | --- | --- |
| Esencial | Monitoreo básico, revisión de copias y restauración periódica, parches críticos, atención de incidentes. | Horario, canales, número de solicitudes y horas mensuales. | Incidente crítico: 1 día hábil; normal: 2 días hábiles. |
| Operativo | Lo anterior, mantenimiento preventivo, actualización de dependencias, informe mensual y bolsa de cambios menores. | Horas de cambios, frecuencia de despliegue y ventana. | Crítico: 4 horas hábiles; normal: 1 día hábil. |
| Dedicado | Cobertura, observabilidad, pruebas de recuperación y capacidad reservada definidas por contrato. | Guardia, 24/7 si se contrata, RTO/RPO, escalamiento y terceros. | Se fija por severidad y horario en el SOW; sin acuerdo no se promete 24/7. |

**Definiciones para el SLA:** crítico = servicio principal indisponible o pérdida de datos; alto = función esencial degradada sin alternativa; normal = error con alternativa o consulta. El reloj corre solo dentro del horario contratado. La primera respuesta confirma recepción, clasificación y siguiente actualización; el plazo de resolución depende de diagnóstico, proveedor y solución acordada. El SOW debe fijar zona horaria de Perú, canal oficial, escalamiento y pausas cuando falta información del cliente.

## Exclusiones habituales que deben quedar escritas

Funcionalidad nueva, rediseño, recuperación de datos anteriores al contrato, costos de nube/licencias/dominio, incidentes causados por cambios de terceros o del cliente, y trabajo fuera de horario no contratado. Cada exclusión se confirma con RC y CL; nunca se usa para negar una obligación ya firmada.

Antes de vender un plan, LP completa: entregables cuantificados, criterios de aceptación, plazo, número de revisiones, propiedad de cuentas, garantía, horario y canal de soporte, severidades, SLA, límites mensuales y procedimiento de cambios.
