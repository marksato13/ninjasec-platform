# Plan de despliegue de 2026-05-22

El borrador original permanece fuera de control de versiones bajo
`DOCUMENTOS/TEMP/PLAN-DEPLOY.md`, por lo que no se propaga ni se puede auditar
desde Git. Se clasifica como historico porque apunta al repositorio anterior,
mezcla dos estrategias de CD incompatibles y asume DuckDNS, SSH y topologia que
pueden no representar el entorno actual.

No ejecutar sus comandos ni copiar sus configuraciones. Para cualquier trabajo
de entrega usar:

1. `../FLUJOS/DESPLIEGUE-PRODUCCION.md` para el despliegue autoalojado vigente.
2. `../PLANIFICACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md` para CI/CD,
   seguridad de supply chain y agentes.
