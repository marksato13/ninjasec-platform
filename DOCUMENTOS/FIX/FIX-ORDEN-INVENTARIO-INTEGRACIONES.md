# FIX — Orden correcto: Inventario antes de Integraciones

Fecha: 2026-05-22

## Problema reportado

En la pantalla de Integraciones, el flujo daba a entender que se integra primero y luego se piensa en equipos/inventario.
Para tu operación actual, el orden correcto es:

1. Cliente
2. Equipos / Inventario
3. Integración (solo si aplica)

Además, por ahora solo se deben crear integraciones de firewall/open-source soportadas (`pfSense`, `FortiGate`).

## Cambios implementados

### 1) Mensaje de flujo operativo en la pantalla de Integraciones

Se agregó un aviso visible en la página de Integraciones indicando el orden recomendado:

- `Clientes -> Dispositivos (Inventario) -> Integraciones`
- Soporte actual limitado a firewalls `pfSense` y `FortiGate`.

Archivo:
- `PY-MK/frontend/src/app/(admin)/dashboard/integrations/page.tsx`

### 2) Formulario de nueva integración corregido y endurecido

Se mejoró el formulario de creación con estos cambios:

- Ya no usa URL hardcodeada incorrecta ni token manual.
- Usa cliente API central (`createIntegration`) para consistencia.
- Agrega selector de cliente (ya no `client_id = 1` fijo).
- Requiere confirmación explícita: inventario revisado/cargado primero.
- Botón de crear deshabilitado hasta confirmar ese prerequisito.
- Mensaje de ayuda con acceso directo a `/dashboard/devices`.

Archivo:
- `PY-MK/frontend/src/components/private/integration-form.tsx`

### 3) API frontend de integraciones extendida

Se agregó función dedicada para alta de integraciones:

- `createIntegration(payload)`

Archivo:
- `PY-MK/frontend/src/lib/api/integrations.ts`

### 4) Página de Integraciones conecta el nuevo formulario

Se pasa la lista de clientes al formulario para crear integración correctamente por cliente.

Archivo:
- `PY-MK/frontend/src/app/(admin)/dashboard/integrations/page.tsx`

## Resultado

Queda aplicado el flujo operativo que pediste a nivel de UX y proceso:

- Primero inventario/equipos.
- Integración después y solo cuando sea necesaria.
- Integración limitada por formulario a conectores soportados (`pfSense`, `FortiGate`).

## Nota técnica

Hoy el modelo de datos de dispositivos aún depende de `integration_id` en backend. Este fix corrige el flujo de uso y evita errores de alta, pero para un modelo 100% "inventario primero" sin dependencia de integración, el siguiente paso sería ajustar el modelo de `devices` para permitir equipos base sin `integration_id`.
