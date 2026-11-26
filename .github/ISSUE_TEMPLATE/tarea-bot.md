---
name: Tarea para el obrero nocturno (vm-ia)
about: Tarea pequeña y mecánica que un modelo local puede resolver solo y entregar como PR a develop
title: ""
labels: ["bot:listo"]
---

<!--
El obrero nocturno de vm-ia toma los issues con la etiqueta `bot:listo`,
los trabaja con un modelo local y abre un PR hacia develop. Nunca fusiona.

Solo tareas mecánicas: lint, textos, pruebas que faltan, documentación,
arreglos pequeños de pantalla. NUNCA: organization_id, autenticación,
migraciones, secretos, CI ni infraestructura (los rechaza solo).
Tope: unas 400 líneas de cambio.
-->

## Tarea
Qué hay que hacer, en una o dos frases concretas.

## Archivos
- PY-MK/frontend/src/ruta/al/archivo.tsx

## Verificación
$ cd PY-MK/frontend && npx eslint src/ruta/al/archivo.tsx

## Tipo
fix(ambito)
