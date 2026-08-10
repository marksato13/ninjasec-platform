# Implementación — Módulo Hardening Técnico Automatizado

> Basado en: `PLANIFICACION/31-MODULO-HARDENING-TECNICO.md`
> Creado: 2026-08-10 · **P1 resuelto (issue #64)**

---

## ✅ P1 — Catálogo + motor de evaluación en vivo

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `HardeningRule` (catálogo global) | ✅ | `db/models/hardening.py` |
| 2 | Migración Alembic | ✅ | `20260809_10_hardening_rules.py`, encadenada tras `20260809_09` |
| 3 | Seed de 12 reglas (5 auto + 7 manual) | ✅ | `seed_hardening_catalog()` en `app/db/seed.py`, idempotente por código |
| 4 | Motor de evaluación en vivo, sin persistir resultado | ✅ | `HardeningEvaluationService.evaluate()` — cruza `Integration`/`CollectionSnapshot` (eventos ECS-lite de 30-P1) |
| 5 | `GET /hardening/rules`, `/evaluate`, `/summary` | ✅ | `modules/hardening/routers/router.py` |
| 6 | Export PDF del gap analysis | ✅ | `services/hardening_pdf.py`, reutiliza ReportLab (mismo patrón que `topology_pdf.py`) |
| 7 | Página `/dashboard/hardening` | ✅ | selector de cliente, resumen, tabla de reglas, export PDF |

### Las 5 reglas automáticas y de dónde sale su evidencia

| Código | Regla | Cómo se verifica |
|---|---|---|
| H-01 | Firewall perimetral integrado y activo | `Integration(connector_type in pfSense/FortiGate, status='connected')` |
| H-02 | SIEM/IDS integrado | `Integration(connector_type='wazuh', status='connected')` |
| H-03 | Recolección de eventos activa (30 días) | `CollectionSnapshot.collected_at` reciente |
| H-04 | Sin eventos críticos de fuerza bruta sin atender | Eventos ECS-lite `event.category='authentication'`, `severity='critical'` |
| H-05 | Sin eventos de malware alto/crítico sin atender | Eventos ECS-lite `event.category='malware'`, `severity in (high, critical)` |

Las 7 restantes (H-06 a H-12: política de contraseñas, MFA, revisión de privilegios, backups, DRP, concientización, acceso físico) son `manual` — no hay dato automático en la plataforma que las verifique, y se reportan como tal explícitamente, nunca como `pass` inventado.

### Evidencia verificada (2026-08-10)

- Suite completa: **188 tests pasan, 1 skip** (8 casos nuevos en `test_hardening.py`: catálogo de 12 reglas, reglas manuales nunca pass/fail, reglas auto sin integraciones fallan/no aplican honestamente, firewall conectado hace pasar H-01, evento crítico de autenticación hace fallar H-04, resumen calcula % solo sobre reglas evaluables, export PDF válido, aislamiento entre organizaciones).
- Migración verificada con `alembic upgrade head` sobre Postgres 16 limpio.
- Smoke test manual vía `curl`: catálogo de 12 reglas, evaluación de un cliente real (H-01 falla correctamente porque sus integraciones estaban en estado `pending`, no `connected` — el motor no "hace trampa"), resumen con 40% de cumplimiento, export PDF válido (`%PDF-`, 1 página).
- `npx tsc --noEmit` sin errores; build de producción real (`npm run build`) confirma la ruta `/dashboard/hardening` compila (2.82 kB).

**Nota importante sobre el catálogo**: las 12 reglas son una selección representativa inspirada en CIS Benchmarks, no un benchmark oficial tokenizado completo — mismo criterio de honestidad ya aplicado al catálogo ISO 27001 (módulo 24) y al parser de Config Visualizer (módulo 23): mejor un catálogo pequeño y verificable que uno grande y falso.
