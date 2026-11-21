# Instrucciones para agentes

Este archivo gobierna todo el repositorio. Para cualquier cambio dentro de
`PY-MK/`, leer además [`PY-MK/CLAUDE.md`](PY-MK/CLAUDE.md) completamente.

## Fuentes de verdad

1. `DOCUMENTOS/PLATAFORMA/PLANIFICACION/NN-*.md`: requisitos del módulo.
2. `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/NN-*.md`: checklist y evidencia.
3. `DOCUMENTOS/PLATAFORMA/ROADMAP.md`: orden de trabajo.
4. `DOCUMENTOS/PLATAFORMA/IMPLEMENTACION/00-BACKLOG-GLOBAL.md`: inventario.

`tash/` es material histórico y nunca prevalece sobre esas fuentes.

## Flujo obligatorio

1. Trabajar en una rama y worktree propios; nunca directamente en `main`.
2. Antes de editar, identificar el pendiente `NN-P-NN` y sus criterios.
3. Un agente modifica únicamente los archivos asignados a su subtarea.
4. Backend, tests y documentación se separan cuando puedan ejecutarse en
   paralelo sin tocar los mismos archivos.
5. Ejecutar las pruebas proporcionales al cambio y registrar el resultado.
6. Actualizar el checklist de implementación con evidencia verificable.
7. Abrir un Pull Request; el merge requiere autorización humana explícita.

## Reporte de verificación: tres estados, nunca dos

Toda puerta de calidad se reporta como **pasó**, **falló** o **no se ejecutó
(y por qué)**. Nunca se declara en verde algo que no se corrió.

| Estado | Cuándo | Cómo se escribe |
|---|---|---|
| ✅ Pasó | Se ejecutó y terminó bien | Con la salida real pegada, no resumida |
| ❌ Falló | Se ejecutó y terminó mal | Con el error textual |
| ⏭️ No se ejecutó | Faltaba una dependencia, Docker estaba apagado, no aplicaba | **Con el motivo.** Nunca se omite la fila |

"Los tests pasan" sin la salida no es evidencia: es una afirmación. Y una
puerta omitida en silencio se lee como aprobada, que es la forma más común
de que un fallo llegue a `main`.

## Ramas

| Rama | De dónde sale | A dónde vuelve | Para qué |
|---|---|---|---|
| `main` | — | — | Lo desplegado. **Nunca recibe push directo** |
| `develop` | `main` | `main` vía PR | Integración del trabajo en curso |
| `feature/<slug>` | `develop` | `develop` vía PR | Funcionalidad nueva |
| `fix/<slug>` | `develop` | `develop` vía PR | Corrección no urgente |
| `chore/<slug>` · `docs/<slug>` | `develop` | `develop` vía PR | Mantenimiento y documentación |
| `hotfix/<slug>` | **`main`** | `main` **y** `develop` | Solo para fallos críticos en producción |

Una incidencia = una rama = un PR. Antes de crear una rama, comprobar que no
existe ya un PR abierto para lo mismo (`gh pr list --search`).

No hay ramas `release/*` a propósito: existen para congelar una versión
mientras varias personas siguen desarrollando. Con un solo desarrollador
añaden ceremonia sin aportar nada.

**Borrado de ramas:** usar `git cherry` para comprobar que el contenido ya
está integrado. `git diff` da falsos negativos cuando el merge fue squash,
que es el modo que usamos.

**Formato de commit:** `tipo(ámbito): descripción en español`. El ámbito es
el módulo (`auth`, `leads`, `catalogs`…) o el área (`config`, `ci`, `deps`).
Si cierra un issue, se añade al final: `feat(auth): login con Google (#83)`.

## Comandos de verificación

Backend:

```bash
cd PY-MK/backend
PYTHONPATH=. pytest -q
```

Frontend:

```bash
cd PY-MK/frontend
npm ci
NEXT_PUBLIC_API_URL=/api/v1 npm run build
```

Secretos:

```bash
gitleaks protect --staged --no-banner --redact
```

## Reglas de seguridad

- Nunca leer, mostrar, registrar ni versionar `.env`, tokens, cookies o claves.
- No usar credenciales seed fuera de entornos locales desechables.
- Toda ruta protegida valida rol y `organization_id`; datos de otro tenant
  devuelven 404 para no confirmar su existencia.
- Toda mutación crítica registra auditoría mediante `AuditService`.
- No ejecutar `DELETE`, `DROP`, `docker compose down -v` ni migraciones sobre
  una base con datos sin autorización y respaldo comprobado.
- No iniciar `28-P3` ni `30-P6` sin cumplir sus puertas de seguridad.
- No activar despliegues, modelos de pago ni servicios públicos por inferencia.

## Convenciones

- Documentación, UI, comentarios y commits: español.
- Identificadores de código: inglés.
- No quitar los dos rewrites de `frontend/next.config.ts`.
- No quitar `from __future__ import annotations` de servicios con `def list`.
- Frontend usa el cliente API, query keys y alertas existentes; nunca `alert()`
  ni `window.confirm`.
- Un pendiente resuelto se tacha con evidencia; nunca se borra del historial.

## Estado conocido

Actualizado el **2026-11-21**. Las cuatro líneas anteriores estaban obsoletas
y se corrigen aquí:

- **219 pruebas backend pasan** (eran 63 en agosto).
- El frontend compila **52 rutas** con Next.js 16.4.6. El build ya **no**
  ejecuta lint: `next lint` desapareció en Next 16 y el script pasó a
  `eslint .`, que hay que invocar aparte.
- **Alembic G-01/G-02 está resuelto** (issue #2, 2026-08-07): existe la
  migración base `20260807_00`, `create_all()` salió de `main.py` y
  `app/db/migrate.py` corre `alembic upgrade head` al arrancar. Ya no
  bloquea el despliegue.
- Deuda de lint abierta: **13 `useEffect` con `setState` síncrono**
  (`02-P-06`), marcados por `react-hooks/set-state-in-effect`. Las reglas
  están en `warn`, **no desactivadas**.
- La siguiente funcionalidad del roadmap sigue siendo `23-P1`, UI de
  topología. `@xyflow/react` ya está instalado.

## Puertas del CI

Qué corre GitHub y qué bloquea. Los workflows reales viven **solo** en
`.github/workflows/` en la raíz del repositorio.

| Job | Comando local equivalente | ¿Bloquea? |
|---|---|---|
| Backend · pytest | `cd PY-MK/backend && PYTHONPATH=. pytest -q` | ✅ Sí |
| Frontend · build | `cd PY-MK/frontend && npm ci && npm run build` | ✅ Sí |
| Frontend · audit | `npm audit --audit-level=critical` | ✅ Sí, solo en críticas |
| Security · Gitleaks | `gitleaks protect --staged --no-banner --redact` | ✅ Sí |
| Security · Semgrep | reglas propias en `.semgrep/ninjasec.yml` | ✅ Sí |
| Security · Trivy fs | escaneo de dependencias, HIGH y CRITICAL | ✅ Sí |
| Lint | `cd PY-MK/frontend && npm run lint` | ❌ **No corre en CI todavía** |

⚠️ Trivy y el audit de npm escanean **todo el árbol**, no solo lo que
cambiaste: una vulnerabilidad nueva publicada en una dependencia pone en
rojo cualquier rama, aunque tu cambio sea de una línea de documentación.
