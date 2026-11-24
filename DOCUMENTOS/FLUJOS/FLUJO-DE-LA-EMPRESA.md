# El flujo de la empresa en la plataforma

> Verificado con pruebas: `backend/tests/test_flujo_empresa.py` y `test_formacion.py`.
> Si este documento y esas pruebas discrepan, mandan las pruebas.

## El recorrido

```
 VISITANTE            ADMIN                          COLABORADOR            CLIENTE
 ─────────            ─────                          ───────────            ───────
 formulario  ──►  Lead (NEW)
 "Agenda una          │ contacta, califica, propone
  reunión"            ▼
                  Lead CLOSED_WON ──► Cliente
                                          │
                                          ▼
                                      Proyecto ──► equipo y tareas ──► ve SU proyecto
                                          │                              y SU tarea
                                          │                              │ cambia el estado
                                          │                              ▼
                                          │◄─────────────────────── tarea «hecha»
                                          ▼
                                    Proyecto completado ──────────────────────► lo ve en su portal
```

## Quién puede hacer qué

| Paso | Visitante | Cliente | Colaborador | Admin | Super admin |
|---|:-:|:-:|:-:|:-:|:-:|
| Dejar un interés (formulario público) | ✅ | | | | |
| Ver y avanzar leads | | | | ✅ | ✅ |
| Crear un cliente | | | | ✅ | ✅ |
| Crear un proyecto | | | | ✅ | ✅ |
| Asignar equipo y crear tareas | | | | ✅ | ✅ |
| Ver proyectos | | **los suyos** | **donde es miembro** | todos | todos |
| Cambiar el **estado** de una tarea | | | **las suyas** | cualquiera | cualquiera |
| Editar título o responsable de una tarea | | | | ✅ | ✅ |
| Ver menús por rol / editarlos | | | | | ✅ |

**Lo que nunca ocurre** (y las pruebas lo vigilan): un cliente ve el proyecto de otro
cliente, un colaborador ve proyectos donde no es miembro, un colaborador mueve la tarea
de otra persona, o un cliente ve los leads.

Los datos de otra organización o de otra persona devuelven **404**, no 403: no se
confirma que existan.

## Lo que se corrigió al escribir la prueba

La prueba del recorrido encontró un hueco real: **el colaborador veía su tarea pero no
podía marcarla como hecha**, porque la actualización de tareas era solo de admin. Ahora
tiene `PATCH /project-tasks/{id}/status`, que cambia **solo el estado** y **solo de sus
tareas**. Título, descripción y responsable siguen siendo del admin.

## Seguimiento del proyecto: el cliente ve su recorrido

El cliente no tiene que preguntar «¿cómo va lo mío?»: lo ve.

```
 EL CLIENTE VE                                  EL ESPECIALISTA ALIMENTA
 ──────────────                                 ────────────────────────
 La senda: 5 fases, y Kuro en la actual    ◄──  Cambia la fase (y escribe qué sigue)
 En marcha: quién hace qué ahora           ◄──  Marca sus tareas: pendiente / en curso / hecha
 Tu equipo: nombre y rol, sin correos      ◄──  Se asigna al proyecto
 Equipos: cuáles, su estado, sin IP        ◄──  Enlaza los equipos de la sede del cliente
 Bitácora: lo que ha pasado                ◄──  Publica avances e hitos (con enlace a la demo)
                                                Notas internas: SOLO el equipo las ve
```

- **Una sola vista** para los dos: la del especialista es la del cliente más un **centro de mando**, y trae un interruptor «**Ver como lo ve el cliente**» para comprobar lo que se publica antes de que lo lea nadie.
- **Las fases se leen con las palabras de cada línea.** Mismas claves en la base, distinto rótulo:

  | | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|
  | **Infraestructura** | Diagnóstico | Planificación | Implementación | Transferencia | Acompañamiento |
  | **Desarrollo** | Descubrimiento | Diseño | Desarrollo | Entrega | Soporte |

- **Lado de desarrollo:** un avance puede llevar un **enlace a la demo o al entorno de pruebas**, que el cliente abre desde la bitácora.
- **Se actualiza sola** cada 15 segundos y muestra «última actividad hace X».
- La bitácora se llena también sola: cada **cambio de fase** y cada **tarea que pasa a hecha** quedan anotados (una sola vez, aunque se marque dos veces).

**Lo que nunca llega al cliente** (las pruebas lo vigilan): notas internas, correos del equipo, la IP de los equipos, proyectos de otro cliente. Lo ajeno devuelve 404, no 403.

Pantallas: cliente en **Proyectos → Ver seguimiento** (`/portal/projects/{id}`); equipo en **Proyectos → Centro de mando** (`/dashboard/projects/{id}/centro`).

## Formación

```
 Plan de estudio ──► Inscripción ──► módulo a módulo ──► Completado ──► Validado
 (NSE 4, CCNA)       (uno mismo)     pendiente / en curso    (quien estudia)   (un admin)
```

- El **porcentaje se pondera por horas**: un módulo de 20 h pesa más que uno de 2 h.
- «Completado» ya cuenta como avance. «Validado» lo pone un **admin**, nunca uno mismo
  (no se puede validar el propio avance), y **no se puede retroceder** después.
- Cada persona ve solo su inscripción; el admin ve la del equipo para validar.
- Pantalla: **Formación** (`/dashboard/formacion`), visible para el equipo. La plataforma
  trae cargados Fortinet NSE 4 y Cisco CCNA.

## Lo que todavía no está en el flujo

| Falta | Por qué importa |
|---|---|
| **Conversión de lead a cliente con un clic** | Hoy el admin crea el cliente a mano; el lead no queda enlazado |
| **Alta de un usuario de portal para el cliente** | Hoy se hace en Usuarios; no hay invitación por correo |
| **Aviso por correo o WhatsApp** cuando avanza el proyecto | Hoy el cliente lo ve al entrar; no se le empuja |
| **Subida de entregables por el colaborador** | Los documentos los publica quien tenga permiso en el proyecto |
