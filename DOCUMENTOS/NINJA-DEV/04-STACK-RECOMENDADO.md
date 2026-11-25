# Stack recomendado por tipo de proyecto

Elegir la solución más simple que cumpla el SOW. Antes de prometer un stack, LT verifica capacidades del equipo, residencia de datos, integraciones, soporte disponible, presupuesto operativo y quién administrará la infraestructura. Registrar excepciones en un ADR.

| Proyecto | Recomendación inicial | Por qué | Cuándo no usarla |
| --- | --- | --- | --- |
| Web corporativa | Sitio estático con Astro o Next.js con generación estática; CSS accesible; CMS solo si el cliente editará contenido con frecuencia. Hosting estático con CDN. | Carga rápida, menor operación y despliegue simple. | Si hay flujos transaccionales, permisos complejos o datos privados; entonces diseñar aplicación y backend. No instalar CMS por costumbre. |
| Sistema a medida o ERP ligero | Next.js + TypeScript para interfaz; FastAPI + Pydantic/SQLAlchemy para API; PostgreSQL y Alembic; Docker Compose para una instalación pequeña. | Separación clara de interfaz y reglas; datos relacionales y migraciones trazables. | Si un SaaS existente cubre el proceso con menor costo total; si el equipo no puede sostener dos servicios; si se exige operación distribuida o alta disponibilidad que una sola VM no cubre. |
| API e integraciones | FastAPI + PostgreSQL cuando se necesita persistencia; OpenAPI; tareas en cola solo si hay trabajo asíncrono real; webhooks firmados e idempotencia. | Contratos visibles y pruebas de integración directas. | Si basta una función gestionada o integración nativa del proveedor; si el cliente exige otro ecosistema o runtime. |
| Automatización | Python con scripts versionados y programador de tareas; logs, reintentos e idempotencia; contenedor si facilita despliegue. | Bajo costo de entrada y mantenimiento legible. | Si una herramienta existente resuelve el flujo; si implica decisiones humanas o efectos irreversibles sin aprobación; si necesita interfaz compleja. |
| App móvil | Primero web adaptable o PWA si cubre el uso; si se requiere app instalada, React Native/Expo con API existente. | Reutiliza conocimientos de TypeScript y evita dos implementaciones nativas al inicio. | PWA: si se requieren capacidades nativas no disponibles o distribución obligatoria en tiendas. React Native: si hay hardware, rendimiento o requisitos específicos que exigen desarrollo nativo. |

## Stack de esta plataforma

La plataforma Ninja Tech usa **FastAPI + Next.js + PostgreSQL + Docker**. FastAPI expone la API; Next.js presenta panel y portal; PostgreSQL guarda datos relacionales; Docker Compose reúne los servicios. Las migraciones van por Alembic. Esta combinación es una referencia probada para proyectos parecidos, no una obligación para cada cliente.

## Comprobación antes de cerrar la propuesta

1. Escribir tres requisitos que deciden la elección: por ejemplo, edición de contenido, integración contable y operación sin internet.
2. Estimar costo de construcción **y** mantenimiento por 12 meses, incluidas copias, monitoreo, licencias y capacitación.
3. Validar autenticación, roles, aislamiento de datos, accesibilidad y obligaciones de protección de datos desde el diseño.
4. Hacer una prueba corta de la integración más incierta antes de comprometer fecha. Registrar resultado y alternativa.
5. Dejar en el ADR quién actualiza dependencias, dónde corre el sistema y cómo se recupera.
