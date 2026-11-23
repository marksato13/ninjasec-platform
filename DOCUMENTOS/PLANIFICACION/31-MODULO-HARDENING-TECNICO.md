# Planificación — Módulo Hardening Técnico Automatizado

> Creado: 2026-08-10 (issue #64, a partir de `DOCUMENTOS/HISTORICO/ideas-roadmap-networking-2026-08-09.md` sección 2.5)

---

## Objetivo

Verificación técnica **automática** de hardening, cruzando datos reales de integraciones y eventos (módulo 30) contra un catálogo de reglas estilo CIS Benchmarks. Complementa al módulo 24 (SGSI ISO 27001), que es la Declaración de Aplicabilidad que un consultor completa **a mano** — este módulo verifica lo que sí se puede verificar con datos técnicos reales, y es honesto sobre lo que no.

## Principio rector

**Una regla marcada `manual` nunca se reporta como `pass`/`fail` sin evidencia real.** Si no hay dato automático disponible para verificar una regla, el resultado es `manual` — nunca se inventa un resultado. Un control marcado `not_applicable` significa que el dato que lo verificaría todavía no existe para ese cliente (ej. cero integraciones), no que el control no aplique por decisión de negocio.

## P1 — Catálogo + motor de evaluación en vivo

- Catálogo global `HardeningRule`: código, título, categoría, severidad, descripción, método de verificación (`auto`/`manual`), clave de chequeo.
- Motor de evaluación **sin persistencia de resultado**: se calcula en cada consulta cruzando `Integration`/`CollectionSnapshot` del cliente — evita que un "cumple" quede obsoleto si la integración se cae.
- `GET /hardening/rules`, `GET /hardening/evaluate?client_id=`, `GET /hardening/summary?client_id=`.
- Export PDF del gap analysis (ReportLab).

## Fuera de alcance (fases futuras)

- Reglas auto-verificables adicionales a medida que el módulo 30 capture más tipos de datos estructurados (hoy solo eventos ECS-lite, no configuración detallada de dispositivos).
- Integración real con OpenSCAP para evaluación XCCDF completa contra un host.
- Tokenización de un CIS Benchmark oficial completo (hoy el catálogo es una selección representativa de 12 reglas, no un benchmark completo — evita el mismo riesgo de alcance que el parser de Config Visualizer).

## Dependencias

| Depende de | Estado |
|---|---|
| 30-P1 Esquema normalizado (ECS-lite) | ✅ |
| 04 Integraciones | ✅ |
