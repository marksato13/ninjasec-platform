# Documentacion de la plataforma

Indice operativo de la documentacion de **desarrollo**. Lo comercial, legal,
financiero y de marketing ya **no esta aqui**: vive en el repositorio
[`ninjasec-empresa`](https://github.com/marksato13/ninjasec-empresa), y la
politica de agentes y enrutado en
[`ninjasec-dev-workspace`](https://github.com/marksato13/ninjasec-dev-workspace).

Indice operativo de la documentacion de la plataforma. La estructura evita
mezclar requisitos de producto, evidencias de implementacion y material que ya
no debe guiar despliegues.

| Ubicacion | Proposito | Cuando actualizar |
|---|---|---|
| `PLANIFICACION/` | Especificacion funcional y tecnica de cada modulo | Antes de implementar un modulo o pendiente |
| `IMPLEMENTACION/` | Checklist, evidencias y pendientes por modulo | Durante y despues de cada cambio |
| `ESTRATEGIA/` | Decisiones transversales de plataforma, entrega y automatizacion | Al cambiar arquitectura u operacion transversal |
| `FLUJOS/` | Procesos que cruzan dos o mas modulos | Al modificar el proceso completo |
| `FIX/` | Post-mortems de cambios puntuales | Al cerrar un fix relevante |
| `HISTORICO/` | Planes reemplazados o contexto no operativo | Nunca como fuente de verdad |
| `ROADMAP.md` | Orden, prioridad y decisiones pendientes | Al reordenar o cerrar una tanda |

## Como empezar

1. Revisa [`ROADMAP.md`](ROADMAP.md) para conocer el orden de trabajo.
2. Consulta [`IMPLEMENTACION/00-BACKLOG-GLOBAL.md`](IMPLEMENTACION/00-BACKLOG-GLOBAL.md) para el inventario de pendientes.
3. Abre el par `PLANIFICACION/NN-*.md` y `IMPLEMENTACION/NN-*.md` del modulo.
4. Para CI/CD, seguridad de entrega y agentes, sigue [`ESTRATEGIA/`](ESTRATEGIA/README.md) y el modulo 33.

Los diagramas de producto editables viven en `PY-MK/docs/diagrams/`. Mermaid
puede vivir dentro de Markdown y GitHub lo renderiza directamente.
