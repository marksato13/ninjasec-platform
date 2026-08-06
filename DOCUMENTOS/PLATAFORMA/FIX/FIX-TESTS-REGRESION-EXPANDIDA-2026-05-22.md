# FIX — Regresion expandida (reports + services)

Fecha: 2026-05-22

## Objetivo

Ampliar cobertura minima de regresion en backend para modulos criticos adicionales.

## Implementacion

Archivo nuevo:
- `PY-MK/backend/tests/test_regression_reports_services.py`

Casos cubiertos:

1. Reports
- `GET /api/v1/reports/last-exports` accesible para collaborator.
- Verifica que el payload incluya llaves esperadas:
  - `consolidated`, `devices`, `tickets`, `reviews`, `review-pdf`, `pipeline`

2. Services
- Collaborator NO puede crear servicios (`POST /services` -> 403).
- Admin SI puede crear servicio (`POST /services` -> 201).
- Admin NO puede eliminar servicio (`DELETE /services/{id}` -> 403).
- Se verifica que el servicio siga existente tras intento de delete prohibido.

## Validacion ejecutada

Comando:
- `pytest -q tests/test_regression_core_modules.py tests/test_regression_reports_services.py`

Resultado:
- `6 passed`

## Ajuste de CI

Archivo actualizado:
- `PY-MK/.github/workflows/ci.yml`

Cambio:
- backend job ahora ejecuta explicitamente `pytest -q tests`.
