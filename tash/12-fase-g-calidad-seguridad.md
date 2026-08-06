# NinjaSec - Fase G - Calidad y seguridad (sin despliegue)

## Objetivo

Endurecer configuracion base y ejecutar QA minimo sin tocar despliegue.

## Cambios aplicados

### 1. Configuracion segura por entorno

- se agrega `APP_ENV` y `SEED_ON_STARTUP`
- en produccion se exige `JWT_SECRET_KEY` no default
- en produccion se exige `CORS_ORIGINS` definido
- se evita seed automatico en produccion

Archivos:

- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env.example`

## QA ejecutado

- `frontend`: `npm run lint` (OK)

## Pendientes opcionales

- migrar `next lint` a ESLint CLI (recomendado por Next)
- agregar pruebas automatizadas si se requieren en esta fase
