# Catálogo de modelos — precios y para qué sirve cada uno

Precios por **millón de tokens**, entrada / salida. Tomados del catálogo de
modelos de OpenCode Console el **2026-11-22**. Son indicativos: cambian, y
los descuentos tienen fecha de caducidad. La fuente manda sobre esta tabla.

> Esta página existe para **decidir**, no para ser exhaustiva. El catálogo
> completo pasa de cien modelos; aquí están los que tienen sentido en
> NinjaSec y la razón por la que el resto no.

## Gratis — para T1 (mecánica)

| Modelo | Selector | Nota |
| --- | --- | --- |
| DeepSeek V4.1 Flash Free | `opencode/deepseek-v4.1-flash-free` | Retención cero documentada |
| GLM 5.3 Flash | `opencode/glm-5.3-flash` | $0.15 / $0.50 — barato, no gratis, pero retención cero |
| MiMo-V2.6-Flash Free | — | **Puede entrenar con lo enviado** |
| Flint 40B Free, Beam Free, Big Pickle, Iceman Free, Tidepool Alpha Free | — | Rotan; comprobar antes de usar |
| Nemotron 3.5 Lightning / Super VL Free | — | |

**Gratis no significa sin coste.** El coste es la revisión: un diff de un
modelo gratis se lee entero antes de commitear. Si la tarea es tan grande
que no se puede revisar entera, no es T1.

## Baratos — alternativa a los gratis cuando importa la retención

| Modelo | Precio | Cuándo |
| --- | --- | --- |
| Claude Haiku 5.5 | $0.10 / $0.50 (≤100K) | Barridos T0 dentro de Claude |
| Qwen3.8 Flash | $0.15 / $0.47 | Alternativa a GLM Flash |
| DeepSeek V4.1 Flash (de pago) | $0.12 / $0.48 | La versión sin el asterisco del gratis |
| GPT 6 Luna | $0.10 / $0.50 (≤272K) | Ya es el `small_model` de OpenCode aquí |

## De trabajo — T2, T3, T6, T8

| Modelo | Precio | Papel en NinjaSec |
| --- | --- | --- |
| **Claude Sonnet 5.5** | $2 / $10 | Frontend, investigación, verificación |
| **Claude Opus 5.5** | $4 / $20 | — |
| **Claude Opus 5** | $5 / $25 | **El motor de este repo.** T2, T4, T7 |
| GPT 6.2 Sol / GPT 6.1 Sol | $2 / $10 (≤272K) | Modelo por defecto de OpenCode en esta máquina |
| GPT 5.4 | $2.50 / $15 | El que usan los agentes de OpenCode ya configurados |

## Revisión adversarial — T5

| Modelo | Precio | Nota |
| --- | --- | --- |
| **GPT-5.3-Codex** | $1.75 / $14 | Ventana de 400K. El de la suscripción Plus |
| GPT 5.3 Codex Spark | $1.75 / $14 | Variante rápida |

## Los que no se usan, y por qué

| Modelo | Precio | Por qué no |
| --- | --- | --- |
| GPT 5.4 Pro / GPT 5.5 Pro | $30 / $180 | Doce veces Opus 5 en salida. Ninguna tarea de este repo lo justifica |
| Claude Fable 5.2 | $8 / $40 | Perfil distinto; no aporta sobre Opus aquí |
| GPT 6 Astra | $10 / $50 | Caro sin ventaja demostrada en este trabajo |
| Modelos de imagen y de *embeddings* | varios | No hay caso de uso todavía. Si llega la búsqueda semántica sobre `DOCUMENTOS/`, los candidatos son `voyage-code-4` ($0.12) y `qwen3-embedding-8b` ($0.01) |

## Depreciados — no enrutar hacia aquí

Marcados como depreciados en el catálogo a esta fecha, entre otros:
GLM 5.2 y 5.1, Gemini 3 Pro y 3.1 Pro, DeepSeek V4 Flash, GPT 5.2 Codex,
GPT 5.1 Codex y sus variantes Max y Mini, GPT 5 Codex, Claude Opus 4.1,
Claude Sonnet 4, Claude Haiku 3.5, Kimi K2 y K2.5, Qwen3 Coder 480B,
MiniMax M2.1 y M2.5, LongCat-2.0.

Si una configuración antigua apunta a uno de estos, hay que actualizarla
antes de usarla.

## Cómo se comprueba que esto sigue siendo cierto

La lista de gratuitos es la que más rota: la documentación de OpenCode dice
que son gratis *por tiempo limitado*. El resto cambia por trimestres. Si
pasó más de un mes desde la fecha de arriba, esta página es una pista, no
un hecho, y hay que volver a `https://opencode.ai/docs/zen`.

Volver a [[Politica-de-enrutado]] · [[Motores]] · [[Presupuesto]]
