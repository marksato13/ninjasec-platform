# NinjaSec - Fase E - Portal por rol

## Objetivo

Separar la experiencia de portal para `client` y `collaborator`, mostrando informacion relevante por rol.

## Cambios aplicados

### 1. Navegacion contextual por rol

- clientes ven: portal, perfil, proyectos, reportes, soporte, empresa, documentos
- colaboradores ven: portal, perfil, proyectos, reportes, soporte, tareas, recursos

Archivo:

- `frontend/src/components/dashboard/portal-sidebar.tsx`

### 2. Portal con resumen por rol

- resumen de proyectos y reportes visibles
- empresa visible solo para clientes

Archivo:

- `frontend/src/components/dashboard/portal-shell.tsx`

### 3. Pantallas funcionales con datos reales

- perfil (datos desde `/auth/me`)
- empresa (solo client, desde `/clients/`)
- proyectos (desde `/projects/`)
- reportes (desde `/reports/`)

Archivos:

- `frontend/src/app/(portal)/portal/profile/page.tsx`
- `frontend/src/app/(portal)/portal/company/page.tsx`
- `frontend/src/app/(portal)/portal/projects/page.tsx`
- `frontend/src/app/(portal)/portal/reports/page.tsx`

### 4. Modulos operativos en preparacion

- tareas, recursos y documentos con estados explicitos
- soporte con canales basicos

Archivos:

- `frontend/src/app/(portal)/portal/tasks/page.tsx`
- `frontend/src/app/(portal)/portal/resources/page.tsx`
- `frontend/src/app/(portal)/portal/documents/page.tsx`
- `frontend/src/app/(portal)/portal/support/page.tsx`

## Siguiente paso recomendado

Completar los modulos de tareas, recursos y documentos con datos reales o integraciones del core de reporting.
