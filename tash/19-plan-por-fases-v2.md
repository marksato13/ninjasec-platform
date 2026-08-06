# NinjaSec v2 - Plan por fases (detalle completo)

## Objetivo

Este documento traduce la especificacion v2 en instrucciones ejecutables por fases y por modulo. Define que falta, que se entrega, y como se valida. Es la guia principal de trabajo para cerrar NinjaSec v2.

## Reglas generales

- Respetar el scope por fase (no mezclar backend y frontend si la fase es solo backend).
- Cada fase debe cerrar con un .md de resultados y cambios aplicados.
- Mantener consistencia visual (cards, badges, layout) en admin y portal.
- Aplicar Context7 para validar practicas (FastAPI Security y Next.js App Router).
- Cualquier cambio de permisos debe reflejarse en backend y frontend.

## Fase 0 - Baseline y acuerdo funcional

### Objetivo

Congelar definicion funcional y arquitectura. Alinear roles, flujo principal y roadmap.

### Entregables

- Especificacion v2 aprobada.
- Diagrama ER actualizado.
- Matriz de roles y permisos validada.

### Estado

- Documento base creado: `docs/18-ninjasec-especificacion-funcional-arquitectura-v2.md`.

---

## Fase 1 - Backend base y permisos v2

### Objetivo

Formalizar RBAC y reglas de negocio con endpoints de soporte a UI.

### Entregables

- Roles extendidos en backend (`collaborator_admin`, `client_admin`).
- Endpoint de permisos por rol y UI consume permisos (no hardcode).
- Reglas de negocio de proyectos validadas en create/update.
- Auditoria en cambios criticos.
- Campo de avatar en users (y soporte para upload o URL).

### Checklist detallado

#### Seguridad y permisos

- Definir matriz de permisos por rol (L3/L2/L1/L0).
- Implementar dependency de permisos (FastAPI `Security`).
- Endpoints deben validar permisos por accion.
- Endpoint `/permissions/me` con permisos agregados.

#### Reglas de negocio

- Proyecto no puede estar `ACTIVE` sin miembros.
- Proyecto requiere client + service/product en creacion.
- Area se infiere desde service/product.
- Auditoria de cambios de estado.

#### Datos de usuario

- Campo `avatar_url` en `users`.
- Endpoint para update de avatar.
- Seed agrega avatar opcional.

---

## Fase 2 - Admin UI (cards, detalle, permisos)

### Objetivo

Backoffice profesional con cards y detalle accionable por rol.

### Entregables

- `/dashboard/projects` en cards con navegacion.
- Vista detalle con tabs: Info, Miembros, Docs, Skills, Recomendaciones.
- Acciones visibles segun rol.
- Estandar visual para cards.

### Checklist detallado

#### Proyectos (Admin)

- Card por proyecto: titulo, estado, tipo, cliente, area, tags, progreso.
- CTA: ver detalle.
- Filtros: status, tipo, cliente, area.
- En detalle: editor de descripcion, estado y fechas.
- En detalle: miembros y asignaciones con roles.

#### Permisos UI

- Super admin puede editar todo.
- Admin edita proyectos y miembros, no configuracion global.
- Collaborator admin solo asignaciones.
- Cliente y colaborador solo lectura en admin.

#### UX y Responsive

- Cards responsive (2-4 columnas).
- Layout tipo dashboard (header + paneles).

---

## Fase 3 - Portal por rol (cliente / colaborador)

### Objetivo

Portal con flujos diferenciados y lectura segura.

### Entregables

- `/portal/projects`: detalle en modo lectura.
- `/portal/reports`: lista filtrada por rol.
- `/portal/company`: contactos y datos del cliente.
- `/portal/profile`: skills/certs con estado de aprobacion.

### Checklist detallado

- Portal cliente: ve reportes, docs y proyectos del cliente.
- Portal colaborador: ve proyectos asignados, habilidades y tareas.
- Botones y CTA solo si el rol lo permite.

---

## Fase 4 - Core reporting e integraciones

### Objetivo

Finalizar el core del producto: integraciones, devices y reportes.

### Entregables

- Integraciones con health, ultima sync y acciones.
- Devices con estado y ultima recoleccion.
- Reportes con historial y ejecuciones.

### Checklist detallado

- Estado de integracion (OK/Warning/Down).
- Timeline de sync.
- Reportes con versionado.

---

## Fase 5 - QA, seguridad y despliegue

### Objetivo

Preparar para produccion.

### Entregables

- Tests de smoke y validaciones por modulo.
- Auditoria completa.
- Hardening de RBAC.
- CI/CD definido.

---

## Backlog detallado por modulo (todo lo faltante)

### Auth

Backend:
- Refresh tokens con expiracion configurable por entorno.
- Bloqueo de cuenta por intentos fallidos (contador + ventana temporal).
- Registro de ultimo login y dispositivo.

Frontend:
- Mensajes claros de error (credenciales invalidas / cuenta bloqueada).
- Indicador de sesion activa y expiracion.
- Redireccion consistente por rol.

UX:
- Mostrar razones de bloqueo y tiempo restante.

Criterios de aceptacion:
- Token de acceso expira y refresh funciona.
- Cuenta bloqueada no permite login hasta pasar el tiempo definido.

### Users / Roles

Backend:
- Campo `avatar_url` en users.
- Endpoint para update de avatar (URL o upload).
- Roles extendidos: `collaborator_admin`, `client_admin`.
- Endpoint `/permissions/me` con permisos agregados.
- Auditoria de cambios de rol/estado.

Frontend:
- Cards con avatar real y fallback.
- Pantalla de permisos por usuario (lista de permisos efectivos).
- Toggle de estado (activo/inactivo).

UX:
- Vista clara de nivel de acceso.
- Badge de rol + badge de nivel.

Criterios de aceptacion:
- Cambio de rol se refleja al recargar permisos.
- Avatar actualizable y visible en cards.

### Clients

Backend:
- Multi-contactos por cliente (client_profiles).
- Historial comercial (estado y notas).
- Vinculo de usuarios cliente a client_id.

Frontend:
- Cards con contacto principal.
- Perfil de cliente con contactos y estado.
- CTA de soporte y solicitudes.

UX:
- Estado comercial visible.
- Acciones segun rol del cliente.

Criterios de aceptacion:
- Cliente puede tener mas de un contacto visible.
- Estado comercial editable por admin.

### Collaborators

Backend:
- Skills/certs con verificacion y aprobacion.
- Disponibilidad y carga (allocation).
- Historial de proyectos (join table).

Frontend:
- Cards con skills visibles y badges.
- Historial de proyectos en detalle.

UX:
- Estado de disponibilidad claro y consistente.

Criterios de aceptacion:
- Skills aprobadas se muestran como verificadas.
- Disponibilidad afecta recomendaciones.

### Projects

Backend:
- Validaciones de estado (no ACTIVE sin miembros).
- Recomendaciones y requisitos de skills.
- Auditoria de cambios de estado.

Frontend:
- Cards + detalle.
- Tabs: Info, Miembros, Docs, Skills, Recomendaciones.
- Asignaciones con roles y porcentaje.

UX:
- Vista de progreso y estado.
- CTA segun rol.

Criterios de aceptacion:
- No se permite activar proyecto sin miembros.
- Recomendaciones visibles en detalle.

### Services

Backend:
- Catalogo con tags y areas.
- Servicios ligados a tipo de proyecto.

Frontend:
- Cards por servicio con filtros.

UX:
- Filtrado por area y tipo.

Criterios de aceptacion:
- Servicios filtran correctamente por area.

### Integrations / Devices

Backend:
- Logs de sync y health.
- Estado de integracion (OK/Warning/Down).

Frontend:
- Estado en tiempo real.
- Timeline de sync.

UX:
- Health indicator claro por integracion.

Criterios de aceptacion:
- Estado cambia segun health.
- Timeline muestra ultima sync.

### Reports

Backend:
- Historial y versionado de reportes.
- Filtros por cliente/proyecto.

Frontend:
- Lista y detalle por cliente.
- KPI resumen.

UX:
- Comparativas y resumen visual.

Criterios de aceptacion:
- Reportes con historial visible.
- KPIs renderizan en cards.

### Audit

Backend:
- Log centralizado por entidad.
- Filtros por usuario/accion/fecha.

Frontend:
- UI con filtros y export.

UX:
- Trazabilidad por entidad.

Criterios de aceptacion:
- Export descarga un CSV/JSON.
- Filtros funcionan por rango.

---

## Orden sugerido de ejecucion

1. Fase 1: backend permisos y reglas.
2. Fase 2: admin proyectos (cards + detalle).
3. Fase 3: portal por rol.
4. Fase 4: core reporting.
5. Fase 5: QA + seguridad.
