# NinjaSec - Fase C - Sitio publico y captacion

## Objetivo

Completar la capa publica para que funcione como canal comercial real, no solo como vitrina visual.

## Cambios aplicados

### 1. Solicitudes de servicios desde la web

Se agrego un formulario publico para crear `service_requests` desde la pagina de servicios.

- listado de servicios se carga desde `/services/`
- envio hacia `/services/requests`

Archivo:

- `frontend/src/components/public/service-request-form.tsx`

### 2. Refuerzo de mensaje comercial en la landing

Se agrego un bloque adicional en la landing para destacar portafolio, consultoria y CTA comercial.

Archivo:

- `frontend/src/app/(public)/page.tsx`

### 3. Servicios con CTA directo

La pagina de servicios ahora incluye el formulario de solicitud para convertir visitas en demanda.

Archivo:

- `frontend/src/app/(public)/servicios/page.tsx`

## Estado de captacion actual

- Leads generales: `/contacto` y `/agenda-demo`
- Postulaciones: `/colabora`
- Solicitudes de servicio: `/servicios`

## Siguiente paso recomendado

Validar formularios con backend local y revisar copy final para presentacion comercial.
