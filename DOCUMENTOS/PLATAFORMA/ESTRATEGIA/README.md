# Estrategia de Plataforma

Esta carpeta contiene decisiones que afectan a varios modulos y no pertenecen
a una pantalla o entidad de negocio concreta. La especificacion ejecutable de
cualquier trabajo transversal conserva su par en `PLANIFICACION/` e
`IMPLEMENTACION/`.

| Documento | Responde |
|---|---|
| [`ARQUITECTURA-CI-CD-Y-AGENTES.md`](ARQUITECTURA-CI-CD-Y-AGENTES.md) | Cual es la arquitectura objetivo de entrega segura y automatizacion asistida |
| [`01-CI-Y-CONTROLES-DE-PR.md`](01-CI-Y-CONTROLES-DE-PR.md) | Como implementar CI, checks obligatorios y controles de PR |
| [`02-CD-STAGING-Y-RECUPERACION.md`](02-CD-STAGING-Y-RECUPERACION.md) | Como promover versiones, proteger produccion y recuperar el servicio |
| [`03-AGENTES-ABIERTOS-Y-GOBIERNO.md`](03-AGENTES-ABIERTOS-Y-GOBIERNO.md) | Como pilotar agentes abiertos sin aumentar privilegios |
| [`04-GUIA-DE-IMPLEMENTACION-33.md`](04-GUIA-DE-IMPLEMENTACION-33.md) | En que orden implementar los once pendientes del modulo 33 |
| [`05-STAGING-GRATUITO-ESXI.md`](05-STAGING-GRATUITO-ESXI.md) | Como preparar staging gratis, aislado y listo para CD futuro |
| [`06-DECISION-HOSTING-STAGING.md`](06-DECISION-HOSTING-STAGING.md) | Que host elegir para staging y cuando usar Cloudflare Tunnel u Oracle |
| [`07-PROVISIONAMIENTO-UBUNTU-STAGING.md`](07-PROVISIONAMIENTO-UBUNTU-STAGING.md) | Que instalar y como preparar Ubuntu Server para staging privado |
| [`../PLANIFICACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md`](../PLANIFICACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md) | Que se debe construir y con que criterios |
| [`../IMPLEMENTACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md`](../IMPLEMENTACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md) | Que esta pendiente y que evidencia lo cierra |

## Regla de costo

El software seleccionado puede ser gratuito o de codigo abierto, pero la
ejecucion no necesariamente es gratuita: runners, almacenamiento, red y
modelos locales requieren infraestructura. Ningun servicio de pago se activa
ni se contrata sin una decision explicita.

## Diagramas

No hace falta instalar un MCP para Mermaid. Los diagramas en bloques
`mermaid` se renderizan en GitHub, y Draw.io ya esta disponible para diagramas
editables que requieran posicionamiento exacto.
