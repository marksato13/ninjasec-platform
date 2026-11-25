# Estimación y costos

El LP estima **alcance y esfuerzo** con LT y DEV antes de prometer fecha. RC aplica después las tarifas reales del repositorio privado `ninjasec-empresa`. Separar inversión inicial de gasto recurrente; nunca usar esta guía como cotización oficial.

## Pasos para estimar

1. Descomponer el SOW en entregables e historias con criterios de aceptación. Identificar integraciones, migración de datos, seguridad, documentación, capacitación y despliegue.
2. Asignar talla a cada historia: **S** (hasta 1 día), **M** (2–3 días), **L** (4–7 días). Dividir una L si tiene varias incertidumbres. Las tallas sirven para comparar, no para facturar.
3. Para cotizar, pasar a horas por **tipo de tarea y rol**. Usar rangos iniciales de la tabla y ajustarlos con experiencia real. Registrar supuesto, dependencia y nivel de confianza.
4. Añadir QA, revisión, reuniones, UAT, despliegue y manuales; no esconderlos dentro de «desarrollo».
5. Aplicar colchón de riesgo **solo sobre horas inciertas**, con motivo escrito: ejemplo 10 % si el alcance está claro, 20–30 % si hay integración sin prueba. No sustituye el control de cambios.
6. Calcular infraestructura, licencias, impuestos aplicables y soporte por separado. RC valida vigencia, moneda y condiciones.

## Rangos orientativos de esfuerzo, no tarifas

| Tipo de tarea | Rango inicial | Qué revisar |
| --- | ---: | --- |
| Descubrimiento y especificación de una historia mediana | 4–8 h | Número de usuarios y reglas |
| Pantalla con formulario y validación | 8–20 h | Estados, permisos, accesibilidad |
| Endpoint con reglas y pruebas | 6–16 h | Autorización, errores, datos |
| Integración externa | 12–40 h | Calidad de API, sandbox, reintentos |
| Migración o importación de datos | 8–32 h | Limpieza, volumen, reversión |
| QA/UAT por flujo | 4–12 h | Casos negativos y dispositivos |
| Despliegue y manuales | 8–24 h | Infraestructura y transferencia |

Son puntos de partida, no compromisos. Si faltan API, muestras o decisor, estimar una exploración acotada antes del proyecto completo.

## Plantilla de cálculo

| Partida | Horas | Tarifa por hora (S/) | Subtotal (S/) |
| --- | ---: | ---: | ---: |
| Análisis y diseño | [h] | [tarifa] | horas × tarifa |
| Desarrollo | [h] | [tarifa] | horas × tarifa |
| QA, UAT y correcciones incluidas | [h] | [tarifa] | horas × tarifa |
| Despliegue, manuales y capacitación | [h] | [tarifa] | horas × tarifa |
| Colchón de riesgo justificado | [h] | [tarifa] | horas × tarifa |
| **Total trabajo inicial** | | | **suma de subtotales** |

| Gasto | Frecuencia | Monto (S/) | Responsable de pago |
| --- | --- | ---: | --- |
| Infraestructura | mensual o anual | [monto] | [cliente/Ninja Tech] |
| Licencias y dominios | mensual o anual | [monto] | [cliente/Ninja Tech] |
| Soporte y mantenimiento | mensual | [monto] | [cliente/Ninja Tech] |

**Inversión inicial = suma de (horas × tarifa por rol) + infraestructura inicial + licencias iniciales.**

**Costo mensual = infraestructura mensual + licencias mensuales + soporte mensual.**
No sumar cuotas mensuales al pago inicial sin indicar cuántos meses se incluyen. Especificar si los montos incluyen impuestos; RC confirma el tratamiento aplicable.

### Ejemplo completamente ficticio, no precio de Ninja Tech

Supuestos: 20 h de análisis a **S/ 70/h**, 80 h de desarrollo a **S/ 90/h**, 20 h de QA a **S/ 70/h**, 12 h de despliegue y manuales a **S/ 80/h**, más 10 h de riesgo de integración a **S/ 90/h**. Infraestructura inicial **S/ 0** y licencia inicial **S/ 0**. Trabajo inicial: `1 400 + 7 200 + 1 400 + 960 + 900 = S/ 11 860`. Recurrente ficticio: infraestructura **S/ 120/mes** + licencias **S/ 30/mes** + soporte **S/ 600/mes** = **S/ 750/mes**. Ninguna cifra representa tarifas, planes ni proveedores reales de la empresa.

## Registro de supuestos

| ID | Supuesto o riesgo | Impacto si falla | Quién lo valida | Fecha límite |
| --- | --- | --- | --- | --- |
| E-01 | [Ej.: API del cliente disponible en sandbox] | [horas/plazo] | [CL] | [fecha] |

Si un supuesto no se confirma, LP revisa la estimación y RC envía el cambio antes de comprometer trabajo adicional.
