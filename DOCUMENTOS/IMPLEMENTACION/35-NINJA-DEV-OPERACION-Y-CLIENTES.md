# Implementación - Ninja Dev: operación y gestión de clientes

> Basado en: `PLANIFICACION/35-NINJA-DEV-OPERACION-Y-CLIENTES.md`
> Creado: 2026-11-25. 35-P-01 tiene el backend en revisión (PR #53).

## Checklist

| ID | Requisito | Estado | Evidencia esperada |
|---|---|---|---|
| `35-P-01` | Sistemas del cliente y entornos | 🟡 Backend en PR #53 | ✅ Migración `20261201_01` probada en PostgreSQL 16 (subir, bajar, subir, `alembic check` limpio); ✅ 9 pruebas de permisos por rol, 404 ajeno, 422 secretos y auditoría, más 3 mutaciones detectadas; ⏳ pestaña en cliente y "Mis sistemas" en portal (contrato en `lib/api/systems.ts`) |
| `35-P-02` | Registro de despliegues | Pendiente | Regla de checklist en `prod` probada; avance en la bitácora al desplegar |
| `35-P-03` | Solicitudes de cambio en Tickets | Pendiente | `kind` y `system_id` en tickets; decisión del cliente auditada; conversión a tareas |
| `35-P-04` | Estimador de costos | Pendiente | Tarifas solo admin (prueba de 403/404); versión aprobada inmutable; propuesta de hitos C3 |
| `35-P-05` | Pruebas de aceptación (UAT) | Pendiente | Casos marcados por el cliente; observar exige nota |
| `35-P-06` | Documentos desde plantilla | Pendiente | Generación en borrador interno; publicar es acción del admin |
| `35-P-07` | Mantenimiento y SLA | 🔒 Bloqueado | Decisión comercial de Mark (horas por plan, tiempos de respuesta, exceso) |
| `35-P-08` | Panel Ninja Dev | Pendiente | Solo datos reales de 35-P-01..03; vencimientos a 30 días |

## Reglas de implementación

- Un PR por fila. El backend se fusiona antes que su pantalla.
- Las pantallas reutilizan el cliente API, las query keys y las alertas
  existentes; nunca `alert()` ni `window.confirm`.
- Nada de precios, tarifas ni datos de clientes reales en el repo: es público.
