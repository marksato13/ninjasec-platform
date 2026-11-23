# NinjaSec - Plan de implementacion (perfiles, skills, certificaciones, docs)

## Decisiones confirmadas

- Verificacion solo por `super_admin`.
- Cliente ve docs solo si: `client_status=active` + `visibility=client` + `enabled=true`.
- Editor Markdown simple (textarea), sin subida de archivos.

## Fase 1 - Modelo de datos y migraciones

### Objetivo

Crear las nuevas tablas y campos base para skills, certificaciones y documentacion por proyecto.

### Entregables

- nuevas tablas: `skills`, `user_skills`, `user_certifications`, `doc_types`, `project_docs`
- extension de `project_members` con permisos
- seeds iniciales para `doc_types`

### Prompt (modo ejecucion)

""
Analiza el repo y agrega las tablas nuevas para perfiles avanzados.
Usa buenas practicas de FastAPI + SQLAlchemy.
Aplica Context7 para consultar docs relevantes de SQLAlchemy/FastAPI si es necesario.
Implementa:
- models: skills, user_skills, user_certifications, doc_types, project_docs
- agrega campos a project_members: role_in_project, can_publish_docs
- agrega enums necesarios
- seed inicial de doc_types segun empresa publica/privada
No hagas cambios en frontend aun.
""

## Fase 2 - API y permisos (RBAC)

### Objetivo

Exponer endpoints con verificacion por `super_admin` y reglas de visibilidad.

### Entregables

- CRUD y listados por rol
- verificacion (approve/reject)
- filtros por proyecto y visibilidad

### Prompt (modo ejecucion)

""
Implementa endpoints para skills, certificaciones y documentacion por proyecto.
Aplica RBAC: solo super_admin puede verificar.
Aplica reglas de visibilidad para clientes (active + enabled + visibility=client).
Usa buenas practicas de FastAPI y SQLAlchemy.
Consulta Context7 para patrones de dependencias y validacion.
No toques frontend.
""

## Fase 3 - Portal (colaborador y cliente)

### Objetivo

Mostrar perfil avanzado, certs y docs en cards con preview.

### Entregables

- perfil con skills y certificaciones
- docs en cards por proyecto
- editor Markdown simple para colaboradores

### Prompt (modo ejecucion)

""
Implementa UI del portal para perfil avanzado y documentacion por proyecto.
Requisitos:
- cards con titulo, resumen, link GitHub y preview Markdown
- colaborador puede crear/editar docs del proyecto
- cliente solo ve docs habilitados y visibles
- sin subida de archivos
Usa buenas practicas de Next.js App Router y CSS existente.
Consulta Context7 para patrones de App Router si hace falta.
""

## Fase 4 - Admin (verificacion y catalogos)

### Objetivo

Panel para aprobar skills/certs y administrar tipos de documentos.

### Entregables

- cola de verificacion (skills/certs)
- gestion de doc_types
- control enable/disable docs

### Prompt (modo ejecucion)

""
Implementa vistas admin para:
- aprobar/rechazar skills y certificaciones
- administrar doc_types
- activar/desactivar docs por proyecto
Usa buenas practicas y el estilo visual actual.
Consulta Context7 si es necesario.
""

## Fase 5 - Auditoria y trazabilidad

### Objetivo

Registrar verificaciones y cambios clave.

### Entregables

- registros en audit_logs para approve/reject
- trazas de cambios de docs

### Prompt (modo ejecucion)

""
Agrega auditoria para verificaciones y cambios de documentacion.
Registra actor, entidad, accion y timestamp.
Usa el AuditService existente.
""
