# Automatizaciones y bots

Trabajo que corre **sin que nadie lo lance**. Es la parte con más valor por
hora y también la que más silencio produce cuando se rompe, así que cada
entrada dice qué hace, cuándo y **qué pasa si falla**.

## Lo que ya corre en GitHub

| Bot | Cuándo | Qué hace | Si falla |
| --- | --- | --- | --- |
| **CI** (`.github/workflows/ci.yml`) | Cada PR y cada push a `main` y `develop` | `backend-tests`, `frontend-build`, `security` | El PR no se puede fusionar: los checks son obligatorios |
| **Security** (`security.yml`, reusable) | Lo llama el CI | Gitleaks, Semgrep CE, Trivy filesystem | Igual: son tres checks obligatorios |
| **Dependabot** | Programado | Agrupa actualizaciones de pip, npm y GitHub Actions | Se acumulan PR; hay ~16 abiertos |

Los cinco checks obligatorios en `main` y en `develop`, con su nombre exacto:

```
Backend tests
Frontend build
Security / Gitleaks
Security / Semgrep CE
Security / Trivy filesystem
```

Además `strict: true`: la rama tiene que estar al día con su base antes de
fusionar. Y `allow_force_pushes: false`.

> **Cuidado con los nombres.** Llevan separadores y espacios exactos. Una
> vez se escribieron en ASCII y el `·` se convirtió en `?`: eso deja la rama
> bloqueada para siempre, porque espera un check que nunca va a existir.
> Si hay que tocarlos, se leen primero de la API, nunca se escriben de memoria.

## Lo que todavía no existe

| Automatización | Qué haría | Cuándo montarla |
| --- | --- | --- |
| **Copia de seguridad de Postgres** | Volcado diario con retención | **Bloquea el despliegue público.** Hoy `./backups` es un punto de montaje vacío |
| **Vigía de PR** | Avisar de PR verdes sin fusionar y de CI en rojo | Cuando haya más de una persona abriendo PR |
| **Vigía de dependencias** | Resumir los Dependabot abiertos y cuáles son críticos | Ya tendría sentido: hay ~16 |
| **Despliegue continuo** | Publicar en cada merge a `main` | Después de la primera exposición pública, que es decisión tuya |

## Si se montan con Orca

Orca sabe programar automatizaciones (`orca automations create`). Dos reglas
que salieron de usarlo en el proyecto hermano:

1. **Se crean con `--disabled`.** Se ejecutan a mano una vez, se revisa el
   resultado y solo entonces se activan. Una automatización que escribe en
   el repo sin haberse probado es ruido en el historial.
2. **Que escriban documentación, no código.** Las tres del proyecto hermano
   son de lectura: vigilan y actualizan una página. Ninguna toca el producto.

## La frontera

Ninguna automatización fusiona, despliega, gasta dinero ni crea cuentas.
Eso está en [[Frontera-de-autonomia]] y no cambia porque el bot tenga prisa.

Ver también: [[Puertas-de-CI]] · [[MCP]]
