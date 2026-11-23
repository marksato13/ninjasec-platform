# Agentes

Los agentes viven en `.claude/agents/` en la raíz del repo, porque ahí es
donde Claude Code los busca. Esta página es su ficha: qué hacen, qué modelo
les toca y —lo importante— **qué no pueden hacer**.

El modelo no es decorativo. Está en el `model:` del archivo de cada agente y
aplica la [[Politica-de-enrutado]] por construcción, no por buena voluntad.

| Agente | Clase | Modelo | ¿Escribe? | Para qué |
| --- | --- | --- | --- | --- |
| `ns-explorador` | T0 | **haiku** | **No** | Barrer el repo y devolver rutas y líneas, no volcados |
| `ns-auditor-tenant` | T4 | **opus** | **No** | Auditar aislamiento multi-tenant en rutas y consultas |
| `ns-backend` | T2 | **opus** | Solo `PY-MK/backend` | Implementar un pendiente de backend con su prueba |
| `ns-frontend` | T3 | **sonnet** | Solo `PY-MK/frontend` | Pantallas y componentes |
| `ns-revisor-ci` | T8 | **sonnet** | **No** | Replicar las puertas del CI y reportar sin maquillar |

## Por qué tres de ellos no tienen `Edit` ni `Write`

`ns-explorador`, `ns-auditor-tenant` y `ns-revisor-ci` tienen la lista de
herramientas recortada en su propio archivo. No es una convención escrita en
el prompt que el modelo pueda ignorar: **la herramienta no existe para ellos**.

Es la misma defensa que en el proyecto hermano, y existe por un motivo
concreto: un revisor que puede arreglar lo que encuentra deja de reportarlo.

## El que no está en la tabla

El **agente principal** —la sesión de Claude Code que abres tú— es el que
hace todo lo de clase T4 y T7: seguridad, tenancy, migraciones, decisiones
y redacción comercial. No se delega, y por eso no tiene ficha: *es* la
sesión.

## Agentes de otros motores

OpenCode tiene sus propios agentes en
`C:\Users\markp\.config\opencode\opencode.jsonc` (`dev`, `python`, `netops`,
`security`, `cobit`, `research`, `linux`, `architect`). Son **generalistas y
no conocen NinjaSec**: no han leído `AGENTS.md` ni `PY-MK/CLAUDE.md`.

Sirven para consultar, no para entregar al repo sin revisión. Si uno de
ellos escribe código que acaba en un PR, pasa por [[Puertas-de-CI]] igual
que el resto.

## Criterio para añadir uno nuevo

El mismo que se aplicó en `francos-dev-workspace` y que ahorró media
configuración desincronizada:

> **Un agente se crea cuando algo ha fallado al menos una vez por no
> tenerlo.** Un agente creado «por si acaso» es una regla más que mantener
> al día.

Candidatos que **todavía no existen** y bajo qué condición tendrían sentido:

| Agente | Cuándo tendría sentido |
| --- | --- |
| `ns-migraciones` | Si las migraciones de Alembic dejan de ser excepcionales. Hoy son T4 y las hace el principal |
| `ns-escritor-pruebas` | Si escribir pruebas se vuelve el cuello de botella |
| `ns-conectores` | Cuando los conectores dejen de ser simulados y haya protocolo real que hablar |

Ver también: [[Skills]] · [[MCP]] · [[Automatizaciones]] · [[Politica-de-enrutado]]
