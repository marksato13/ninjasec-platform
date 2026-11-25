# Módulos activables — qué se despliega y qué espera

> Decidido el **2026-11-23**. La web pública es el gancho para clientes y
> colaboradores, así que lo que se despliega tiene que funcionar de verdad.
> Lo que no, se queda en el código, apagado, y se enciende cuando toque.

## El problema

Ninja Tech tiene 38 módulos de API y 24 pantallas de panel. No todos están
igual de terminados, y uno de ellos **miente**:

`simulate_connector_test()` devuelve `"reachable": true` **sin contactar
ningún equipo**. Encima de ese dato inventado corren la evaluación de
*hardening*, la puntuación de riesgo y el índice de salud que alimenta el
informe SOC.

Mientras eso siga así, exponer esas pantallas en la web pública es un riesgo
comercial, no técnico: el primer cliente que pida conectar su firewall en una
demo lo descubre en un minuto.

## La decisión

**Ni borrarlo ni exponerlo: apagarlo.** El código se queda íntegro, con sus
vistas y sus pruebas. Un interruptor por cápsula decide si se registra o no.

Lo que **no** se hace y por qué:

| Alternativa | Por qué no |
| --- | --- |
| Borrar el módulo y rehacerlo después | Se pierde el trabajo y la historia. Son ~40 archivos |
| Dejarlo y avisar «es una demo» | El aviso no lo lee nadie, y el informe SOC parece real |
| Sacarlo a otro despliegue | Comparte la base de datos y los modelos. Partirlo es un proyecto, no una tarea |
| Ocultar solo el menú | Adivinar la URL llega igual. Ocultar no es apagar |

## Dónde está el límite

No es obvio, y fue lo primero que hubo que medir. **Doce módulos importan
`Integration` o `CollectionSnapshot`**, pero no por el mismo motivo:

### Dependen de telemetría real → entran en la cápsula

| Módulo | Qué hace | Por qué entra |
| --- | --- | --- |
| `integrations` | Los conectores | Es la pieza que miente |
| `collection` | Instantáneas de configuración | Sin conector no hay nada que recoger |
| `hardening` | Evalúa reglas contra configuraciones | Lee `CollectionSnapshot` |
| `risk_scoring` | Puntúa riesgo por cliente | Lee `CollectionSnapshot` |
| `health_score` | Índice de salud e **informe SOC** | Compone los tres de arriba |

### Solo usan `Integration` como *join* → se quedan

| Módulo | Cómo la usa |
| --- | --- |
| `dashboard` | `join(Integration, Device.integration_id == Integration.id)` para filtrar por organización |
| `reports` | El mismo *join*, para contar dispositivos del cliente |
| `vulnerability_inventory` | El mismo *join*, y cruza vendor/modelo contra el catálogo |
| `alerts` | Mira licencias vencidas, que son un dato introducido a mano |
| `security_reviews` | Enlaza una revisión a su integración, si la hay |

Estos siguen funcionando con la cápsula apagada: devuelven menos filas, no
se rompen. **Eso había que comprobarlo antes de decidir, no después.**

### Independientes

`netdoctor`, `risks`, `compliance`, `audits`, `architecture` y todo lo
comercial no tocan telemetría. Se despliegan.

## Cómo funciona el interruptor

Una cápsula es una entrada en un registro, no un `if` repartido por el
código:

```python
# app/core/features.py
CAPSULAS = {
    "telemetria": Capsula(
        nombre="telemetria",
        descripcion="Conectores, recolección y todo lo que se calcula sobre ella",
        modulos=("integrations", "collection", "hardening", "risk_scoring", "health_score"),
        rutas_api=("/integrations", "/collection", "/hardening", "/risk-scoring", "/health-score"),
        rutas_ui=("/dashboard/integrations", "/dashboard/hardening", "/dashboard/soc-report"),
        activa_por_defecto=False,
        motivo="Los conectores son simulados: simulate_connector_test() no contacta ningún equipo",
    ),
}
```

Se enciende con una variable de entorno:

```
CAPSULAS_ACTIVAS=telemetria
```

Y entonces vuelve **todo**: las rutas de API, las pantallas, las entradas del
menú y las pruebas. Nada más que hacer.

### Las tres capas que hay que apagar, no una

| Capa | Qué pasa apagada |
| --- | --- |
| **Registro de rutas** | El router no se incluye: la ruta no existe, 404 natural |
| **Pantallas** | La página devuelve `notFound()`. Adivinar la URL no sirve |
| **Menú** | Las entradas no se pintan |

Apagar solo el menú es el error clásico: la ruta sigue ahí y cualquiera que
teclee la URL entra. Por eso son tres y no una.

## El contrato de la API describe el código, no el despliegue

El job `Contrato OpenAPI` se puso rojo al introducir las cápsulas: apagar
`telemetria` quita 13 rutas del esquema, y `oasdiff` lo lee —con razón— como
un cambio incompatible.

La decisión fue que **el exportador enciende todas las cápsulas**. El contrato
dice qué ofrece el código; qué sirve una instancia concreta es configuración
de despliegue.

Si el esquema siguiera al interruptor, cada vez que se tocara una variable de
entorno el check gritaría «cambio rompedor». Un check que grita por todo deja
de cazar las roturas de verdad, que es para lo que existe.

**Consecuencia que hay que conocer:** una instancia con una cápsula apagada
sirve un **subconjunto** de su contrato publicado. Quien consuma la API desde
fuera tiene que preguntar a `GET /api/v1/capsulas` qué hay encendido, no
deducirlo del esquema.

## Qué NO protege esto

- **No es seguridad.** Es gestión de alcance. Un módulo apagado no está
  protegido de nada; está ausente. La autorización sigue siendo de
  `organization_id` y los roles.
- **No oculta el código.** El repositorio va a ser público: el código de la
  cápsula se lee igual. Lo que no se puede es usarlo en la instancia
  desplegada.
- **No arregla los conectores.** Los conectores siguen simulados. Esto solo
  evita que esa simulación se vea como un producto.

## Lo que hay que hacer para encenderla

La cápsula `telemetria` se enciende cuando los conectores sean reales. Eso
significa, como mínimo:

1. **`simulate_connector_test()` hace una petición HTTP de verdad**, con su
   tiempo límite, su manejo de error y su prueba contra un servidor falso.
2. **Un conector real por fabricante**, empezando por el que más se vende:
   pfSense o FortiGate.
3. **Credenciales por integración**, cifradas, que no aparezcan en logs.
4. **La recolección guarda lo que recibió**, no lo que esperaba recibir.

Hasta el punto 1 no tiene sentido encenderla, ni siquiera en un entorno de
pruebas: un conector que dice que todo responde es peor que no tener conector.

## Siguiente cápsula candidata: plan de estudio por colaborador

Pedido el **2026-11-23**, sin construir todavía.

La idea: cada colaborador —estudiantes de la UPeU— tiene un **plan de
estudio** con módulos, y su progreso se ve en su portal. Es lo que convierte
la plataforma en un gancho para captar colaboradores, no solo clientes.

Lo que ya existe y hay que reutilizar en vez de duplicar:

| Ya hay | Qué aporta |
| --- | --- |
| `skills` | Las habilidades y su nivel por usuario |
| `certifications` | Certificaciones con su estado |
| `collaborators` | El perfil, el área y la disponibilidad |
| `projects` + `project_members` | En qué ha trabajado de verdad |
| `recruitment` | Cómo entró |

Lo que falta, y es el módulo nuevo:

- Un **plan** (una ruta de aprendizaje) con módulos ordenados y requisitos.
- La **asignación** de un plan a un colaborador, con fechas.
- El **progreso** por módulo: pendiente, en curso, hecho, con evidencia.
- La **vista en el portal** del colaborador, y la vista de seguimiento para
  quien lo tutoriza.

Dos decisiones que hay que cerrar antes de programar:

1. **¿El plan se define por área o por persona?** Por área es reutilizable y
   escala; por persona es más flexible y no escala. Lo razonable es plan por
   área con desvíos por persona, pero eso es el diseño más caro.
2. **¿El progreso lo marca el colaborador o quien lo tutoriza?** Si lo marca
   el colaborador, hace falta evidencia y aprobación; si lo marca el tutor,
   hace falta que el tutor entre a marcarlo. Cambia el modelo de datos.

Y una advertencia desde ya: **`recruitment` no tiene `organization_id`**, así
que los datos de los candidatos son globales. Un plan de estudio colgado de
ahí heredaría la fuga. Eso se arregla antes, no después.

Hasta cerrar esas dos decisiones esto no se programa: es exactamente el caso
que la ficha de tarea llama *«decisiones pendientes que afectan al diseño»*.

## Cómo se decide si algo va en una cápsula

Tres preguntas. Si alguna sale «sí», va apagado:

1. **¿Devuelve datos que parecen reales y no lo son?** El caso de los
   conectores.
2. **¿Se puede llegar a una pantalla que no hace nada?** Media funcionalidad
   visible es peor que ninguna.
3. **¿Falta algo que solo tú puedes decidir?** Precio, alcance, un dato de
   negocio. Mejor apagado que inventado.

Ver también: [`09-STAGING-MULTIPROYECTO.md`](09-STAGING-MULTIPROYECTO.md) ·
[`08-DECISION-HOSTING.md`](08-DECISION-HOSTING.md) ·
[`../IMPLEMENTACION/04-MODULO-INTEGRACIONES.md`](../IMPLEMENTACION/04-MODULO-INTEGRACIONES.md)
