# Política de enrutado — qué motor y qué modelo para cada tarea

> Esta es la pieza central de [[MOC-Cortex|CORTEX]]. Todo lo demás existe para
> que esta tabla se pueda aplicar sin pensarlo dos veces.

Hay tres motores instalados en esta máquina y entre todos dan acceso a
modelos que van de **gratis** a **$180 por millón de tokens de salida**.
Mandar todo al más caro es quemar cuota; mandar todo al más barato es cómo
se filtran datos de otro tenant. La decisión se toma por **radio de daño**,
no por precio.

## Los cuatro ejes

Antes de elegir motor, una tarea se mide en cuatro ejes. Dos preguntas
bastan para las dos primeras:

| Eje | Pregunta | Si la respuesta es «sí»… |
| --- | --- | --- |
| **Radio de daño** | ¿Puede filtrar datos de otro tenant, romper el login o perder datos? | Clase **T4**. No se delega. Punto. |
| **Contexto propio** | ¿Hace falta conocer `AGENTS.md`, las convenciones del repo o el estado de los PR? | Claude, que ya los tiene cargados |
| **Volumen** | ¿Son muchos archivos y poca decisión? | Modelo barato o gratis |
| **Verificabilidad** | ¿Hay una prueba que diga sí/no sin criterio humano? | Se puede delegar con red de seguridad |

El eje que manda es el primero. Si hay duda entre dos clases, **gana la más
cara**: equivocarse hacia arriba cuesta cuota, equivocarse hacia abajo cuesta
un incidente.

## La tabla

| Clase | Qué es | Ejemplo real de NinjaSec | Motor | Modelo |
| --- | --- | --- | --- | --- |
| **T0** | Barrido de solo lectura | «¿en qué 18 tablas está `organization_id`?» | Claude, subagente [[Agentes\|ns-explorador]] | **Haiku 5.5** |
| **T1** | Mecánica repetida con diff revisable entero | los 8 `VARCHAR(4000)` → `TEXT` | **OpenCode** | gratis de Console: `deepseek-v4.1-flash-free`, `glm-5.3-flash` |
| **T2** | Implementación acotada de backend con prueba | endpoint nuevo + su `pytest` | Claude, subagente [[Agentes\|ns-backend]] | **Opus 5** |
| **T3** | Pantalla o componente de frontend | vista nueva en `/dashboard` | Claude, subagente [[Agentes\|ns-frontend]] | **Sonnet 5.5** |
| **T4** | **Seguridad, tenancy, auth, migraciones, secretos** | las tres fugas multi-tenant, `is_production`, Alembic | **Claude principal, sin delegar** | **Opus 5** |
| **T5** | Segunda opinión adversarial sobre un diff | «¿este PR tiene un bug que no vi?» | **Codex CLI** | **GPT-5.3-Codex** |
| **T6** | Investigación externa con fuentes | «¿eramba es de verdad open source?» | Claude, subagente + WebSearch | **Sonnet 5.5** |
| **T7** | Redacción comercial y de negocio | catálogo de servicios, propuesta, precios | Claude principal | **Opus 5** |
| **T8** | Verificación mecánica de puertas | correr las 5 puertas y reportar | Claude, subagente [[Agentes\|ns-revisor-ci]] | **Sonnet 5.5** |

## Las fronteras, escritas al revés

Es más útil saber qué **no** puede pasar que qué puede:

**Nunca sale de Claude Opus con el repo cargado**

- Cualquier archivo bajo `backend/app/core/` (config, seguridad, dependencias).
- Cualquier ruta que lea o escriba datos filtrando por `organization_id`.
- Cualquier migración de Alembic.
- Cualquier cosa que toque `.env`, secretos, seed de contraseñas o JWT.
- La decisión de abrir el sistema al público.

Motivo: estos son exactamente los sitios donde ya hubo un fallo real
—`IS_PRODUCTION` ignorado, tres fugas de tenant, `services.slug` único
globalmente— y donde el fallo no se ve en el diff si no conoces la regla.

**Nunca se delega a un motor sin las reglas cargadas**

Codex y OpenCode **no leen `AGENTS.md`**. No saben que los datos de otro
tenant devuelven 404 y no 403, que no se usa `alert()`, que `from __future__
import annotations` no se quita. Se les da trabajo **autocontenido**: un
archivo, un patrón, un diff que se revisa entero.

**Nunca se acepta un resultado sin verificarlo**

Lo que devuelve un motor delegado es una **propuesta**, no una entrega. Pasa
por [[Puertas-de-CI]] igual que si lo hubiera escrito yo. Un diff de OpenCode
que no compila es ruido, no velocidad.

## Por qué Codex, si ya hay Claude

No por capacidad: por **sesgo**. Dos modelos de la misma familia tienden a
cometer y a pasar por alto los mismos errores. Un revisor de otra familia es
la forma barata de romper esa correlación.

El sitio donde más rinde es **T5**: se le da el diff de un PR y la pregunta
«¿qué falla aquí?», sin contarle qué se intentó hacer. Si coincide con lo que
ya pensaba, sube la confianza; si saca algo nuevo, ya pagó el viaje.

## Y el presupuesto

El cuello de botella no es el precio por token: es la **cuota semanal** de
cada suscripción. Criterio operativo:

1. Mirar el consumo antes de lanzar trabajo largo (`CORTEX/herramientas/estado.ps1`).
2. El motor con la ventana semanal más holgada se lleva el trabajo largo.
3. El otro se reserva para tareas acotadas hasta que su ventana reinicie.
4. **T4 nunca entra en este cálculo.** Si no hay cuota de Opus, se espera.

Detalle en [[Presupuesto]]. Catálogo con precios en [[Catalogo-de-modelos]].
Qué está instalado de verdad en [[Motores]].
