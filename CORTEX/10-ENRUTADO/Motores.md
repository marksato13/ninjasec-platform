# Motores — lo que está instalado de verdad

Verificado en esta máquina el **2026-11-22**. Si algo no está en esta tabla,
no existe todavía y no se enruta trabajo hacia ahí.

| Motor | Versión | Ejecutable | Autenticación |
| --- | --- | --- | --- |
| **Claude Code** | — | `C:\Users\markp\.local\bin\claude.exe` | OAuth |
| **Codex CLI** | `0.169.0` | `C:\Users\markp\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` | OAuth, `Personal (Plus)` |
| **OpenCode** | `1.19.0` | `C:\Users\markp\scoop\shims\opencode.exe` | configurado |
| **Orca** | `1.4.218` | `C:\Users\markp\AppData\Local\Programs\Orca\resources\bin\orca.exe` | — |

## Claude Code

El motor principal. Es el único que carga `AGENTS.md`, `PY-MK/CLAUDE.md` y la
memoria del proyecto, así que es el único que conoce las reglas que no están
en el código: el 404 en vez de 403, los dos rewrites de `next.config.ts`, la
prohibición de `alert()`.

Modelos que reparte entre sus subagentes, de más a menos caro:

| Modelo | Id | Para qué aquí |
| --- | --- | --- |
| Opus 5 | `claude-opus-5` | T2, T4, T7 — todo lo que decide |
| Sonnet 5.5 | `claude-sonnet-5-5` | T3, T6, T8 — patrón claro, coste medio |
| Haiku 5.5 | `claude-haiku-5-5` | T0 — barridos de solo lectura |

El modelo de un subagente se fija en el `model:` de su archivo en
`.claude/agents/`. Ver [[Agentes]].

## Codex CLI

Segundo par de ojos de otra familia. Se usa **siempre contra un diff
concreto**, nunca para escribir una funcionalidad desde cero en este repo:
no conoce las convenciones y el coste de enseñárselas en cada prompt supera
lo que ahorra.

```powershell
# [LAPTOP PowerShell] -> lo ejecuto yo
codex exec --cd "<ruta del worktree>" "Revisa el diff de HEAD contra origin/main. ¿Qué falla?"
```

Modelo por defecto de la suscripción Plus: **GPT-5.3-Codex** (ventana de
400K). La variante `Spark` existe para respuestas rápidas.

## OpenCode

El motor barato, y el único con acceso a modelos **gratuitos**. Configurado
ya en `C:\Users\markp\.config\opencode\opencode.jsonc` con:

```jsonc
"model":       "openai/gpt-6.1-sol",
"small_model": "openai/gpt-6-luna",
```

y con agentes propios (`dev`, `python`, `netops`, `security`, `cobit`,
`research`, `linux`, `architect`) definidos ahí mismo. Esos agentes son
**generalistas y no conocen NinjaSec**: sirven para consulta, no para
entregar código al repo sin revisión.

Para tareas **T1** se lanza con un modelo gratis explícito:

```powershell
# [LAPTOP PowerShell] -> lo ejecuto yo
opencode run --model opencode/deepseek-v4.1-flash-free "<tarea autocontenida>"
```

Sintaxis del selector: `proveedor/modelo`, con sufijo opcional `#variante`
(por ejemplo `#high`). El proveedor termina en la **primera** barra; el id
del modelo puede llevar más. Distingue mayúsculas.

### Aviso sobre los modelos gratis

Son gratis **por tiempo limitado** y la lista rota. Según la documentación de
OpenCode, solo algunos declaran retención cero y no entrenar con lo enviado;
otros **sí pueden usar lo enviado para mejorar el modelo**.

**Consecuencia operativa:** a un modelo gratis no se le manda nada del
`.env`, ni claves, ni datos de clientes del seed, ni el volcado de la base.
Solo código del repositorio y tareas de forma.

## Orca

Orquestador de worktrees. Útil cuando una tarea necesita su propio árbol y
su propio agente corriendo dentro. Aquí no es obligatorio: los worktrees de
NinjaSec se crean con `git worktree` a mano y está documentado en
[[Worktrees]]. Orca entra cuando haya que lanzar **varios agentes a la vez**
sobre ramas distintas.

Dato que cuesta encontrar: el agente que corre en un worktree **no** se lee
en `worktree.agents` (sale vacío), sino en `agentIdentity` de cada terminal.

Siguiente: [[Catalogo-de-modelos]] · [[Politica-de-enrutado]]
