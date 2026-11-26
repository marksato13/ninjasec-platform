# Implementación - Ninja Dev: operación y gestión de clientes

> Basado en: `PLANIFICACION/35-NINJA-DEV-OPERACION-Y-CLIENTES.md`
> Creado: 2026-11-25. 35-P-01 tiene el backend en revisión (PR #53).

## Checklist

| ID | Requisito | Estado | Evidencia esperada |
|---|---|---|---|
| `35-P-01` | Sistemas del cliente y entornos | 🟡 Backend en PR #53 | ✅ Migración `20261201_01` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 9 pruebas de permisos por rol, 404 ajeno, 422 secretos y auditoría, más 3 mutaciones detectadas; ⏳ pestaña en cliente y "Mis sistemas" en portal (contrato en `lib/api/systems.ts`) |
| `35-P-02` | Registro de despliegues | 🟡 Backend en PR #58 | ✅ Migración `20261201_02` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 7 pruebas: regla de checklist en `prod` (422), avance «Versión X publicada» en la bitácora una sola vez, cliente solo ve `prod` que llegó y sin checklist, roles, 404 ajeno y auditoría; ✅ 4 mutaciones detectadas; ⏳ pantalla (contrato en `lib/api/deployments.ts`) |
| `35-P-03` | Solicitudes de cambio en Tickets | 🟡 Backend en PR #57 | ✅ Migración `20261201_03` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 5 pruebas: flujo abrir → estimar → aprobar/rechazar → convertir en tarea, roles, 404 ajeno y otra organización, garantía, auditoría; 3 mutaciones detectadas; ⏳ pantalla: "Pedir un cambio" en Mis sistemas y bloque de estimación en el ticket (contrato en `lib/api/tickets.ts`) |
| `35-P-04` | Estimador de costos | Pendiente | Tarifas solo admin (prueba de 403/404); versión aprobada inmutable; propuesta de hitos C3 |
| `35-P-05` | Pruebas de aceptación (UAT) | 🟡 Backend en PR #61 | ✅ `tests/test_pruebas_de_aceptacion.py`: 7 pruebas, 4 mutaciones detectadas; suite `605 passed`; migración `20261202_01` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio). Pantalla pendiente (contrato en `lib/api/uat.ts`) |
| `35-P-06` | Documentos desde plantilla | Pendiente | Generación en borrador interno; publicar es acción del admin |
| `35-P-07` | Mantenimiento y SLA | 🔒 Bloqueado | Decisión comercial de Mark (horas por plan, tiempos de respuesta, exceso) |
| `35-P-08` | Panel Ninja Dev | Pendiente | Solo datos reales de 35-P-01..03; vencimientos a 30 días |

## Reglas de implementación

- Un PR por fila. El backend se fusiona antes que su pantalla.
- Las pantallas reutilizan el cliente API, las query keys y las alertas
  existentes; nunca `alert()` ni `window.confirm`.
- Nada de precios, tarifas ni datos de clientes reales en el repo: es público.
