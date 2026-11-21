<!--
Esta plantilla se rellena sola en cada PR. Borra las secciones que no
apliquen, pero no borres la de "Superficie de ataque" sin leerla: NinjaSec
es una plataforma multi-tenant con 4 roles, y ahi es donde se cuelan los
fallos caros.
-->

## Qué hace

<!-- Una o dos frases. Qué cambia para quien usa la plataforma. -->

## Por qué

<!-- El problema, no la solución. Si cierra un pendiente, su ID: NN-P-NN.
     Si cierra un issue: "Closes #numero" (GitHub lo cierra solo al mergear). -->

## Decisiones que tomé

<!-- Lo que elegiste y lo que descartaste, con el motivo. Si no hubo ninguna
     decisión real, borra esta sección. -->

---

## ✅ Definition of Done

Marca solo lo que **ejecutaste**, no lo que crees que pasaría.

- [ ] `cd PY-MK/backend && PYTHONPATH=. pytest -q` pasa
- [ ] `cd PY-MK/frontend && npx tsc --noEmit` limpio
- [ ] `cd PY-MK/frontend && npm run build` pasa
- [ ] `npm audit --audit-level=critical` sin críticas
- [ ] Si toqué el esquema: la migración de Alembic sube **y baja**
- [ ] Documentación actualizada (`IMPLEMENTACION/NN-*.md` con evidencia `archivo:línea`)
- [ ] El pendiente queda **tachado con evidencia**, nunca borrado

### Salida real de las pruebas

<!-- Pega la salida, no la resumas. "Los tests pasan" sin la salida no es
     evidencia: es una afirmación. -->

```
```

---

## 🔐 Superficie de ataque

**Rellena esto aunque el cambio parezca inocuo.**

| Pregunta | Respuesta |
|---|---|
| ¿Endpoints nuevos o modificados? | |
| ¿Qué rol los puede llamar? (`super_admin` / `admin` / `collaborator` / `client`) | |
| ¿Filtran por `organization_id`? | |
| ¿Datos de otra organización devuelven **404** y no 403? | |
| ¿Hay algún endpoint sin autenticar? ¿Tiene rate limiting? | |
| ¿Registra en el audit log vía `AuditService`? | |

### Autorrevisión

- [ ] No hay secretos, tokens ni contraseñas en el código ni en los logs
- [ ] No hay datos sensibles en mensajes de error devueltos al cliente
- [ ] Si añadí dependencias: revisé sus vulnerabilidades conocidas
- [ ] Si el cambio afecta a producción: las guardas de `IS_PRODUCTION` siguen activas

---

## Lo que NO hace este PR

<!-- Alcance que dejaste fuera a propósito, y por qué. Evita la pregunta
     "¿y por qué no arreglaste también...?" en la revisión. -->

## Riesgos conocidos

<!-- Lo que puede salir mal, y cómo se revierte. Si no hay ninguno, dilo
     explícitamente: "ninguno, el cambio es aditivo y no toca datos". -->
