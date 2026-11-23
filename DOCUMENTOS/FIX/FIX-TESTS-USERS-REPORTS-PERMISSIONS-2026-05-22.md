# FIX — Tests de permisos (users + reports exports)

Fecha: 2026-05-22

## Objetivo

Agregar regresion sobre permisos sensibles:
- gestion de usuarios por rol
- exports consolidados de reportes por rol

## Implementacion

Archivo nuevo:
- `PY-MK/backend/tests/test_regression_users_reports_permissions.py`

Casos cubiertos:

1. Users permissions
- collaborator no puede listar usuarios (`GET /users` -> 403)
- collaborator no puede crear usuarios (`POST /users` -> 403)

2. Reports consolidated exports permissions
- admin puede exportar PDF consolidado (`GET /reports/consolidated-pdf` -> 200)
- admin puede exportar XLSX consolidado (`GET /reports/consolidated-xlsx` -> 200)
- collaborator no puede exportar consolidado (PDF/XLSX -> 403)

3. Reports unknown client
- cliente inexistente en consolidado devuelve 404

## Verificacion ejecutada

Comando:
- `pytest -q tests/test_regression_core_modules.py tests/test_regression_reports_services.py tests/test_regression_users_reports_permissions.py`

Resultado:
- `9 passed`
