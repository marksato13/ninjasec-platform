---
pendiente: NN-P-NN
clase: T?
motor:
modelo:
estado: abierto
rama:
worktree:
pr:
---

# NN-P-NN — <título>

> **Regla de esta ficha:** separa siempre lo que **verificaste** de lo que
> **supones**. Todo hecho lleva evidencia (`archivo:línea`, commit o salida
> de comando). Un supuesto sin confirmar nunca se escribe como hecho.

## Identificación

| | |
| --- | --- |
| Pendiente | `NN-P-NN` |
| Módulo | `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-....md` |
| Rama | `<tipo>/<slug>` |
| Worktree | `ninjasec-wt-<tema>` |
| Base (`origin/main`) | `<sha>` |
| Fecha | |

## Despacho

Rellenado por `/ns-despachar`. Ver [[Politica-de-enrutado]].

| | |
| --- | --- |
| **Clase** | T? |
| **Motor** | Claude principal / subagente `ns-*` / Codex / OpenCode |
| **Modelo** | |
| **Motivo** | Por qué esa clase y no la de al lado |
| **Qué se le entrega** | El contexto exacto, si es un motor sin las reglas del repo |
| **Cómo se verifica** | Qué prueba dice sí o no |

Si la clase es **T4**, aquí solo cabe: *Claude principal, Opus 5, no se delega.*

## Criterios

| # | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| CA-1 | | cubierto / parcial / ausente / no verificable | `archivo:línea` |
| CA-2 | | | |

## Hechos auditados

- **Hecho:** … · *Evidencia:* `PY-MK/backend/app/...:42`

## Supuestos

- **Supuesto:** … · *Confirma:* <quién>

## Decisiones pendientes

- **Decisión:** … · *Decide:* <quién> · *Bloquea:* sí / no

## Alcance

Qué entra. Solo los criterios marcados ausente o parcial.

## Fuera de alcance

Qué **no** entra, explícito, para que nadie lo espere en la revisión.

## Plan técnico

| Capa | Archivos |
| --- | --- |
| modelos | |
| migración | |
| servicios | |
| rutas | |
| frontend | |
| pruebas | |

## Aislamiento multi-tenant

Obligatorio si la tarea toca una ruta protegida o una consulta.

| Ruta | Método | Rol | ¿Filtra por `organization_id`? | ¿404 en vez de 403? |
| --- | --- | --- | --- | --- |

## Migraciones

¿Cambia el esquema? Nombre del archivo, `down_revision` y qué hace.
Comprobar que los índices del modelo y los de la migración coinciden: el
descuadre lo caza `test_alembic_bootstrap`, pero tarde.

## Plan de pruebas

| Prueba | Tipo | Estado |
| --- | --- | --- |
| | unitaria / integración / e2e | pendiente / pasa / falla |

## Verificación

Marca **solo** lo que ejecutaste.

- [ ] `PYTHONPATH=. pytest -q`
- [ ] `npm ci` + `npm run build`
- [ ] `npm audit --audit-level=critical`
- [ ] `gitleaks protect --staged --no-banner --redact`
- [ ] `git diff --check`
- [ ] Sin `.env`, secretos, caches ni logs en el diff

No ejecutado y por qué:

## Riesgos

## Entrega

| | |
| --- | --- |
| PR | |
| Estado del CI | |
| Checklist de `IMPLEMENTACION/` | tachado con evidencia / pendiente |
