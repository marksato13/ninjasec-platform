# Postulaciones - Fase 3 (Portal colaborador)

## Objetivo

Habilitar el acceso de colaboradores a postulaciones asignadas, con vista detalle para registrar reviews y recomendaciones.

## Implementado

- Listado "Mis revisiones" en cards con filtros por estado, rol deseado y fechas.
- Vista detalle con tabs: Resumen, Review, Notas internas y Timeline.
- Formulario de review con score, recomendacion y notas internas.
- Formulario de notas internas visibles en administracion.
- Timeline con eventos de estado, asignaciones, reviews y notas.
- Endpoints GET para listados en detalle (asignaciones, reviews, notas, adjuntos).

## Rutas y archivos

- Portal listado: `frontend/src/app/(portal)/portal/applications/page.tsx`
- Portal detalle: `frontend/src/app/(portal)/portal/applications/[applicationId]/page.tsx`
- Sidebar portal: `frontend/src/components/dashboard/portal-sidebar.tsx`
- API frontend: `frontend/src/lib/api.ts`
- Endpoints backend: `backend/app/modules/recruitment/routers/router.py`

## Validacion sugerida

1) Ingresar como colaborador y abrir `/portal/applications`.
2) Verificar que solo aparezcan postulaciones asignadas.
3) Abrir una postulacion, enviar review y nota interna.
4) Confirmar que el timeline refleje los eventos.
5) Ingresar como admin y validar que las recomendaciones se ven en el detalle.
