# Reporte y plan de implementacion (stack recomendado)

## Resumen

Se evaluaron librerias para un stack robusto Next.js + FastAPI. Se prioriza: productividad, rendimiento, seguridad y consistencia de UI.

## Recomendacion principal (lo que conviene usar)

### Frontend (Next.js)

- UI: `Shadcn/ui` + `Tailwind CSS`
  - Motivo: componentes accesibles, personalizables y consistentes; acelera UI sin perder control.
- Data fetching/cache: `TanStack Query`
  - Motivo: cache, revalidacion y estado de servidor confiable.
- Formularios: `React Hook Form` + `Zod`
  - Motivo: performance alta, validacion tipada y escalable.
- Animaciones: `Framer Motion`
  - Motivo: mejor integracion React que Anime.js para UI.

### Backend (FastAPI)

- Validacion: `Pydantic` (nativo en FastAPI)
- ORM: `SQLAlchemy 2.0`
- Auth: `PyJWT` + cookies HTTP-only
- Tiempo real: `WebSockets` de FastAPI (si se requieren notificaciones)

### Infraestructura

- Contenedores: `Docker` (ya usado en el proyecto). Podman es viable pero no necesario hoy.
- Deploy: `Vercel` para Next.js, `Render` o `Railway` para FastAPI.

## Recomendacion especifica para alertas y modales

- Alertas/toasts: `SweetAlert2` (ya solicitado) para confirmaciones, errores y estados.
- Modales complejos: `@radix-ui/react-dialog` (si se requiere accesibilidad total y composicion avanzada).

**Recomendacion final**

- Usar **SweetAlert2** como base de alertas y confirmaciones.
- Para modales simples de formularios, usar un modal propio (ya creado) o Radix si se quiere accesibilidad avanzada.

## Plan de actualizacion e implementacion (alto nivel)

### Fase 1 - UI Base y Alertas

- Integrar SweetAlert2 para:
  - Confirmaciones de eliminar.
  - Mensajes de exito/error en formularios.
- Convertir formularios en modales en admin (usuarios, clientes, colaboradores, proyectos).

### Fase 2 - UX y Estandar visual

- Normalizar cards, badges y botones en todo el backoffice.
- Ajustar espaciados y margenes globales.

### Fase 3 - Data fetching moderno

- Migrar llamadas de API a `TanStack Query`.
- Crear hooks tipados por modulo.

### Fase 4 - Formularios robustos

- Integrar `React Hook Form` + `Zod` en CRUDs.
- Validaciones consistentes con backend.

### Fase 5 - Backend permisos y seguridad

- RBAC formal con dependencias FastAPI.
- Endpoint `/permissions/me`.
- Auditoria extendida.

## Plan de implementacion (detalle tecnico)

1. Alertas y modales:
   - Instalar SweetAlert2.
   - Reemplazar `window.confirm` por SweetAlert2.
   - Crear hooks para success/error.

2. Formularios en modales:
   - Boton "Nuevo" abre modal.
   - Formulario dentro del modal.

3. Mejoras UI/UX:
   - Cards responsivos.
   - Espaciado consistente.
   - Headers compactos.

4. Migracion progresiva:
   - Usuarios -> Clientes -> Colaboradores -> Proyectos.

## Nota

Si deseas, se puede instalar Shadcn/ui y Tailwind despues de estabilizar las vistas actuales para evitar refactor masivo.
