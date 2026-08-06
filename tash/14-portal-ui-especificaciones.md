# NinjaSec - Especificaciones UI Portal

## Objetivo

Unificar la interfaz del portal con una apariencia profesional, header funcional y control de tema.

## Header del portal

- muestra titulo de seccion segun ruta
- muestra avatar con iniciales y nombre
- incluye toggle de tema claro/oscuro
- el avatar enlaza a `/portal/profile`

## Navegacion

- items del sidebar sin descripcion
- items visibles segun rol (client/collaborator)

## Modulos

- los modulos no incluyen descripcion debajo del titulo
- se mantiene contenido operativo en paneles

## Botones

- estilos unificados: primary, secondary, ghost, destructive
- estados hover y focus consistentes

## Tema claro / oscuro

- toggle guarda preferencia en `localStorage`
- variables CSS controlan colores globales
- se aplica `data-theme` en `html`

## Archivos clave

- `frontend/src/components/dashboard/portal-header.tsx`
- `frontend/src/components/theme/theme-provider.tsx`
- `frontend/src/components/theme/theme-toggle.tsx`
- `frontend/src/components/dashboard/portal-sidebar.tsx`
- `frontend/src/components/dashboard/portal-shell.tsx`
- `frontend/src/app/(portal)/portal/layout.tsx`
- `frontend/src/app/globals.css`
