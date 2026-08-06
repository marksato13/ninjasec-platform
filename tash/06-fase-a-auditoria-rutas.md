# NinjaSec - Fase A - Auditoria de rutas y pantallas

## Objetivo de esta auditoria

Levantar el mapa real de rutas del frontend, compararlo con la especificacion aprobada y marcar el estado actual de cada pantalla.

## 1. Mapa real de rutas actuales (frontend)

### Publico

- `/`
- `/nosotros`
- `/servicios`
- `/solucion`
- `/contacto`
- `/agenda-demo`
- `/colabora`
- `/login`

### Admin (dashboard)

- `/dashboard`
- `/dashboard/users`
- `/dashboard/clients`
- `/dashboard/collaborators`
- `/dashboard/projects`
- `/dashboard/services`
- `/dashboard/integrations`
- `/dashboard/devices`
- `/dashboard/reports`
- `/dashboard/leads`
- `/dashboard/applications`
- `/dashboard/audit`
- `/dashboard/settings`

### Portal (cliente / colaborador)

- `/portal`
- `/portal/profile`
- `/portal/company`
- `/portal/projects`
- `/portal/reports`
- `/portal/support`
- `/portal/tasks`
- `/portal/resources`
- `/portal/documents`

## 2. Comparacion contra especificacion

### Rutas publicas (match completo)

La especificacion de `docs/01-ninjasec-especificacion-y-plan.md` coincide con las rutas publicas actuales.

### Rutas privadas admin

Coinciden todas y ya se agrego:

- `/dashboard/settings`

### Rutas privadas portal

Coinciden todas, pero hay extras no definidos en la especificacion:

- Extras: `/portal/tasks`, `/portal/resources`, `/portal/documents`

Decision tomada:

- se mantienen como modulos opcionales del portal (quedan para fases posteriores)

## 3. Estado real de pantallas

### Pantallas funcionales (consumen API)

- `/dashboard/users` (lista + formulario)
- `/dashboard/clients` (lista + formulario)
- `/dashboard/services` (lista + solicitudes)
- `/dashboard/integrations` (lista + test + collect + formulario)
- `/dashboard/reports` (lista + run + historial + formulario)
- `/dashboard/devices` (lista + snapshots)
- `/dashboard/leads` (lista)
- `/dashboard/applications` (lista)
- `/dashboard/collaborators` (lista)
- `/dashboard/projects` (lista)
- `/contacto` (formulario lead)
- `/agenda-demo` (formulario lead)
- `/colabora` (formulario postulacion)
- `/login` (formulario login)

### Pantallas placeholder o resumen

- `/dashboard/audit`
- `/dashboard/settings`
- `/portal`
- `/portal/profile`
- `/portal/company`
- `/portal/projects`
- `/portal/reports`
- `/portal/support`
- `/portal/tasks`
- `/portal/resources`
- `/portal/documents`

### Pantallas publicas de contenido (sin datos dinamicos)

- `/`
- `/nosotros`
- `/servicios`
- `/solucion`

## 4. Acciones necesarias para cerrar Fase A

### A. Definir el mapa final de rutas

1. agregar `/dashboard/settings`
2. mantener como opcionales en el portal:
   - `/portal/tasks`
   - `/portal/resources`
   - `/portal/documents`

### B. Alinear estructura del frontend con la especificacion

Opcional pero recomendado:

- reorganizar `app/` con route groups `(public)`, `(admin)` y `(portal)`
- mantener los `layout.tsx` actuales pero moverlos a sus grupos

### C. Marcar pantallas completas vs pendientes

1. documentar que pantallas ya consumen API
2. documentar que pantallas son placeholder
3. decidir prioridad de completado por fase

## 5. Resultado esperado de Fase A

- mapa de rutas aprobado y congelado
- decision final sobre rutas extras del portal
- estructura del frontend alineada con esa decision
- lista de pantallas completas vs pendientes
