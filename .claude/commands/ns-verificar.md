---
description: Corre las puertas del CI de NinjaSec en local y revisa el diff antes del PR
argument-hint: 12-P-03
---

Verifica la entrega de **$1** con el subagente `ns-revisor-ci`.

Lánzalo con el diff actual y su ficha, y pídele las puertas una por una.
**No lo hagas tú en el hilo principal**: el revisor no tiene `Edit` ni
`Write` a propósito, y esa es justamente la garantía de que reporta en vez
de arreglar.

## Lo que tiene que volver

```
Backend tests               <resultado real>
Frontend build              <resultado real>
npm audit                   <resultado real>
Security / Gitleaks         <resultado real>
Security / Semgrep CE       no ejecutada en local - solo corre en CI
Security / Trivy filesystem no ejecutada en local - solo corre en CI
```

Más la revisión del diff: secretos, pruebas que fallan sin el cambio,
índices de migración frente a modelos, `alert()`, los *rewrites* de
`next.config.ts`, y que el PR cubra un solo pendiente.

## Qué haces con el resultado

1. **Si hay rojo:** vuelve a implementar. No abras PR. Un PR en rojo es un
   viaje perdido y, con `strict: true`, tampoco se puede fusionar.
2. **Si hay puertas no ejecutadas:** anótalas en la ficha con el motivo.
   Semgrep y Trivy solo corren en CI; eso es un motivo válido. «No me dio
   tiempo» no lo es.
3. **Si toca `organization_id`, autenticación o Alembic:** lanza además
   `ns-auditor-tenant` antes de seguir. Es clase T4 y no se fía de las
   puertas genéricas.

## Rellenar la ficha

Marca en el bloque **Verificación** solo lo que se ejecutó de verdad, y
escribe debajo lo que no, con su motivo.

Lo que no se corrió no se marca. Esta es la regla que más entregas falsas ha
evitado en este repositorio.

## Al terminar

Di si se puede pasar a `/ns-pr $1` o qué falta. Nada más.
