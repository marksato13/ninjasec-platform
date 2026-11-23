---
name: ninjasec-enrutado
description: Decide a qué motor y a qué modelo va una tarea de NinjaSec — Claude Opus, Sonnet, Haiku, Codex CLI u OpenCode. Usar al clasificar un pendiente, al plantearse delegar trabajo, al mencionar Codex, OpenCode, subagentes o coste de cuota, y siempre antes de mandar código a un motor que no sea Claude.
---

# Enrutado de tareas en NinjaSec

Hay tres motores en esta máquina y entre todos dan acceso a modelos de
gratis a $180 por millón de tokens de salida. La decisión se toma por
**radio de daño**, no por precio.

Detalle completo en `CORTEX/10-ENRUTADO/Politica-de-enrutado.md`.

## La pregunta que decide

> ¿Este cambio puede filtrar datos de otro tenant, romper el login, perder
> datos o exponer un secreto?

**Si la respuesta es sí: clase T4. Claude principal, Opus 5, no se delega.**
Fin. No hay más preguntas.

Entra en T4 todo lo que toque:

- `PY-MK/backend/app/core/` — configuración, seguridad, dependencias
- cualquier consulta o ruta con `organization_id`
- cualquier migración de Alembic
- `.env`, seed de contraseñas, JWT, configuración de producción

Motivo: ahí es exactamente donde ya hubo fallos reales —`IS_PRODUCTION`
ignorado, tres fugas de tenant, `services.slug` único globalmente— y donde
el fallo **no se ve en el diff si no conoces la regla**.

## El resto

| Clase | Qué es | Motor | Modelo |
| --- | --- | --- | --- |
| T0 | Barrido de solo lectura | `ns-explorador` | haiku |
| T1 | Mecánica repetida, diff revisable entero | OpenCode | `opencode/deepseek-v4.1-flash-free` |
| T2 | Backend acotado con prueba | `ns-backend` | opus |
| T3 | Frontend | `ns-frontend` | sonnet |
| **T4** | **Seguridad, tenancy, auth, migraciones** | **principal** | **opus** |
| T5 | Segunda opinión sobre un diff | Codex CLI | GPT-5.3-Codex |
| T6 | Investigación con fuentes | subagente + WebSearch | sonnet |
| T7 | Negocio y redacción | principal | opus |
| T8 | Verificación de puertas | `ns-revisor-ci` | sonnet |

Si dudas entre dos clases, **gana la más cara**. Equivocarse hacia arriba
cuesta cuota; hacia abajo cuesta un incidente.

## Antes de mandar algo fuera de Claude

Codex y OpenCode **no han leído `AGENTS.md`**. No saben que los datos de
otro tenant devuelven 404 y no 403, que no se usa `alert()`, que
`from __future__ import annotations` no se quita de los servicios con
`def list`.

Tres condiciones para delegarles trabajo:

1. **Autocontenido.** Un archivo, un patrón, un diff. Nunca «mira el repo».
2. **Sin nada sensible.** Ni `.env`, ni claves, ni datos del seed de
   clientes, ni volcados de base. Hay modelos gratis cuya documentación dice
   que **pueden entrenar con lo enviado**.
3. **Verificable.** Tiene que haber una prueba que diga sí o no.

Lo que devuelven es una **propuesta**, no una entrega: pasa por las puertas
del CI igual que el resto.

```bash
codex exec --cd "<worktree>" "Revisa el diff de HEAD contra origin/main. ¿Qué falla?"
opencode run --model opencode/deepseek-v4.1-flash-free "<tarea autocontenida>"
```

A Codex se le da el diff **sin contarle la intención**: si le explicas qué
pretendías, confirma tu sesgo en vez de romperlo.

## La cuota

El cuello de botella es la ventana **semanal**, no el precio por token. El
trabajo largo va al motor con la ventana más holgada.

**T4 no entra en ese cálculo.** Si no hay cuota de Opus, se espera.
