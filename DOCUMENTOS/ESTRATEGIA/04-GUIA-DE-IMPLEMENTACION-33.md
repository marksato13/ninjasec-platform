# Guia de implementacion del modulo 33

Esta es la secuencia de trabajo para implementar CI/CD y agentes sin saltar
puertas de seguridad. Cada fase debe abrir su propia rama, actualizar el
checklist `IMPLEMENTACION/33-PLATAFORMA-ENTREGA-Y-AUTOMATIZACION.md` y pasar la
verificacion proporcional antes de iniciar la siguiente.

## Orden y entregables

| Fase | Pendientes | Resultado | Requiere decision humana |
|---|---|---|---|
| 1 | `33-P-01`, `33-P-02` | CI de backend y frontend | Checks obligatorios de `main` |
| 2 | `33-P-03`, `33-P-04` | Escaneo de secretos, SAST y supply chain | Severidades bloqueantes y excepciones |
| 3 | `33-P-05` | Dependabot configurado | Cadencia de actualizaciones |
| 4 | `33-P-06`, `33-P-08` | Artefactos, staging y recuperacion probada | Host/registro OCI y destino desechable |
| 5 | `33-P-07`, `33-P-09` | CD protegido a produccion y evidencia | Entorno GitHub, aprobadores y runner |
| 6 | `33-P-10`, `33-P-11` | Pilotos de agentes abiertos | Hardware, privacidad y continuidad |

## Fase 1: CI reproducible

1. Auditar el workflow CI existente y conservar su prueba Alembic con
   PostgreSQL efimero, auditoria npm critica y permisos minimos en `33-P-01`.
2. Ampliar `.github/workflows/ci.yml` segun
   `01-CI-Y-CONTROLES-DE-PR.md`.
3. Ejecutar localmente los mismos comandos antes de abrir PR:

   ```bash
   cd PY-MK/backend
   PYTHONPATH=. pytest -q
   ```

   ```bash
   cd PY-MK/frontend
   npm ci
   NEXT_PUBLIC_API_URL=/api/v1 npm run build
   ```

4. Validar en GitHub mediante una PR de prueba. No marcar el pendiente como
   cerrado sin URL de ejecucion verde y sin comprobar un fallo controlado.

## Fase 2: seguridad de pipeline

1. Agregar configuraciones de Gitleaks, Semgrep CE y Trivy.
2. Escanear primero el estado actual para clasificar resultados heredados.
3. Corregir resultados reales antes de crear exclusiones. Cada excepcion debe
   incluir motivo, responsable y fecha de expiracion.
4. Volver bloqueante Gitleaks de inmediato; endurecer Semgrep y Trivy en una
   PR posterior cuando su linea base sea conocida.
5. Ejecutar el secreto de prueba solamente en una rama desechable y removerlo
   antes de compartir logs o artefactos.

## Fase 3: dependencias

1. Crear `.github/dependabot.yml` para `PY-MK/backend`, `PY-MK/frontend` y
   GitHub Actions de la raiz.
2. Configurar grupos pequenos y frecuencia semanal para que los PRs sean
   revisables.
3. No habilitar auto-merge. Un cambio de dependencia pasa CI, revision humana
   y pruebas funcionales cuando cambie comportamiento sensible.

## Fase 4: staging y recuperacion

1. Elegir y documentar hosts separados de staging y produccion.
   La guia de staging gratuito y su alternativa cloud esta en
   `05-STAGING-GRATUITO-ESXI.md`.
   La decision recomendada y las puertas ESXi/Oracle/Tunnel estan en
   `06-DECISION-HOSTING-STAGING.md`.
   El runbook de instalaciones Ubuntu esta en
   `07-PROVISIONAMIENTO-UBUNTU-STAGING.md`.
2. Elegir un registro OCI que no imponga costos no aprobados.
3. Refactorizar Compose para recibir imagenes por digest en release, manteniendo
   el flujo local de desarrollo intacto.
4. Crear release desde un tag de `main`, publicar artefactos, escanearlos y
   desplegar exclusivamente los digests resultantes en staging.
5. Implementar backup automatizado y restaurar una copia en una base
   desechable autorizada. Esta restauracion es obligatoria antes de producir.
6. Probar rollback de aplicacion compatible y documentar como se maneja una
   migracion que no permite volver atras.

## Fase 5: produccion protegida

1. Crear entorno `production` en GitHub con aprobadores requeridos.
2. Registrar runner de produccion aislado y restringirlo a tags confiables.
3. Configurar `deploy-production.yml` para consumir solo los digests ya
   verificados en staging.
4. Ejecutar health checks de Caddy, frontend y backend despues del deploy.
5. Registrar version, digests, aprobador, hora y resultado de rollback en la
   evidencia del pendiente.
6. Si falla cualquier gate, detener el proceso. No reintentar sobre produccion
   sin identificar la causa y decidir rollback o correccion.

## Fase 6: agentes

1. Medir capacidad local y aprobar el modelo antes de instalarlo.
2. Ejecutar piloto de PR-Agent de comentarios con GitHub App de minimo alcance.
3. Configurar Continue para uso local sin compartir secretos.
4. Configurar OpenHands solo en sandbox y con tareas reversibles.
5. Revisar bitacora de dos semanas; adoptar o retirar con evidencia.

## Reglas que no se pueden omitir

- No usar `pull_request_target` con codigo de PR.
- No exponer secretos a jobs de PR, agentes o forks.
- No usar el runner de produccion para CI, testing o agentes.
- No desplegar desde una rama mutable ni desde un checkout no identificado.
- No declarar recuperacion sin una restauracion probada.
- No usar modelos o servicios de pago sin aprobacion explicita.

## Cierre del modulo

El modulo 33 solo se considera operativo cuando los once pendientes tienen
evidencia verificable. La activacion de produccion se trata como un cambio
separado, aprobado por una persona, incluso si todos los archivos ya existen.
