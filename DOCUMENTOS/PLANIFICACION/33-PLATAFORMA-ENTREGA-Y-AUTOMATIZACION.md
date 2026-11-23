# 33 - Plataforma de entrega segura y automatizacion asistida

> Estado: planificado el 2026-08-23.
> Alcance transversal: no crea una funcionalidad visible para clientes, pero
> protege cada cambio de todos los modulos.

## Objetivo

Construir una cadena de entrega reproducible, segura y de bajo costo para
NinjaSec. Debe validar cada cambio, detectar riesgos antes del merge, promover
versiones trazables y permitir automatizacion asistida por IA sin entregar a un
agente permisos de merge, despliegue o administracion de secretos.

## Fuera de alcance

- Exponer el producto a internet o activar un despliegue real.
- Contratar SaaS de IA, CI/CD o infraestructura por inferencia.
- Ejecutar acciones remotas contra infraestructura de clientes.
- Reemplazar la revision humana por agentes.

## Decisiones de diseno

| Area | Decision |
|---|---|
| CI | GitHub Actions como orquestador, porque el repositorio ya esta en GitHub |
| CD | Promocion separada por entorno; produccion solo con aprobacion humana |
| Seguridad | Gitleaks, Semgrep CE y Trivy como controles complementarios |
| Dependencias | Dependabot con PRs revisables, nunca auto-merge inicial |
| Agentes | PR-Agent primero, en modo comentario; Continue y OpenHands son pilotos locales opcionales |
| Inferencia IA | Local por defecto si se desea costo de licencia cero; la capacidad del equipo es una puerta previa |
| Runners | CI hospedado por GitHub; despliegue autoalojado y aislado solo para refs confiables |

## Pendientes y criterios de aceptacion

| ID | Entregable | Criterio de aceptacion |
|---|---|---|
| `33-P-01` | Inventario y CI base | Existe workflow versionado; en PR ejecuta `PYTHONPATH=. pytest -q` en backend y `npm ci` mas build de frontend |
| `33-P-02` | Calidad y determinismo | Dependencias se instalan de forma reproducible; los checks muestran logs y fallan ante test o build roto |
| `33-P-03` | Gate de secretos | Gitleaks bloquea secretos nuevos y se documenta el proceso de falsos positivos sin guardar secretos reales |
| `33-P-04` | SAST y supply chain | Semgrep CE y Trivy escanean en CI; las severidades que bloquean se acuerdan y quedan versionadas |
| `33-P-05` | Gestion de dependencias | Dependabot crea PRs revisables para Python, Node y GitHub Actions |
| `33-P-06` | Version y staging | Una version identificable se puede desplegar en staging, verificar y revertir sin reconstruir otra rama |
| `33-P-07` | Produccion protegida | El job usa entorno GitHub `production`, aprobacion humana, runner separado, health check y registro de version |
| `33-P-08` | Recuperacion | Existe backup automatizado y una prueba documentada de restauracion antes de cualquier deploy real |
| `33-P-09` | Observabilidad de entrega | Fallos de CI, despliegue y health check generan evidencia consultable; no exponen datos sensibles |
| `33-P-10` | Piloto de PR-Agent | PR-Agent se autoaloja, solo comenta durante dos semanas y se evalua por utilidad, falsos positivos y privacidad |
| `33-P-11` | Pilotos de agentes locales | Continue y OpenHands se prueban aislados sin secretos ni permisos de escritura remota; se decide continuar o descartar con evidencia |

## Gates obligatorios

### Antes de habilitar CD

1. `33-P-01` a `33-P-05` cerrados con ejecuciones verdes.
2. La rama `main` tiene proteccion y checks obligatorios configurados por una persona con permisos de GitHub.
3. Se identifica el destino de staging y se confirma que no contiene datos de produccion.

### Antes de cualquier produccion

1. `33-P-06` a `33-P-09` cerrados.
2. Secretos rotados y almacenados fuera del repositorio.
3. Backup y restauracion verificados con evidencia fechada.
4. Aprobacion humana en el entorno GitHub `production`.
5. Plan de rollback probado contra una version previa.

## Orden de ejecucion

`33-P-01` -> `33-P-02` -> `33-P-03` -> `33-P-04` -> `33-P-05` ->
`33-P-06` -> `33-P-08` -> `33-P-07` -> `33-P-09` -> `33-P-10` -> `33-P-11`.

El trabajo local de producto, incluido `23-P-01`, puede continuar. El CD real
queda bloqueado hasta cumplir las puertas anteriores.

## Referencias

- `../ESTRATEGIA/ARQUITECTURA-CI-CD-Y-AGENTES.md`
- `../ESTRATEGIA/01-CI-Y-CONTROLES-DE-PR.md`
- `../ESTRATEGIA/02-CD-STAGING-Y-RECUPERACION.md`
- `../ESTRATEGIA/03-AGENTES-ABIERTOS-Y-GOBIERNO.md`
- `../ESTRATEGIA/04-GUIA-DE-IMPLEMENTACION-33.md`
- `../ESTRATEGIA/05-STAGING-GRATUITO-ESXI.md`
- `../ESTRATEGIA/06-DECISION-HOSTING-STAGING.md`
- `../ESTRATEGIA/07-PROVISIONAMIENTO-UBUNTU-STAGING.md`
- `../FLUJOS/FLUJO-ENTREGA-SEGURA.md`
- `../FLUJOS/DESPLIEGUE-PRODUCCION.md`
- `../IMPLEMENTACION/00-BACKLOG-GLOBAL.md`
- `../../PY-MK/docs/diagrams/README.md`
