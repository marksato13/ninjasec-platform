# NinjaSec - Siguiente trabajo por fases

## Estado actual del proyecto

Despues de revisar el repositorio, el proyecto ya no esta en etapa de estructura vacia. Ya existe una base funcional importante.

### Lo que ya esta avanzado

- backend FastAPI con `main.py`, `api/router.py` y modulos separados
- modelos principales de base de datos ya creados en `backend/app/db/models`
- autenticacion con `login`, `me`, token y redireccion por rol
- seed inicial con usuarios demo, cliente demo, integraciones demo y reporte demo
- frontend Next.js con landing, paginas publicas, `login`, `dashboard` y `portal`
- guards de frontend para `dashboard` y `portal`
- varias pantallas administrativas ya consumen API

### Lo que aun esta incompleto o parcial

- varias vistas del frontend aun son pantallas de resumen o placeholder
- la estructura del frontend no esta alineada del todo con la especificacion de `route groups`
- no todas las rutas definidas en la especificacion existen exactamente igual
- faltan validaciones finas de permisos por modulo y por accion
- faltan pruebas automatizadas reales
- falta endurecimiento para produccion

## Que debes hacer ahora mismo

La siguiente tarea correcta no es crear mas modulos nuevos. Lo siguiente es cerrar la `Fase A` real del proyecto con una alineacion entre especificacion y codigo existente.

### Fase A - Alineacion final de arquitectura y rutas

Objetivo:

Dejar el proyecto consistente con la especificacion funcional ya aprobada para evitar que el resto del desarrollo se construya sobre rutas, vistas o permisos inconsistentes.

Debes hacer ahora:

1. revisar cada ruta del frontend contra la especificacion oficial
2. confirmar si faltan estas rutas esperadas:
   - `/dashboard/settings`
   - `/portal/company`
   - `/portal/projects`
   - `/portal/reports`
   - `/portal/support`
3. decidir si se conservaran rutas extra ya creadas como:
   - `/portal/tasks`
   - `/portal/resources`
   - `/portal/documents`
4. reorganizar el frontend hacia grupos logicos equivalentes a:
   - publico
   - admin
   - portal
5. dejar documentado que paginas estan completas, cuales estan parciales y cuales son placeholder

Entregable de esta fase:

- mapa real de rutas implementadas
- estructura frontend alineada con la especificacion
- lista de vistas completas vs pendientes

## Despues de eso, que sigue

### Fase B - Cerrar autenticacion y permisos de verdad

Objetivo:

Pasar de una autenticacion funcional a un control de acceso confiable por rol y modulo.

Debes hacer despues:

1. revisar todos los endpoints para aplicar `require_roles(...)` donde falte
2. separar permisos de lectura y escritura para admin, collaborator y client
3. asegurar que `client` no pueda ver datos globales del dashboard
4. asegurar que `collaborator` vea solo su contexto operativo
5. unificar comportamiento de redireccion despues de login y despues de sesion expirada
6. validar respuestas `401` y `403` en frontend y backend

Entregable de esta fase:

- permisos por endpoint aplicados
- guards del frontend consistentes
- flujo de login, logout y sesion expirada estable

## Luego sigue

### Fase C - Completar el sitio publico y captacion

Objetivo:

Convertir la capa publica en una parte comercial util, no solo visual.

Debes hacer despues:

1. revisar si `inicio`, `nosotros`, `servicios`, `solucion`, `contacto`, `agenda-demo` y `colabora` cumplen el mensaje comercial definido en `docs`
2. completar formularios publicos y su experiencia de exito/error
3. conectar completamente captacion con:
   - `leads`
   - `job_applications`
   - `service_requests`
4. mejorar copy comercial, CTA y credibilidad visual
5. dejar clara la doble identidad: empresa + plataforma

Entregable de esta fase:

- sitio publico comercialmente consistente
- formularios guardando datos reales
- narrativa de portafolio alineada a NinjaSec

## Luego sigue

### Fase D - Convertir el dashboard en backoffice real

Objetivo:

Pasar de pantallas administrativas mixtas a gestion operativa real.

Debes hacer despues:

1. identificar modulos del dashboard que hoy solo muestran resumen o listados parciales
2. completar CRUDs faltantes para:
   - usuarios
   - clientes
   - colaboradores
   - proyectos
   - servicios
3. completar vistas de leads, postulaciones y auditoria
4. agregar estados vacios, carga, errores y confirmaciones
5. revisar consistencia entre formularios del frontend y esquemas del backend

Entregable de esta fase:

- backoffice utilizable por admin
- CRUDs principales cerrados
- trazabilidad administrativa mas clara

## Luego sigue

### Fase E - Portal por rol de verdad

Objetivo:

Dejar de tener un portal generico y construir experiencias diferenciadas para `client` y `collaborator`.

Debes hacer despues:

1. definir que ve exactamente un cliente en `/portal`
2. definir que ve exactamente un colaborador en `/portal`
3. adaptar sidebar, cards, tablas y mensajes segun rol
4. mostrar solo proyectos, reportes, soporte y datos permitidos para ese usuario
5. evaluar si `tasks`, `resources` y `documents` se quedan o se mueven a una fase posterior

Entregable de esta fase:

- portal contextualizado por rol
- experiencia cliente distinta de experiencia colaborador

## Luego sigue

### Fase F - Fortalecer el core de reporting por API

Objetivo:

Hacer que el diferencial del producto sea real y no solo demostrativo.

Debes hacer despues:

1. revisar el flujo de `integrations`, `devices`, `collection`, `reports` y `report_runs`
2. definir conectores demo vs conectores reales
3. mejorar prueba de conexion y recoleccion de snapshots
4. enlazar snapshots con dispositivos e integraciones de forma clara
5. mejorar ejecucion de reportes y salida de resultados
6. preparar siguiente paso hacia exportacion de reportes o PDFs

Entregable de esta fase:

- flujo de integracion a reporte funcionando de punta a punta
- mejor base para conectores reales como `pfSense` y `FortiGate`

## Luego sigue

### Fase G - Calidad, seguridad y despliegue

Objetivo:

Endurecer el sistema para uso serio.

Debes hacer despues:

1. agregar pruebas backend por modulos criticos
2. agregar pruebas frontend para flujos esenciales
3. mover configuraciones sensibles fuera de valores inseguros por defecto
4. revisar CORS, secretos, expiracion de token y manejo de errores
5. limpiar logs y artefactos no necesarios en el repo
6. preparar despliegue reproducible con Docker

Entregable de esta fase:

- proyecto mas estable, seguro y desplegable

## Orden recomendado real de ejecucion

1. Fase A - alinear arquitectura, rutas y pantallas actuales
2. Fase B - cerrar permisos y autenticacion por rol
3. Fase C - completar sitio publico y captacion
4. Fase D - convertir dashboard en backoffice real
5. Fase E - construir portal contextualizado por rol
6. Fase F - fortalecer integraciones, collection y reportes
7. Fase G - pruebas, seguridad y despliegue

## Recomendacion practica

Si quieres avanzar sin desorden, el siguiente bloque de trabajo deberia ser este:

1. auditar todas las rutas del frontend y compararlas con la especificacion
2. marcar que pantallas son reales y cuales son placeholder
3. ajustar permisos backend por modulo
4. recien despues completar vistas y formularios

Ese orden reduce retrabajo porque primero fija la estructura, luego el acceso, y luego la funcionalidad visible.
