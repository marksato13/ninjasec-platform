# Despliegues para pymes

El LT elige destino según carga, disponibilidad, residencia de datos, presupuesto operativo y capacidad de administración. Toda puesta en producción tiene dueño, respaldo recuperable, versión identificable y vuelta atrás ensayada. Para **esta plataforma**, consultar además el [runbook existente](../FLUJOS/DESPLIEGUE-PRODUCCION.md); esta guía es general y no autoriza activar un entorno.

## Opciones de alojamiento

| Opción | Encaja cuando | Atención antes de elegir |
| --- | --- | --- |
| VPS o instancia de Oracle Cloud Free | Aplicación pequeña con backend, base de datos y operador técnico disponible. | Confirmar límites y disponibilidad actuales del proveedor, arquitectura CPU, persistencia, red, copias externas y costo si se excede la capa gratuita. La gratuidad no garantiza capacidad ni SLA. |
| Docker Compose + Caddy en VPS | Uno o pocos servicios, tráfico moderado y despliegue controlado en una máquina. Caddy termina HTTPS y dirige al frontend/API. | La VM es un punto único de fallo; limitar puertos, mantener imágenes y sistema actualizados, proteger base de datos y respaldar fuera de la VM. No confundir reinicio de contenedor con recuperación de datos. |
| Vercel o Netlify | Sitio estático o frontend cuya ejecución sea compatible con la plataforma elegida. | Verificar funciones, límites, región, costos y variables de entorno. PostgreSQL y un backend FastAPI persistente requieren alojamiento aparte. |
| AWS | Integraciones, escalamiento, controles o requisitos corporativos que justifiquen más servicios gestionados. | Estimar consumo, egresos, observabilidad, IAM y operación. No proponer complejidad de nube sin responsable ni presupuesto aprobados. |

## Secuencia mínima de CI/CD con GitHub Actions

1. **Pull request:** instalar dependencias de forma reproducible; ejecutar pruebas backend, build frontend y controles de seguridad aplicables; publicar resultado exacto. No pasar secretos de producción a jobs de PR.
2. **Revisión:** LT revisa cambios, migraciones, licencias, dependencias y evidencia; LP confirma alcance. Fusionar solo con puertas requeridas aprobadas.
3. **Artefacto:** construir una imagen o paquete con etiqueta de commit SHA; guardar referencia y checksum. Evitar `latest` como única forma de identificar versión.
4. **Staging:** desplegar el mismo artefacto y configuración equivalente sin datos reales; ejecutar smoke test y UAT pactado.
5. **Producción:** obtener aprobación humana y ventana; confirmar respaldo y reversión; desplegar versión aprobada; comprobar salud y flujos críticos; comunicar resultado. Guardar registro de despliegue.

Un workflow de despliegue debe limitarse a la rama y entorno aprobados, usar permisos mínimos y separar credenciales de producción. Fijar acciones a versiones revisadas. Si no existe entorno protegido o respaldo restaurable, el despliegue queda pendiente.

## Respaldos y restauración

- **Qué:** PostgreSQL, archivos cargados por usuarios y configuración necesaria para reconstruir el servicio. Los secretos se guardan en un gestor seguro aparte.
- **Cómo:** copia automatizada, cifrada y fuera de la máquina principal; política de retención acordada en el SOW; monitoreo de éxito/fallo. Para PostgreSQL usar copia lógica consistente o solución equivalente y verificar integridad.
- **Prueba:** restaurar periódicamente en entorno aislado; registrar fecha, tamaño, versión, tiempo de recuperación y validación de una muestra de datos. Una copia sin prueba de restauración no es evidencia de recuperación.
- **Objetivos:** pactar RPO (máxima pérdida de datos aceptable) y RTO (tiempo objetivo de recuperación) con el cliente; elegir frecuencia y arquitectura según esos objetivos.

## Checklist de puesta en producción

| Comprobación | Responsable | Evidencia |
| --- | --- | --- |
| SOW/UAT y versión aprobados; ventana y contactos confirmados | LP | Acta y aviso |
| Revisión de seguridad, licencias y CI completada | LT | PR y resultados |
| DNS, HTTPS, dominio y certificados listos | LT | Prueba de acceso |
| Credenciales de producción únicas, permisos mínimos y secretos fuera del repositorio | LT | Lista de controles, sin valores |
| Migraciones revisadas; compatibilidad y reversión conocidas | LT | Plan y ensayo |
| Respaldo reciente y restauración previamente probada | LT | Registro y ubicación segura |
| Monitoreo, alertas, logs sin datos sensibles y responsable de guardia | LT | Captura/enlace |
| Smoke test: inicio de sesión, permisos, operación clave, correo/integración y lectura/escritura | QA | Casos y resultados |
| Manuales y canal de soporte entregados | LP | Enlaces y acuse |

## Vuelta atrás

1. Si falla un criterio crítico, LT detiene el despliegue y avisa a LP/CL con impacto y ETA de evaluación.
2. Conservar logs y versión fallida; volver al artefacto anterior **solo si** el esquema y los datos siguen siendo compatibles.
3. Si hubo migración no reversible o escrituras nuevas, usar el plan específico ensayado: migración correctiva o restauración con aprobación del responsable de datos, considerando el RPO. No ejecutar restauración destructiva por reflejo.
4. QA repite smoke test y comprueba integridad; LP comunica estado, incidente y próximo paso.
5. Registrar causa, versión, horario, personas, datos afectados y acción preventiva.

**Registro de despliegue:** proyecto, entorno, fecha/hora, responsable, SHA/artefacto, PR, respaldo, migraciones, resultados del smoke test, decisión de continuar o revertir, aprobación y enlace al incidente si aplica.
