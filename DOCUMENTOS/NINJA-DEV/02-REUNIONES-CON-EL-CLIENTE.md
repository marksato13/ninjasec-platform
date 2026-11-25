# Reuniones con el cliente

El LP convoca con objetivo, agenda y enlace a documentos al menos un día hábil antes. Al terminar, envía el acta por el canal acordado dentro de un día hábil. El CL confirma acuerdos o corrige el acta; las decisiones de alcance y costo requieren aprobación explícita.

| Reunión | Duración y asistentes | Agenda tipo | Salida y decisión |
| --- | --- | --- | --- |
| Kickoff | 60 min; CL decisor y usuario clave, LP, LT, RC | 10 min objetivo y éxito; 15 min alcance/exclusiones; 10 min hitos; 10 min accesos y datos; 10 min riesgos; 5 min próximos pasos. | Acta, responsables, calendario, canal y fecha del primer sprint. |
| Refinamiento | 45–60 min semanal o por sprint; CL usuario clave, LP, DEV, QA cuando aplique | 5 min objetivo; 25–35 min historias y ejemplos; 10 min prioridades/dependencias; 5 min decisiones. | Historias con criterios y dudas asignadas; ninguna duda crítica se declara resuelta sin CL. |
| Demo | 30–45 min al final de cada sprint; CL decisor/usuarios, LP, DEV, QA | 5 min objetivo; 20 min recorrido en entorno de prueba; 10 min preguntas y observaciones; 5 min aceptación/prioridad. | Acta con historias demostradas, evidencia y observaciones clasificadas. |
| Cierre | 45–60 min; CL decisor, LP, LT y soporte | 10 min alcance entregado; 15 min UAT y pendientes; 10 min manuales/accesos; 10 min soporte/SLA; 5 min conformidad. | Acta de conformidad o lista de observaciones con responsable y fecha. |

## Antes, durante y después

- **Antes:** LP confirma asistentes con poder de decisión, prepara entorno y casos, envía agenda y preguntas concretas. DEV evita usar datos reales sin autorización.
- **Durante:** LP lleva el tiempo; una persona anota acuerdos y discrepancias; cada decisión tiene responsable y fecha. Si falta el decisor, se deja como pendiente.
- **Después:** LP envía acta, actualiza backlog y SOW si corresponde, y verifica que cada compromiso esté asignado. No convertir una observación de demo en trabajo adicional sin evaluar impacto.

## Plantilla breve de acta

    # Acta — [tipo de reunión] — [proyecto]
    Fecha y zona horaria: [AAAA-MM-DD, hora, Perú]
    Participantes y rol: [nombre — rol]
    Objetivo: [una frase]
    Documentos/versiones revisados: [enlaces]

    ## Decisiones
    | ID | Acuerdo y alcance exacto | Aprueba | Fecha |
    | --- | --- | --- | --- |
    | D-01 | [decisión] | [CL/LP] | [fecha] |

    ## Acciones
    | ID | Tarea | Responsable | Vence | Evidencia |
    | --- | --- | --- | --- | --- |
    | A-01 | [acción] | [nombre] | [fecha] | [enlace] |

    ## Riesgos y dudas
    - [Riesgo o pregunta] — [quién responde] — [fecha].

    Próxima reunión: [fecha o por definir]
    Confirmación del cliente: [enlace a correo/ticket/firma o pendiente]

Si el cliente no confirma, el LP marca el acta «pendiente de confirmación» y pide respuesta; no atribuye aprobación tácita.
