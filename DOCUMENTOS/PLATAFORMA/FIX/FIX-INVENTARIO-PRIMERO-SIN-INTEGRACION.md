# FIX — Inventario primero (equipos sin integracion)

Fecha: 2026-05-22

## Objetivo

Aplicar el modelo operativo que pediste: primero registrar equipos en inventario, y despues asociarlos a una integracion solo cuando sea necesario.

## Implementacion realizada

### Backend

1. `Device.integration_id` ahora permite nulo:
- Archivo: `PY-MK/backend/app/db/models/device.py`
- Cambio: `nullable=False` -> `nullable=True`

2. Schemas de dispositivos actualizados para soportar inventario base:
- Archivo: `PY-MK/backend/app/modules/devices/schemas/device.py`
- Cambios:
  - `DeviceRead.integration_id` -> `int | None`
  - `DeviceCreate.integration_id` -> `int | None`
  - `DeviceUpdate.integration_id` agregado (`int | None`)

3. Servicio de dispositivos ajustado para escenarios sin integracion:
- Archivo: `PY-MK/backend/app/modules/devices/services/device_service.py`
- Cambios clave:
  - Queries con `outerjoin` para no excluir equipos sin consola.
  - Filtro por cliente funciona por integracion o por sede (`site_id`).
  - `create()` permite crear equipo sin `integration_id`.
  - `get_or_404()` y `retire()` validan acceso por integracion o por sede/cliente.
  - `update()` valida integracion solo si se envia una nueva.

4. Export XLSX de inventario:
- Archivo: `PY-MK/backend/app/modules/devices/routers/router.py`
- Cambio: columna "Consola" muestra `Sin integracion` cuando no hay enlace.

### Frontend

1. Tipado API de dispositivos compatible con integracion opcional:
- Archivo: `PY-MK/frontend/src/lib/api/devices.ts`
- Cambio: `integration_id` pasa a opcional/null.

2. Pantalla de Dispositivos preparada para inventario base:
- Archivo: `PY-MK/frontend/src/app/(admin)/dashboard/devices/page.tsx`
- Cambios:
  - Formulario de alta ya no exige consola.
  - Selector de consola incluye opcion: `Sin integracion (inventario base)`.
  - Se puede guardar equipo con `integration_id = null`.
  - Aviso UI explicando el flujo "inventario primero".
  - Cards muestran `Sin integracion` cuando aplique.

## Resultado funcional

- Ya puedes crear y gestionar equipos sin depender de integraciones.
- El inventario queda como paso inicial real.
- La asociacion con consola se vuelve opcional y posterior.

## Nota importante

Para persistir este cambio en bases existentes necesitas migracion SQL/Alembic:
- `devices.integration_id` debe quedar nullable en la tabla real.

Sin esa migracion, en una base vieja puede fallar al guardar equipos sin integracion.
