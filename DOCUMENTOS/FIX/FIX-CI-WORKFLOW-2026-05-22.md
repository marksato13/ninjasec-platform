# FIX — CI ejecutable en GitHub Actions

Fecha: 2026-05-22

## Objetivo

Cerrar pendiente de CI real para validar calidad minima en cada push/PR.

## Implementacion

Se creo workflow ejecutable:
- `PY-MK/.github/workflows/ci.yml`

Incluye 2 jobs:

1. `backend-tests`
- Python 3.12
- `pip install -r backend/requirements.txt`
- `pytest -q` en `backend/`

2. `frontend-quality`
- Node 20
- `npm ci` en `frontend/`
- `npm run lint`
- `npm run build`

Triggers:
- `push` a `main` y `develop`
- `pull_request` hacia `main` y `develop`

## Resultado

- Ya existe gate automatizado para backend y frontend.
- El repo deja de depender solo de verificacion manual local.
