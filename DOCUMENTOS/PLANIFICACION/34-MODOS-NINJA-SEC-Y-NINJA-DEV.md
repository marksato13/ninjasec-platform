# 34 - Modos Ninja Sec y Ninja Dev

> Estado: planificado el 2026-11-25, a pedido del usuario.
> Depende de: `#36` (menú ordenado por flujo) y del sistema visual con temas
> `ninja-sec` y `ninja-dev`.

## Objetivo

La empresa tiene dos áreas con trabajo muy distinto. Hoy todo se ve mezclado:
un super admin que está atendiendo un desarrollo ve NetDoctor, riesgos y
vulnerabilidades, y no ve nada propio de desarrollo.

Se añade un **selector de modo** en la cabecera del panel: **Todo · Ninja Sec ·
Ninja Dev**. El modo cambia qué se muestra, nunca qué se puede hacer.

## Decisiones de diseño

| Tema | Decisión | Por qué |
|---|---|---|
| Qué es el modo | Una **preferencia de vista**, no un permiso | Los permisos siguen en `require_roles` y `organization_id`. Un modo nunca abre ni cierra un endpoint |
| Dónde se guarda | En el navegador (`localStorage`, con `try/catch`), con `Todo` por defecto | Es una comodidad por persona; no hace falta tabla |
| Quién lo ve | Super admin y admin. El colaborador entra en el modo de su área si solo tiene una, y en `Todo` si tiene ambas | Un colaborador de Dev no necesita las herramientas de Sec |
| Cómo se sabe el área de un proyecto | Columna nueva `areas.business_line` (`sec`, `dev` o vacía) | Hoy se adivina por el texto del slug ("sec", "dev"), y eso falla con un área llamada "Redes" |
| Cómo se sabe el área de una opción del menú | Campo `linea` en cada `Opcion` de `app/core/navegacion.py`: `sec`, `dev` o `comun` | El menú ya viene del servidor; se filtra donde ya se decide qué se muestra |
| Aspecto | El modo activa el tema `ninja-sec` (esmeralda) o `ninja-dev` (violeta) | Se nota al instante en qué modo estás |

## Qué cambia en cada pantalla

| Pantalla | Todo | Ninja Sec | Ninja Dev |
|---|---|---|---|
| **Menú** | Todo | Comercial, Operación, **Herramientas Ninja Sec**, Equipo, Control | Comercial, Operación, **Herramientas Ninja Dev**, Equipo, Control |
| **Dashboard** | Las dos áreas lado a lado | Proyectos de seguridad, revisiones, riesgos altos, vulnerabilidades abiertas, ventanas pendientes | Proyectos de desarrollo por fase, entregas de la semana, despliegues, tickets de soporte de sistemas |
| **Proyectos** | Todos, con etiqueta de área | Solo proyectos del área Sec | Solo proyectos del área Dev, con vista de sprints o fases |
| **Servicios** | Todo el catálogo | Servicios del área Sec | Servicios del área Dev |
| **Clientes** | Todos | Clientes con algún proyecto o servicio Sec | Clientes con algún proyecto o servicio Dev |
| **Tickets** | Todos | Del área Sec | Del área Dev |
| **Formación** | Todo | Certificaciones de seguridad y redes | Certificaciones de desarrollo y nube |

Lo común (Leads, Clientes, Tickets, Equipo, Control) aparece en los dos
modos, filtrado cuando tiene sentido.

## Herramientas Ninja Dev (nuevas en el menú)

Se apoyan en la guía `DOCUMENTOS/NINJA-DEV/` (redactada con Codex, revisada a
mano). La regla del usuario: **no llenar la plataforma de módulos**. Primero
se muestra la guía; solo se convierte en módulo lo que ahorra trabajo real.

| Opción | Qué es | ¿Módulo o guía? | Esfuerzo |
|---|---|---|---|
| **Guía Ninja Dev** | Flujo de trabajo, reuniones con el cliente, documentos, stack recomendado, despliegues, uso de IA con referencias | Guía (como la Guía SGSI) | S |
| **Estimador de costos** | Horas por tarea × tarifa + infraestructura + licencias + soporte; exporta a la plantilla de cotización | **Módulo**: calcula y se guarda en el proyecto | M |
| **Planes de servicio** | Básico, Profesional, A medida y mantenimiento mensual, sin precios en la plataforma | Guía; los precios siguen en `ninjasec-empresa` | S |
| **Registro de despliegues** | Qué versión se desplegó, dónde, quién y cómo se vuelve atrás | **Módulo**, colgado del proyecto | M |
| **Documentos desde plantilla** | Propuesta, alcance, acta de kickoff y de conformidad, rellenados con los datos del proyecto | **Módulo**: reutiliza `PLANTILLAS` de `ninjasec-empresa` | L |
| **Catálogo de stack** | Stack recomendado por tipo de proyecto | Guía | S |

## Orden de trabajo

1. **Datos** (T4, agente principal): migración `areas.business_line`, con
   relleno inicial desde el slug y el nombre y prueba de subida y bajada en
   PostgreSQL desechable. Respaldo de producción antes de desplegar.
2. **Menú** (T4): `linea` en cada `Opcion`; `/navigation/me` la devuelve;
   prueba que fija qué opciones son `sec`, `dev` y `comun`.
3. **Selector de modo y tema** (T3): cabecera, `localStorage` y tema.
4. **Dashboard por modo** (T3): reutiliza los widgets del dashboard honesto
   (`#34`); solo datos reales.
5. **Filtros por modo** en Proyectos, Servicios, Clientes y Tickets (T3), con
   el área que ya devuelven los endpoints.
6. **Guía Ninja Dev** en `/dashboard/ninja-dev` (T3), leyendo los Markdown.
7. Después, uno por uno y con su propio PR: estimador, registro de
   despliegues y documentos desde plantilla.

## Criterios de aceptación

- Cambiar de modo no cambia ninguna respuesta del backend que no sea un
  filtro pedido por el propio frontend; un usuario en modo Dev que abre una
  URL de Sec la ve igual si su rol lo permite.
- Sin `business_line`, un área cuenta como de las dos líneas: nada desaparece
  por falta de datos.
- Las pruebas de menús por rol siguen pasando y fijan la `linea` de cada
  opción.
- El modo elegido sobrevive a recargar la página y no rompe con el
  almacenamiento bloqueado.

## Fuera de alcance

- Permisos distintos por área (un colaborador de Dev que no pueda ver Sec).
  Si se necesita, es un pendiente aparte con su propia revisión de seguridad.
- Gestión de tareas o sprints dentro de la plataforma: se hace en ClickUp.
