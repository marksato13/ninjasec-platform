# 36 - Módulo de órdenes de trabajo · implementación

Requisitos: [`PLANIFICACION/36`](../PLANIFICACION/36-MODULO-ORDENES-DE-TRABAJO.md).

## Rebanada 1 · De la solicitud a la orden cerrada

| Pendiente | Qué | Issue | Carril | Estado |
| --- | --- | --- | --- | --- |
| 36-P-00 | Validar el diseño | #119 | Mark | ✅ Cerrado el 2026-11-26 |
| 36-P-01 | Modelos, migración `20261203_01`, `states.py` | #120 | Claude | En PR |
| 36-P-02 | API con aislamiento por rol, organización y técnico; auditoría; menú | #121 | Claude | Espera a #120 y #88 |
| 36-P-03 | Pruebas de la tabla de transiciones, con mutación | #122 | Obrero | Espera a #120 |
| 36-P-04 | Panel del admin: órdenes | #123 | OpenCode | Espera a #121 |
| 36-P-05 | Solicitudes y editor de cotizaciones | #124 | OpenCode | Espera a #123 |
| 36-P-06 | «Mis órdenes» del técnico y portal del cliente | #125 | OpenCode | Espera a #124 |

## Siguientes

| Pendiente | Qué |
| --- | --- |
| 36-P-07 | Rebanada 2: `clients.tax_id` y migración del Excel con informe de duplicados, rechazos y conciliación |
| 36-P-08 | Rebanada 3: tope de monto con revisión de gerencia (R-08) y avisos (cotizaciones que vencen, órdenes sin asignar) |

## Evidencia de 36-P-01

| Puerta | Estado |
| --- | --- |
| `PYTHONPATH=. pytest -q` | ✅ 653 pasan, 1 omitida; ❌ 3 de `test_rate_limit_redis.py` fallan porque no hay Redis en el portátil (las excluyen el obrero y la verificación local) |
| `test_alembic_bootstrap.py` contra PostgreSQL 16 efímero | ✅ 2 pasan |
| `alembic downgrade -1` y `upgrade head` | ✅ 5 tablas → 0 → 5 |
| `alembic check` | ✅ «No new upgrade operations detected»: modelo y migración cuadran |
| Mutación de #122 (`return actor in allowed` → `return True`) | ✅ la línea existe una vez y el reemplazo cambia el archivo |
