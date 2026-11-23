# Implementación — Módulo Inventario de Vulnerabilidades

> Basado en: `PLANIFICACION/32-MODULO-INVENTARIO-VULNERABILIDADES.md`
> Creado: 2026-08-10 · **P1 resuelto (issue #65)**

---

## ✅ P1 — Inventario CVE + EPSS por dispositivo

| # | Requisito | Estado | Archivos |
|---|-----------|--------|----------|
| 1 | Modelo `CveInventoryCache` | ✅ | `db/models/vulnerability_inventory.py` — único por `product_key` (`vendor::modelo`) |
| 2 | Migración Alembic | ✅ | `20260809_11_cve_cache.py`, encadenada tras `20260809_10` |
| 3 | Cliente CIRCL (sin API key) | ✅ | `services/cve_client.py` → `search_cves_by_product()` — **llamada HTTP real**, no simulada (a diferencia de 30-P1/30-P2, CIRCL no exige key) |
| 4 | Cliente EPSS (sin API key) | ✅ | `enrich_with_epss()` — batch en una sola request por lote de CVEs |
| 5 | Caché con TTL de 7 días | ✅ | `VulnerabilityInventoryService._cves_for_product()` |
| 6 | Degradación ante fallo de red | ✅ | cualquier error de `httpx` devuelve lista vacía, nunca rompe el endpoint |
| 7 | `GET /vulnerability-inventory/devices?client_id=` ordenado por EPSS | ✅ | `modules/vulnerability_inventory/` |
| 8 | Página `/dashboard/vulnerabilities` | ✅ | selector de cliente, tabla de CVEs por dispositivo con badges de severidad y EPSS |

### Verificado con datos reales (2026-08-10)

A diferencia de 30-P1/30-P2 (simulados sin API key), este entorno **sí tiene acceso real a internet** — se verificó con una llamada real, no simulada:

```
GET /vulnerability-inventory/devices?client_id=<cliente con dispositivo cisco/ios>
```

Devolvió 5 CVEs reales de Cisco IOS/IOS XE publicados en 2025-2026 (ej. `CVE-2025-20352`, CVSS 7.7, EPSS 0.38754), **correctamente priorizados por EPSS**: `CVE-2025-20363` tiene CVSS más alto (9.0, crítico) pero EPSS más bajo (0.0752) que `CVE-2025-20352` (CVSS 7.7, EPSS 0.38754) — y el inventario lo pone primero por EPSS, demostrando exactamente el valor descrito en la planificación (priorizar por explotabilidad real, no solo severidad).

Primera consulta: 1.65s (llamada real a CIRCL + EPSS). Segunda consulta sobre el mismo producto: 25ms (caché). Verificado en `cve_inventory_cache` que solo existe una fila por `product_key`.

### Tests

Los tests siembran `CveInventoryCache` directamente en vez de depender de la red real — determinista y rápido independientemente de la conectividad del entorno de CI, aunque el código de producción sí hace la llamada real.

**Verificado**: 193 tests pasan (1 skip, 5 casos nuevos: sin CVEs en caché no aparece, ordena por EPSS no por CVSS, múltiples dispositivos se ordenan por top EPSS, caché se reutiliza sin duplicar, aislamiento entre organizaciones). Migración verificada con `alembic upgrade head` sobre Postgres limpio. `npx tsc --noEmit` sin errores; build de producción real confirma que `/dashboard/vulnerabilities` compila (1.86 kB).

### 32-P2 (pendiente): Shodan

Exposición pasiva de la IP pública del cliente — no implementado en esta fase.
