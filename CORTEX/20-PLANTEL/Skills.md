# Skills

Una *skill* es conocimiento que se carga solo cuando hace falta, por su
descripción. A diferencia de `AGENTS.md`, que se carga siempre, una skill no
ocupa contexto hasta que la tarea la pide.

## Del repositorio — `.claude/skills/`

| Skill | Se carga cuando |
| --- | --- |
| `ninjasec-puertas-ci` | Al verificar, antes de commit o push, o si un PR sale en rojo |
| `ninjasec-multitenant` | Al tocar una ruta protegida, una consulta con `organization_id` o un modelo con tenant |
| `ninjasec-enrutado` | Al decidir a qué motor va una tarea, o al mencionar Codex, OpenCode o delegar |

Las tres son **del repositorio**: viajan con él, así que valen en cualquier
worktree y en cualquier máquina donde se clone.

## Globales de la máquina — `~/.claude/skills/`

Instaladas en el sistema. Las que tienen sentido aquí:

| Skill | Para qué en NinjaSec |
| --- | --- |
| `diagramas-arquitectura` | Diagramas `.drawio` para entregables de cliente |
| `diagramas-red` | Topologías con iconos oficiales de Fortinet, Cisco, pfSense |
| `esxi` | El laboratorio donde iba el staging |
| `fortigate-firewall-audit` | Auditorías de FortiGate — es servicio vendible |
| `configuring-pfsense-firewall-rules` | Igual, con pfSense |
| `cisco-device-health` | Triaje de equipos Cisco |
| `code-review` | Revisión del diff antes de abrir PR |
| `orchestration` / `orca-cli` | Cuando haya que coordinar varios agentes a la vez |

Las cuatro de redes y firewalls no son decoración: son exactamente los
equipos sobre los que NinjaSec promete informes. Cuando los conectores dejen
de estar simulados, esas skills son el puente entre lo que la plataforma
dice y lo que la consultora sabe hacer a mano.

## Las que no se activan aquí

`audio-transcription`, `meeting-transcript-analysis`, `herdr`,
`orquestador-tesis`, `revision-articulo-ijies`, `similitud-articulo` y los
revisores de la tesis son de otros proyectos. No estorban, pero no se
invocan desde este repo.

## Criterio para escribir una skill nueva

Se escribe una skill cuando el conocimiento cumple **las tres**:

1. Es **repetido** — se necesita en más de una tarea.
2. Es **específico de este repo** — no lo sabe un modelo por su cuenta.
3. Es **caro de equivocarse** — el error no salta en el diff.

`ninjasec-multitenant` es el ejemplo perfecto: la regla de devolver 404 en
vez de 403 no se deduce del código, se repite en cada ruta y equivocarse
confirma la existencia de datos de otro cliente.

Ver también: [[Agentes]] · [[MCP]]
