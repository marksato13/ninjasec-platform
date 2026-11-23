# NinjaSec - Plan por fases: proyectos por tipo, areas y recomendacion de colaboradores

## Decisiones confirmadas

- Separar `services` y `products`.
- Areas iniciales definidas (ver lista).
- Reglas de negocio obligatorias: todo proyecto debe tener cliente y colaboradores.

## Areas recomendadas (catalogo inicial)

- Redes
- Seguridad de redes
- Ciberseguridad
- Desarrollo
- DevOps
- Gestion TI
- Consultoria
- Datos y analitica
- Compliance / GRC

## Fase 1 - Modelo de datos

### Objetivo

Crear tablas base para tipo de proyecto, areas, productos, requisitos y recomendaciones.

### Cambios

- `project_types` (implementation, consulting, support)
- `areas`
- `products` (con area_id)
- `project_requirements` (skills + nivel + obligatorio)
- `project_recommendations` (ranking de colaboradores)
- extender `services` (area_id, project_type_id sugerido)
- extender `projects` (project_type_id, area_id, service_id/product_id)
- extender `project_members` (assignment_type, is_required)

### Regla clave

- No se permite `project` sin `client_id` ni colaboradores asignados.

## Fase 2 - Seeds y datos ficticios

### Objetivo

Datos reales para probar reglas y recomendaciones.

### Seeds sugeridos

- Project types:
  - Implementacion
  - Consultoria
  - Soporte
- Areas:
  - Redes
  - Seguridad de redes
  - Ciberseguridad
  - Desarrollo
  - DevOps
  - Gestion TI
  - Consultoria
  - Datos y analitica
  - Compliance / GRC
- Products:
  - NinjaSec Core (Ciberseguridad)
  - NinjaSec Observability (Redes)
- Services:
  - API Reporting (Ciberseguridad)
  - SOC Dashboard (Ciberseguridad)
  - Network Monitoring (Redes)
  - Compliance Baseline (Compliance / GRC)
- Clientes:
  - Blue Shield Tech
  - Orion Logistics
  - Nova Retail
- Colaboradores:
  - Maria Torres (Redes, FortiGate, Seguridad de redes)
  - Luis Arce (Ciberseguridad, SOC, Threat Hunting)
  - Carla Paredes (DevOps, Automatizacion, CI/CD)

## Fase 3 - API (backend)

### Objetivo

Endpoints para crear proyectos por tipo y obtener sugerencias de colaboradores.

### Endpoints nuevos

- `GET /project-types`
- `GET /areas`
- `GET /products`
- `POST /projects` (con `project_type_id`, `service_id` o `product_id`)
- `POST /project-requirements`
- `GET /project-recommendations?project_id=`
- `POST /project-members` (asignar colaborador)

### Reglas de negocio en API

- `project_type_id` obligatorio.
- `client_id` obligatorio.
- `service_id` o `product_id` obligatorio.
- `area_id` se autocompleta desde servicio/producto.
- `status` solo pasa a `active` si hay colaboradores asignados.

## Fase 4 - Logica de recomendacion

### Objetivo

Calcular sugerencias por skills.

### Logica propuesta

- Cada requisito de skill genera un peso.
- Nivel de skill del colaborador aporta puntaje.
- Se guarda ranking en `project_recommendations`.
- Solo se sugiere colaboradores del mismo tenant.

## Fase 5 - UI Admin

### Objetivo

Formulario de proyecto mas inteligente y asistido.

### UI propuesta

- Select de tipo de proyecto.
- Select de servicio o producto.
- Campo de area autocompletado (solo lectura).
- Seccion de requisitos (skills + nivel + obligatorio).
- Seccion de recomendados con boton “Asignar”.

## Fase 6 - UI Portal (colaborador/cliente)

### Objetivo

Mostrar contexto del proyecto y equipo asignado.

### UI propuesta

- Cliente ve: servicio/producto, area, colaboradores asignados.
- Colaborador ve: rol asignado y tareas sugeridas.

## Reglas operativas finales

- Un proyecto sin cliente no se guarda.
- Un proyecto sin colaboradores no puede activarse.
- La asignacion por recomendacion no reemplaza aprobacion humana.
