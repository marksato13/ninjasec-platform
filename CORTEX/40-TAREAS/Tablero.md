# Tablero

Trabajo real de NinjaSec al **2026-11-22**, ya clasificado según
[[Politica-de-enrutado]]. Esta página se actualiza con `/ns-inbox`.

La columna **Clase** no es una etiqueta: decide quién lo hace. Una tarea T4
no baja a T2 porque haya prisa.

## En vuelo — PR abiertos

| PR | Qué | Clase | Estado |
| --- | --- | --- | --- |
| #134 | Decisión de hosting con costes en soles | T7 | Verde, listo |
| #133 | Mapa guía del SGSI | T3 | Verde, listo |
| #132 | Índices de FK y `services.slug` compuesto | T4 | Verde, listo |
| #131 | Tres fugas multi-tenant | **T4** | Verde, listo |
| #128 | Playwright y E2E en Docker | T8 | **Rojo** en `E2E · Playwright` |
| #117 | Staging sobre ESXi | T7 | **Rojo** en `Frontend build` y `Security / Trivy filesystem` — la rama es de septiembre y arrastra el Next vulnerable. Lo reemplaza #134 |

Más **5 PR de Dependabot** sin triar. Clase T1: son mecánicos, pero el diff
se lee entero porque tocan dependencias.

## Bloquea el despliegue público

| # | Qué | Clase | Quién |
| --- | --- | --- | --- |
| 1 | Contraseñas del seed en texto plano (`admin@ninjasec.local` / `change-me`) | **T4** | Claude |
| 2 | Rotar los secretos G-03 | — | **Mark.** Acción humana |
| 3 | Copias de seguridad de Postgres — `./backups` es un punto de montaje vacío | T2 | Claude |

## Sin commitear

`ninjasec-wt-payload` lleva días con ocho modelos modificados
(`VARCHAR` → `TEXT`) y la migración `20261121_02_payloads_a_text.py` sin
añadir a git. **Clase T1 de código, pero T4 de revisión**: es una migración.

## De la auditoría de base de datos

| Gravedad | Qué | Clase |
| --- | --- | --- |
| Alta | `devices` sin `organization_id`; el tenant sale de un `OR` de dos claves foráneas nulables | **T4** |
| Alta | Borrar un usuario devuelve 500 y no 409 — faltan `ondelete` y un manejador de `IntegrityError` | **T4** |
| Media | `job_applications` sin `organization_id`: datos de candidatos globales | **T4** |
| Media | `UserSkill.level` texto libre, interpretado por subcadenas en inglés con la interfaz en español | T2 |
| Media | `/audit-logs/` sin paginación sobre la tabla que más crece | T2 |
| Media | El panel materializa entidades para contarlas en Python en vez de `func.count()` | T2 |

## Lo que ya no es deuda técnica

**Los conectores están simulados.** `simulate_connector_test()` devuelve
`"reachable": true` sin contactar ningún equipo, y encima de esa mentira
corren el informe SOC, el *hardening* y el índice de salud.

Clase **T2 grande**, y es lo único de esta página que es un **bloqueante
comercial**, no técnico: el primer cliente que pida conectar su firewall en
una demo lo descubre en un minuto.

## Aparcado por decisión de Mark

| Qué | Nota |
| --- | --- |
| Corpus de plantillas de SGSI en español | No existe nada libre equivalente. La pieza de más valor |
| `sgsi-docgen` | Portar la generación de Word. El manifiesto ya funciona y pasa sus 8 pruebas |
| `02-P-06` | 13 `useEffect` con `setState` síncrono, hoy en `warn` |
| Matriz `deny` de permisos | Requiere decisión de Mark. Ver [[Frontera-de-autonomia]] |

## Decisión abierta que bloquea

**¿Los dos sistemas adicionales son estáticos de verdad, o alguno necesita
backend?** Estáticos: VPS de 4 GB, ~S/ 250 al año. Con backend: 8 GB,
~S/ 430. Decide Mark.

Ver también: [[Ciclo-de-vida]] · [[TEMPLATE]]
