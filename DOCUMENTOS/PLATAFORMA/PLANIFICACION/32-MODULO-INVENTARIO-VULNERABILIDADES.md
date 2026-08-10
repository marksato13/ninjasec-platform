# Planificación — Módulo Inventario de Vulnerabilidades

> Creado: 2026-08-10 (issue #65, a partir de `tash/ideas-roadmap-networking-2026-08-09.md` sección 2.6)

---

## Objetivo

Cruza el inventario real de dispositivos del cliente (`Device.vendor`/`Device.model`) con CVEs conocidos, priorizando por **EPSS** (probabilidad real de explotación, FIRST.org) en vez de solo CVSS — evita la trampa de "todo es crítico" que tiene ordenar solo por severidad.

## P1 — Inventario CVE + EPSS por dispositivo

- Fuente primaria: **CIRCL CVE Search** (`cve.circl.lu`, sin API key) — a diferencia de NVD, no exige key para throughput razonable.
- **EPSS** (`api.first.org`, sin key) para el score de explotabilidad real.
- Caché por `vendor::modelo` (`CveInventoryCache`) con TTL de 7 días — varios clientes comparten el mismo equipo, no tiene sentido re-consultar por cada uno.
- Cualquier fallo de red degrada a lista vacía, nunca rompe el endpoint.
- `GET /vulnerability-inventory/devices?client_id=` — dispositivos con CVEs conocidos, ordenados por `top_epss_score` descendente.
- Página `/dashboard/vulnerabilities`.

## Fuera de alcance

- **OpenVAS/Greenbone** (escaneo activo real) — requiere infraestructura de escaneo que no es parte de esta fase.
- **32-P2 — Shodan** (exposición pasiva): consulta pasiva de la IP pública del cliente, sin escaneo activo. Queda pendiente como fase siguiente.

## Dependencias

| Depende de | Estado |
|---|---|
| 05 Dispositivos (`vendor`/`model`) | ✅ |
