# FIX — Tests de regresion backend (core)

Fecha: 2026-05-22

## Objetivo

Agregar una suite minima de regresion para modulos criticos no-auth y evitar roturas silenciosas.

## Implementacion

Archivo nuevo:
- `PY-MK/backend/tests/test_regression_core_modules.py`

Cobertura agregada:

1. Leads
- Crear lead (endpoint publico)
- Listar leads autenticado como admin
- Mover estado con `PATCH /leads/{id}`

2. Support Tickets
- Crear ticket como admin
- Verificar regla: no se puede cerrar sin `resolution` (422)
- Verificar cierre correcto con `resolution` (200)

3. Users (guardas de permisos)
- Verificar que admin no puede editar a otro admin (403)
- Verificar que admin no puede cambiar `role_code` (403)

## Ajuste tecnico adicional

Para que tests y app funcionen desde distintos working directories, se ajusto el mount de estaticos a ruta absoluta basada en `main.py`:
- `PY-MK/backend/app/main.py`

Antes: `app/static` relativa
Ahora: `Path(__file__).resolve().parent / "static"`

## Verificacion ejecutada

Comando:
- `pytest -q tests/test_regression_core_modules.py` (desde `backend/`)

Resultado:
- `3 passed`
